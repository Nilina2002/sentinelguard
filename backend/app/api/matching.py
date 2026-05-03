from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ai_service import search_similar_images

router = APIRouter(prefix="/matching", tags=["Matching"])


class SearchPayload(BaseModel):
    embedding: List[float]
    top_k: int = 5


@router.post("/search")
def search_embedding(payload: SearchPayload):
    matches = search_similar_images(payload.embedding, top_k=payload.top_k)
    return {"matches": matches}
