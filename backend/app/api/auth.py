from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select
from app.api.deps import get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=APIResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.exec(select(User).where(User.email == data.email)).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        email=data.email,
        password=hash_password(data.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

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
