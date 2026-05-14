from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    __tablename__ = "user"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    phone: Optional[str] = Field(default=None)
    avatar_url: Optional[str] = Field(default=None)
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)