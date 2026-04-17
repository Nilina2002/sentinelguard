from sqlmodel import SQLModel, Field
from typing import Optional

class ReportMatch(SQLModel, table=True):
    __tablename__ = "report_match"

    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="report.id")
    image_id: int = Field(foreign_key="image.id")
    similarity_score: float