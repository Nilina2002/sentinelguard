from datetime import datetime
from pydantic import BaseModel


class ImageOwner(BaseModel):
    id: int
    email: str
    username: str
    avatar_url: str | None = None


class ImageFeedItem(BaseModel):
    id: int
    image_url: str
    created_at: datetime
    owner: ImageOwner
    like_count: int = 0
    comment_count: int = 0