from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ReportEvidence(SQLModel, table=True):
    __tablename__ = "report_evidence"

    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="report.id")
    evidence_type: str
    file_path: Optional[str] = None
    vector_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
