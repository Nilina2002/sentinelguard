from typing import List

import cv2
import face_recognition
import numpy as np
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from sqlalchemy import func

from app.api.deps import get_db, get_current_user
from app.models import User
from app.models.blocklist import Blocklist
from app.models.deletion_log import DeletionLog
from app.models.embedding_meta_data import EmbeddingMetadata
from app.models.image import Image
from app.models.report import Report
from app.models.report_match import ReportMatch
from app.schemas.common import APIResponse
from app.services.ai_service import (
    SIMILARITY_THRESHOLD,
    TOP_K_DEFAULT,
    add_to_blocklist,
    get_image_embedding,
    search_similar_images,
    normalize_embedding,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


class EmbeddingPayload(BaseModel):
    verified: bool
    embedding: List[float]
    target_image_id: int
    threshold: float = SIMILARITY_THRESHOLD


class ReportHistoryItem(BaseModel):
    id: int
    status: str
    similarity_score: float | None = None
    matches_found: int = 0
    created_at: str


@router.post("/")
def create_report(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = Report(reporter_id=user.id)
    db.add(report)
    db.commit()
    db.refresh(report)

    return report


@router.get("/me", response_model=list[ReportHistoryItem])
def list_my_reports(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    match_counts = (
        select(ReportMatch.report_id, func.count(ReportMatch.id).label("matches_found"))
        .group_by(ReportMatch.report_id)
        .subquery()
    )

    stmt = (
        select(
            Report,
            func.coalesce(match_counts.c.matches_found, 0),
        )
        .outerjoin(match_counts, match_counts.c.report_id == Report.id)
        .where(Report.reporter_id == user.id)
        .order_by(Report.created_at.desc())
    )
    rows = db.exec(stmt).all()

    items: list[ReportHistoryItem] = []
    for report, matches_found in rows:
        items.append(
            ReportHistoryItem(
                id=report.id,
                status=report.status.value,
                similarity_score=report.similarity_score,
                matches_found=int(matches_found or 0),
                created_at=report.created_at.isoformat(),
            )
        )
    return items

@router.post("/{report_id}/embedding")
def submit_embedding(
    report_id: int,
    payload: EmbeddingPayload,
    db: Session = Depends(get_db),
):
    report = db.get(Report, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not payload.verified:
        report.status = "rejected"
        db.commit()
        return APIResponse(success=False, message="Verification failed")

    threshold = payload.threshold or SIMILARITY_THRESHOLD
    target_image = db.get(Image, payload.target_image_id)
    if not target_image:
        raise HTTPException(status_code=404, detail="Target image not found")
    if target_image.is_deleted:
        return APIResponse(success=False, message="Target image already deleted")

    query_vector = normalize_embedding(payload.embedding)
    matches = search_similar_images(query_vector, top_k=TOP_K_DEFAULT)
    qualifying = [match for match in matches if match.get("score", 0) >= threshold]

    if not qualifying:
        report.status = "rejected"
        report.similarity_score = None
        db.commit()
        return APIResponse(
            success=False,
            message="No similar matches were found above the threshold",
            data={"matches_found": 0, "images_deleted": 0},
        )

    report.status = "verified"
    best_score = max(match.get("score", 0) for match in qualifying)
    report.similarity_score = best_score

    images_deleted = 0
    for match in qualifying:
        image_id = int(match.get("image_id", 0))
        vector_id = str(match.get("vector_id", ""))
        similarity = float(match.get("score", 0))

        image = db.get(Image, image_id)
        if not image or image.is_deleted or image.user_id == report.reporter_id:
            continue

        existing = db.exec(
            select(ReportMatch).where(
                ReportMatch.report_id == report_id,
                ReportMatch.image_id == image_id,
            )
        ).first()
        if not existing:
            db.add(
                ReportMatch(
                    report_id=report_id,
                    image_id=image_id,
                    similarity_score=similarity,
                )
            )

        image.is_deleted = True
        db.add(DeletionLog(image_id=image_id, report_id=report_id))
        if vector_id:
            db.add(Blocklist(vector_id=vector_id, reason="ncii"))
            add_to_blocklist(
                vector_id=vector_id,
                embedding=get_image_embedding(vector_id) or query_vector,
                reason="ncii",
            )
        images_deleted += 1

    report.status = "processed"
    db.commit()

    return APIResponse(
        success=True,
        message="Claim verified and image removed",
        data={
            "matches_found": len(qualifying),
            "images_deleted": images_deleted,
            "similarity": best_score,
        },
    )

@router.post("/{report_id}/match")
def match_report(report_id: int, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    matches = db.exec(
        select(ReportMatch).where(ReportMatch.report_id == report_id)
    ).all()
    return {"matches_found": len(matches)}

@router.get("/{report_id}/results")
def get_results(report_id: int, db: Session = Depends(get_db)):
    matches = db.exec(
        select(ReportMatch).where(ReportMatch.report_id == report_id)
    ).all()

    return matches

@router.post("/{report_id}/enforce")
def enforce(report_id: int, db: Session = Depends(get_db)):
    matches = db.exec(
        select(ReportMatch).where(ReportMatch.report_id == report_id)
    ).all()

    deleted = 0
    for match in matches:
        image = db.get(Image, match.image_id)
        if image and not image.is_deleted:
            image.is_deleted = True
            db.add(DeletionLog(image_id=image.id, report_id=report_id))
            deleted += 1

    db.commit()

    return {"message": "Enforcement complete", "images_deleted": deleted}

def read_image(file: UploadFile):
    contents = file.file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

@router.post("/verify")
async def verify_report(selfie: UploadFile = File(...), reported_image: UploadFile = File(...)):
    try:
        # Read images
        selfie_img = read_image(selfie)
        reported_img = read_image(reported_image)

        # Convert BGR → RGB
        selfie_rgb = cv2.cvtColor(selfie_img, cv2.COLOR_BGR2RGB)
        reported_rgb = cv2.cvtColor(reported_img, cv2.COLOR_BGR2RGB)

        # Encode faces
        selfie_encodings = face_recognition.face_encodings(selfie_rgb)
        reported_encodings = face_recognition.face_encodings(reported_rgb)

        if not selfie_encodings:
            return {"verified": False, "message": "No face in selfie"}

        if not reported_encodings:
            return {"verified": False, "message": "No face in reported image"}

        # Compare
        result = face_recognition.compare_faces(
            [reported_encodings[0]],
            selfie_encodings[0],
            tolerance=0.7  # lower = stricter
        )

        distance = face_recognition.face_distance(
            [reported_encodings[0]],
            selfie_encodings[0]
        )[0]

        verified = bool(result[0])

        if verified:
            # TODO: save to DB
            pass
        return APIResponse(success=verified, message="Identity verified", data={"similarity": 1-distance})
    except Exception:
        return APIResponse(success=False, message="Error occurred while processing images")