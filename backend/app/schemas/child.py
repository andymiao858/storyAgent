from typing import List, Optional
from pydantic import BaseModel


class ChildCreate(BaseModel):
    nickname: str
    age: int
    avatar_url: Optional[str] = ""
    interests: List[str] = []
    reading_level: str = "beginner"


class ChildUpdate(BaseModel):
    nickname: Optional[str] = None
    age: Optional[int] = None
    avatar_url: Optional[str] = None
    interests: Optional[List[str]] = None
    reading_level: Optional[str] = None


class ChildResponse(BaseModel):
    id: int
    parent_id: int
    nickname: str
    age: int
    avatar_url: str
    interests: list
    reading_level: str
    is_active: bool

    model_config = {"from_attributes": True}
