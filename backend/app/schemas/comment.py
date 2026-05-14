from datetime import datetime
from pydantic import BaseModel


class CommentUser(BaseModel):
    id: int
    username: str
    avatar_url: str | None = None


class CommentCreate(BaseModel):
    content: str


class CommentOut(BaseModel):
    id: int
    content: str
    created_at: datetime
    user: CommentUser
