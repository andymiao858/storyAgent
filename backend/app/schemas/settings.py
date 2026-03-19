from typing import List, Optional
from pydantic import BaseModel


class ParentSettingsUpdate(BaseModel):
    blocked_topics: Optional[List[str]] = None
    preferred_themes: Optional[List[str]] = None
    daily_limit_minutes: Optional[int] = None


class ParentSettingsResponse(BaseModel):
    id: int
    parent_id: int
    blocked_topics: list
    preferred_themes: list
    daily_limit_minutes: int

    model_config = {"from_attributes": True}
