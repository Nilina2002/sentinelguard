from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.common import APIResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=APIResponse)
def get_me(user: User = Depends(get_current_user)):
    return APIResponse(success=True, message="User retrieved successfully", data=user)
