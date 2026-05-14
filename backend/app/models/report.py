from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ReportStatus(str, Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"
    processed = "processed"


class Report(SQLModel, table=True):
    __tablename__ = "report"

    id: Optional[int] = Field(default=None, primary_key=True)
    reporter_id: int = Field(foreign_key="user.id")
    target_image_id: Optional[int] = Field(default=None, foreign_key="image.id")
    status: ReportStatus = Field(default=ReportStatus.pending)
    similarity_score: Optional[float] = None
    face_presence_passed: bool = Field(default=False)
    selfie_verified: bool = Field(default=False)
    supporting_verified: bool = Field(default=False)
    final_decision: Optional[str] = None
    selfie_similarity: Optional[float] = None
    support_similarity: Optional[float] = None
    db_consistency_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)