from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class EmbeddingMetadata(SQLModel, table=True):
    __tablename__ = "embedding_metadata"

    id: Optional[int] = Field(default=None, primary_key=True)
    image_id: int = Field(foreign_key="image.id")
    vector_id: str  # ID in ChromaDB
    model_used: str = Field(default="clip")
    created_at: datetime = Field(default_factory=datetime.utcnow)