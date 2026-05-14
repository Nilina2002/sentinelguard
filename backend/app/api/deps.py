from fastapi import Depends, HTTPException, Request
from jose import jwt, JWTError
from sqlmodel import Session
from app.db.session import get_session
from app.core.config import settings
from app.models.user import User
from app.schemas.common import APIResponse


def get_db(session: Session = Depends(get_session)):
    return session


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
