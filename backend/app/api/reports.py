from typing import List

import cv2
import face_recognition
import numpy as np
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

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
    add_to_blocklist,
    get_image_embedding,
    normalize_embedding,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


class EmbeddingPayload(BaseModel):
    verified: bool
    embedding: List[float]
    target_image_id: int
    threshold: float = SIMILARITY_THRESHOLD


@router.post("/")
def create_report(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = Report(reporter_id=user.id)
    db.add(report)
    db.commit()
    db.refresh(report)

    return report

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

    embedding_meta = db.exec(
        select(EmbeddingMetadata).where(EmbeddingMetadata.image_id == target_image.id)
    ).first()
    if not embedding_meta:
        return APIResponse(success=False, message="Target image has no embedding")

    target_vector = get_image_embedding(embedding_meta.vector_id)
    if not target_vector:
        return APIResponse(success=False, message="Target embedding not found in vector store")

    query_vector = normalize_embedding(payload.embedding)
    similarity = float(np.dot(np.array(query_vector, dtype=np.float32), np.array(target_vector, dtype=np.float32)))

    if similarity < threshold:
        report.status = "rejected"
        report.similarity_score = similarity
        db.commit()
        return APIResponse(
            success=False,
            message="Claim image does not match the reported image strongly enough",
            data={"matches_found": 0, "images_deleted": 0, "similarity": similarity},
        )

    report.status = "verified"
    report.similarity_score = similarity

    existing = db.exec(
        select(ReportMatch).where(
            ReportMatch.report_id == report_id,
            ReportMatch.image_id == target_image.id,
        )
    ).first()
    if not existing:
        db.add(
            ReportMatch(
                report_id=report_id,
                image_id=target_image.id,
                similarity_score=similarity,
            )
        )

    target_image.is_deleted = True
    db.add(DeletionLog(image_id=target_image.id, report_id=report_id))
    db.add(Blocklist(vector_id=embedding_meta.vector_id, reason="ncii"))
    add_to_blocklist(
        vector_id=embedding_meta.vector_id,
        embedding=target_vector,
        reason="ncii",
    )

    report.status = "processed"
    db.commit()

    return APIResponse(
        success=True,
        message="Claim verified and image removed",
        data={"matches_found": 1, "images_deleted": 1, "similarity": similarity},
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
            tolerance=0.5  # lower = stricter
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