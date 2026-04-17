from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.api.deps import get_db
from app.models.report import Report
from app.models.report_match import ReportMatch
from app.models.image import Image
from app.models.deletion_log import DeletionLog

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
