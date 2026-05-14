from fastapi import APIRouter, Depends, UploadFile, File
from sqlmodel import Session
from app.api.deps import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.common import APIResponse
import os
import shutil
import uuid

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=APIResponse)
def get_me(user: User = Depends(get_current_user)):
    return APIResponse(success=True, message="User retrieved successfully", data=user)


@router.put("/me/avatar", response_model=APIResponse)
def update_avatar(
    avatar: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    avatar_dir = os.path.join("uploads", "avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}_{avatar.filename}"
    avatar_path = os.path.join(avatar_dir, filename)

    with open(avatar_path, "wb") as buffer:
        shutil.copyfileobj(avatar.file, buffer)

    if user.avatar_url and os.path.exists(user.avatar_url):
        try:
            os.remove(user.avatar_url)
        except OSError:
            pass

    user.avatar_url = avatar_path
    db.add(user)
    db.commit()
    db.refresh(user)
    return APIResponse(success=True, message="Avatar updated", data=user)
