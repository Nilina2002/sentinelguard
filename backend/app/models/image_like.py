from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import UniqueConstraint


class ImageLike(SQLModel, table=True):
    __tablename__ = "image_like"
    __table_args__ = (UniqueConstraint("image_id", "user_id", name="uq_image_like"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    image_id: int = Field(foreign_key="image.id")
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
