import hashlib
import logging
import os
import uuid
from typing import List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.models import User
from app.models.blocklist import Blocklist
from app.models.deletion_log import DeletionLog
from app.models.embedding_meta_data import EmbeddingMetadata
from app.models.image import Image
from app.models.report import Report
from app.models.report_evidence import ReportEvidence
from app.models.report_match import ReportMatch
from app.models.report_verification_attempt import ReportVerificationAttempt
from app.schemas.common import APIResponse
from app.services.ai_service import (
    add_to_blocklist,
    cosine_similarity,
    get_image_embedding,
    normalize_embedding,
)
from app.services.face_verification_service import (
    analyze_faces,
    best_face_similarity,
    decode_upload_image,
)
from app.services.image_embedding_service import generate_embedding_from_bgr

router = APIRouter(prefix="/reports", tags=["Reports"])
EVIDENCE_UPLOAD_DIR = "uploads/report_evidence"
os.makedirs(EVIDENCE_UPLOAD_DIR, exist_ok=True)
logger = logging.getLogger(__name__)
verification_metrics = {
    "face_presence_check_passed": 0,
    "face_presence_check_failed": 0,
    "selfie_verify_passed": 0,
    "selfie_verify_failed": 0,
    "supporting_evidence_verify_passed": 0,
    "supporting_evidence_verify_failed": 0,
    "finalize_passed": 0,
    "finalize_failed": 0,
}


class CreateReportPayload(BaseModel):
    target_image_id: int


class EmbeddingPayload(BaseModel):
    verified: bool
    embedding: List[float]
    target_image_id: int
    threshold: float = 0.98


def _hash_ip(ip_address: Optional[str]) -> Optional[str]:
    if not ip_address:
        return None
    return hashlib.sha256(ip_address.encode("utf-8")).hexdigest()


def _record_attempt(
    db: Session,
    request: Request,
    report_id: int,
    step: str,
    status: str,
    reason_code: Optional[str] = None,
    scores: Optional[dict] = None,
):
    metric_key = f"{step}_passed" if status == "passed" else f"{step}_failed"
    if metric_key in verification_metrics:
        verification_metrics[metric_key] += 1
    logger.info(
        "report_verification_attempt",
        extra={
            "report_id": report_id,
            "step": step,
            "status": status,
            "reason_code": reason_code,
            "scores": scores or {},
        },
    )
    db.add(
        ReportVerificationAttempt(
            report_id=report_id,
            step=step,
            status=status,
            reason_code=reason_code,
            scores_json=scores,
            ip_hash=_hash_ip(request.client.host if request.client else None),
            user_agent=request.headers.get("user-agent"),
        )
    )


def _load_reported_image(report: Report, db: Session) -> tuple[Image, np.ndarray]:
    if not report.target_image_id:
        raise HTTPException(status_code=400, detail="Report has no target image")
    target_image = db.get(Image, report.target_image_id)
    if not target_image:
        raise HTTPException(status_code=404, detail="Target image not found")
    if target_image.is_deleted:
        raise HTTPException(status_code=400, detail="Target image already deleted")
    image_bgr = cv2.imread(target_image.image_url)
    if image_bgr is None:
        raise HTTPException(status_code=400, detail="Unable to read reported image from storage")
    return target_image, image_bgr


def _get_report_or_404(report_id: int, user: User, db: Session) -> Report:
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.reporter_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed to access this report")
    return report


def compute_final_score(scores: List[Optional[float]]) -> float:
    valid_scores = [score for score in scores if score is not None]
    return float(min(valid_scores)) if valid_scores else 0.0


