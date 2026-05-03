from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class DeletionLog(SQLModel, table=True):
    __tablename__ = "deletion_log"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    image_id: int = Field(foreign_key="image.id")
    report_id: int = Field(foreign_key="report.id")
    deleted_at: datetime = Field(default_factory=datetime.utcnow)
    