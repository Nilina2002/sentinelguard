from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Blocklist(SQLModel, table=True):
    __tablename__ = "blocklist"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vector_id: str  # from ChromaDB
    reason: str = Field(default="ncii")
    created_at: datetime = Field(default_factory=datetime.utcnow)