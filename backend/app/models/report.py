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
    status: ReportStatus = Field(default=ReportStatus.pending)
    similarity_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)