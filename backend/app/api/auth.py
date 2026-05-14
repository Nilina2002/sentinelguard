from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File, Form
from sqlmodel import Session, select
from app.api.deps import get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.auth import LoginRequest
from pydantic import EmailStr
from app.core.security import hash_password, verify_password, create_access_token
import os
import shutil
import uuid

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=APIResponse)
def register(
    response: Response,
    db: Session = Depends(get_db),
    email: EmailStr = Form(...),
    password: str = Form(...),
    username: str = Form(...),
    phone: str | None = Form(None),
    avatar: UploadFile | None = File(None),
):
    existing = db.exec(select(User).where(User.email == email)).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    existing_username = db.exec(select(User).where(User.username == username)).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already exists")

    avatar_path = None
    if avatar:
        avatar_dir = os.path.join("uploads", "avatars")
        os.makedirs(avatar_dir, exist_ok=True)
        filename = f"{uuid.uuid4()}_{avatar.filename}"
        avatar_path = os.path.join(avatar_dir, filename)
        with open(avatar_path, "wb") as buffer:
            shutil.copyfileobj(avatar.file, buffer)

    user = User(
        email=email,
        username=username,
        phone=phone,
        avatar_url=avatar_path,
        password=hash_password(password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,   # True in production (HTTPS)
        samesite="lax"
    )

    return APIResponse(success=True, message="User registered successfully")


@router.post("/login", response_model=APIResponse)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.exec(select(User).where(User.email == data.email)).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,   # True in production (HTTPS)
        samesite="lax"
    )

    return APIResponse(success=True, message="Login successful")

@router.post("/logout", response_model=APIResponse)
def logout(response: Response):
    response.delete_cookie("access_token")
    return APIResponse(success=True, message="Logout successful")
