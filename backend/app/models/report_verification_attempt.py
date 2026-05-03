from datetime import datetime
from typing import Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class ReportVerificationAttempt(SQLModel, table=True):
    __tablename__ = "report_verification_attempt"

    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="report.id")
    step: str
    status: str
    reason_code: Optional[str] = None
    scores_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    ip_hash: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
