from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlmodel import Session, select
from app.api.deps import get_db
from app.models.report import Report
from app.models.report_match import ReportMatch
from app.models.image import Image
from app.models.deletion_log import DeletionLog
from app.schemas.common import APIResponse
import face_recognition
import numpy as np
import cv2

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/")
def create_report(db: Session = Depends(get_db)):
    report = Report(reporter_id=1)  # temp user
    db.add(report)
    db.commit()
    db.refresh(report)

    return report

@router.post("/{report_id}/embedding")
def submit_embedding(report_id: int, payload: dict, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not payload.get("verified"):
        report.status = "rejected"
        db.commit()
        return {"message": "Verification failed"}

    report.status = "verified"
    db.commit()

    # TODO: send embedding to matching service
    return {"message": "Embedding received"}

@router.post("/{report_id}/match")
def match_report(report_id: int, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # TEMP: simulate match
    images = db.exec(select(Image).where(Image.is_deleted == False)).all()

    matches = []
    for img in images[:2]:  # fake match first 2
        match = ReportMatch(
            report_id=report_id,
            image_id=img.id,
            similarity_score=0.95,
        )
        db.add(match)
        matches.append(match)

    db.commit()

    report.status = "processed"
    db.commit()

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

    for match in matches:
        image = db.get(Image, match.image_id)
        if image:
            image.is_deleted = True

            log = DeletionLog(
                image_id=image.id,
                report_id=report_id,
            )
            db.add(log)

    db.commit()

    return {"message": "Enforcement complete"}

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

    except Exception as e:
        return APIResponse(success=False, message="Error occurred while processing images")