@router.post("/")
def create_report(
    payload: CreateReportPayload,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_image = db.get(Image, payload.target_image_id)
    if not target_image:
        raise HTTPException(status_code=404, detail="Target image not found")
    if target_image.is_deleted:
        raise HTTPException(status_code=400, detail="Target image already deleted")
    report = Report(reporter_id=user.id, target_image_id=payload.target_image_id)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.post("/{report_id}/face-presence-check")
def face_presence_check(
    report_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _get_report_or_404(report_id, user, db)
    _, reported_bgr = _load_reported_image(report, db)
    report_embedding = generate_embedding_from_bgr(reported_bgr)
    face_analysis = analyze_faces(reported_bgr)

    if face_analysis.face_count < 1:
        report.status = "rejected"
        _record_attempt(
            db,
            request,
            report_id,
            step="face_presence_check",
            status="failed",
            reason_code="NO_FACE_DETECTED",
        )
        db.commit()
        return APIResponse(
            success=False,
            message="No face detected in reported image",
            data={"stage": "face_presence_check", "reason_code": "NO_FACE_DETECTED"},
        )

    report.face_presence_passed = True
    report.support_similarity = None
    report.db_consistency_score = None
    _record_attempt(
        db,
        request,
        report_id,
        step="face_presence_check",
        status="passed",
        scores={"face_count": face_analysis.face_count, "report_embedding_norm": float(np.linalg.norm(report_embedding))},
    )
    db.commit()
    return APIResponse(
        success=True,
        message="Face detected in reported image",
        data={"stage": "face_presence_check", "reason_code": None, "scores": {"face_count": face_analysis.face_count}},
    )


@router.post("/{report_id}/selfie-verify")
async def selfie_verify(
    report_id: int,
    request: Request,
    selfie: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _get_report_or_404(report_id, user, db)
    if not report.face_presence_passed:
        raise HTTPException(status_code=400, detail="Face presence check must pass first")

    _, reported_bgr = _load_reported_image(report, db)
    reported_faces = analyze_faces(reported_bgr)
    if reported_faces.face_count < 1:
        raise HTTPException(status_code=400, detail="Reported image no longer has detectable face")

    selfie_bytes = await selfie.read()
    selfie_bgr = decode_upload_image(selfie_bytes)
    selfie_faces = analyze_faces(selfie_bgr)
    if selfie_faces.face_count != 1:
        reason_code = "SELFIE_FACE_COUNT_INVALID"
        report.selfie_verified = False
        report.status = "rejected"
        _record_attempt(
            db,
            request,
            report_id,
            step="selfie_verify",
            status="failed",
            reason_code=reason_code,
            scores={"face_count": selfie_faces.face_count},
        )
        db.commit()
        return APIResponse(
            success=False,
            message="Selfie must contain exactly one face",
            data={"stage": "selfie_verify", "reason_code": reason_code},
        )

    if selfie_faces.liveness_score < settings.SELFIE_LIVENESS_THRESHOLD:
        reason_code = "LIVENESS_CHECK_FAILED"
        report.selfie_verified = False
        report.status = "rejected"
        _record_attempt(
            db,
            request,
            report_id,
            step="selfie_verify",
            status="failed",
            reason_code=reason_code,
            scores={"liveness_score": selfie_faces.liveness_score},
        )
        db.commit()
        return APIResponse(
            success=False,
            message="Selfie liveness check failed",
            data={
                "stage": "selfie_verify",
                "reason_code": reason_code,
                "scores": {"liveness_score": selfie_faces.liveness_score},
            },
        )

    similarity = best_face_similarity(selfie_faces.encodings[0], reported_faces.encodings)
    report.selfie_similarity = similarity
    if similarity < settings.SELFIE_FACE_THRESHOLD:
        reason_code = "SELFIE_MISMATCH"
        report.selfie_verified = False
        report.status = "rejected"
        _record_attempt(
            db,
            request,
            report_id,
            step="selfie_verify",
            status="failed",
            reason_code=reason_code,
            scores={"selfie_similarity": similarity, "liveness_score": selfie_faces.liveness_score},
        )
        db.commit()
        return APIResponse(
            success=False,
            message="Selfie does not match the reported face",
            data={
                "stage": "selfie_verify",
                "reason_code": reason_code,
                "scores": {"selfie_similarity": similarity},
            },
        )

    selfie_path = os.path.join(EVIDENCE_UPLOAD_DIR, f"{uuid.uuid4()}_{selfie.filename}")
    with open(selfie_path, "wb") as buffer:
        buffer.write(selfie_bytes)
    db.add(ReportEvidence(report_id=report_id, evidence_type="selfie", file_path=selfie_path))

    report.selfie_verified = True
    report.status = "verified"
    _record_attempt(
        db,
        request,
        report_id,
        step="selfie_verify",
        status="passed",
        scores={"selfie_similarity": similarity, "liveness_score": selfie_faces.liveness_score},
    )
    db.commit()
    return APIResponse(
        success=True,
        message="Selfie verification passed",
        data={
            "stage": "selfie_verify",
            "reason_code": None,
            "scores": {"selfie_similarity": similarity, "liveness_score": selfie_faces.liveness_score},
        },
    )


@router.post("/{report_id}/supporting-evidence-verify")
async def supporting_evidence_verify(
    report_id: int,
    request: Request,
    supporting_image: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _get_report_or_404(report_id, user, db)
    if not report.selfie_verified:
        raise HTTPException(status_code=400, detail="Selfie verification must pass first")

    _, reported_bgr = _load_reported_image(report, db)
    support_bytes = await supporting_image.read()
    support_bgr = decode_upload_image(support_bytes)

    support_embedding = normalize_embedding(generate_embedding_from_bgr(support_bgr))
    report_embedding = normalize_embedding(generate_embedding_from_bgr(reported_bgr))
    support_vs_report = cosine_similarity(support_embedding, report_embedding)

    reporter_vectors: List[List[float]] = []
    reporter_images = db.exec(select(Image).where(Image.user_id == user.id, Image.is_deleted == False)).all()
    for image in reporter_images:
        embedding_meta = db.exec(
            select(EmbeddingMetadata).where(EmbeddingMetadata.image_id == image.id)
        ).first()
        if embedding_meta:
            vector = get_image_embedding(embedding_meta.vector_id)
            if vector:
                reporter_vectors.append(vector)

    if reporter_vectors:
        history_scores = [cosine_similarity(support_embedding, vector) for vector in reporter_vectors]
        support_vs_history = float(max(history_scores))
    else:
        support_vs_history = support_vs_report

    report.support_similarity = support_vs_report
    report.db_consistency_score = support_vs_history
    supporting_path = os.path.join(EVIDENCE_UPLOAD_DIR, f"{uuid.uuid4()}_{supporting_image.filename}")
    with open(supporting_path, "wb") as buffer:
        buffer.write(support_bytes)

    if (
        support_vs_report < settings.SUPPORT_REPORT_THRESHOLD
        or support_vs_history < settings.SUPPORT_DB_THRESHOLD
    ):
        reason_code = "SUPPORTING_EVIDENCE_MISMATCH"
        report.supporting_verified = False
        report.status = "rejected"
        db.add(ReportEvidence(report_id=report_id, evidence_type="supporting", file_path=supporting_path))
        _record_attempt(
            db,
            request,
            report_id,
            step="supporting_evidence_verify",
            status="failed",
            reason_code=reason_code,
            scores={
                "support_vs_report": support_vs_report,
                "support_vs_history": support_vs_history,
            },
        )
        db.commit()
        return APIResponse(
            success=False,
            message="Supporting evidence did not meet verification thresholds",
            data={
                "stage": "supporting_evidence_verify",
                "reason_code": reason_code,
                "scores": {
                    "support_vs_report": support_vs_report,
                    "support_vs_history": support_vs_history,
                },
            },
        )

    db.add(ReportEvidence(report_id=report_id, evidence_type="supporting", file_path=supporting_path))
    report.supporting_verified = True
    _record_attempt(
        db,
        request,
        report_id,
        step="supporting_evidence_verify",
        status="passed",
        scores={"support_vs_report": support_vs_report, "support_vs_history": support_vs_history},
    )
    db.commit()
    return APIResponse(
        success=True,
        message="Supporting evidence verified",
        data={
            "stage": "supporting_evidence_verify",
            "reason_code": None,
            "scores": {"support_vs_report": support_vs_report, "support_vs_history": support_vs_history},
        },
    )


@router.post("/{report_id}/finalize")
def finalize_report(
    report_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _get_report_or_404(report_id, user, db)
    if not (report.face_presence_passed and report.selfie_verified and report.supporting_verified):
        raise HTTPException(status_code=400, detail="All verification stages must pass before finalize")

    final_score = compute_final_score(
        [report.selfie_similarity, report.support_similarity, report.db_consistency_score]
    )
    report.final_decision = "approved" if final_score >= settings.FINAL_THRESHOLD else "rejected"
    report.similarity_score = final_score

    target_image, _ = _load_reported_image(report, db)
    if report.final_decision != "approved":
        report.status = "rejected"
        _record_attempt(
            db,
            request,
            report_id,
            step="finalize",
            status="failed",
            reason_code="FINAL_THRESHOLD_FAILED",
            scores={"final_score": final_score},
        )
        db.commit()
        return APIResponse(
            success=False,
            message="Final confidence below threshold",
            data={"stage": "finalize", "reason_code": "FINAL_THRESHOLD_FAILED", "scores": {"final_score": final_score}},
        )

    embedding_meta = db.exec(
        select(EmbeddingMetadata).where(EmbeddingMetadata.image_id == target_image.id)
    ).first()
    if embedding_meta:
        target_vector = get_image_embedding(embedding_meta.vector_id)
        if target_vector:
            db.add(Blocklist(vector_id=embedding_meta.vector_id, reason="ncii"))
            add_to_blocklist(vector_id=embedding_meta.vector_id, embedding=target_vector, reason="ncii")

    existing = db.exec(
        select(ReportMatch).where(ReportMatch.report_id == report_id, ReportMatch.image_id == target_image.id)
    ).first()
    if not existing:
        db.add(ReportMatch(report_id=report_id, image_id=target_image.id, similarity_score=final_score))

    target_image.is_deleted = True
    report.status = "processed"
    db.add(DeletionLog(image_id=target_image.id, report_id=report_id))
    _record_attempt(
        db,
        request,
        report_id,
        step="finalize",
        status="passed",
        scores={"final_score": final_score},
    )
    db.commit()
    return APIResponse(
        success=True,
        message="Ownership verified. Reported image deleted.",
        data={"stage": "finalize", "reason_code": None, "scores": {"final_score": final_score}},
    )

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

@router.get("/{report_id}/audit")
def get_audit_log(
    report_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _get_report_or_404(report_id, user, db)
    attempts = db.exec(
        select(ReportVerificationAttempt)
        .where(ReportVerificationAttempt.report_id == report.id)
        .order_by(ReportVerificationAttempt.created_at)
    ).all()
    return attempts


@router.get("/metrics/verification")
def get_verification_metrics():
    return verification_metrics