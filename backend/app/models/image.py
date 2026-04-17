from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Image(SQLModel, table=True):
    __tablename__ = "image"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    image_url: str = Field(default=None)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)