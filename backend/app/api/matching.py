from fastapi import APIRouter

router = APIRouter(prefix="/matching", tags=["Matching"])


@router.post("/search")
def search_embedding():
    return {"message": "Matching service placeholder"}
