from typing import List, Optional
from pydantic import BaseModel


class StoryStartRequest(BaseModel):
    child_id: int
    theme: str
    main_character: str
    scene: str


class StoryStartResponse(BaseModel):
    story_id: int
    session_id: int
    first_scene_text: str
    options: List[dict]


class StoryContinueRequest(BaseModel):
    session_id: int
    selected_option: str


class StoryContinueResponse(BaseModel):
    next_scene_text: str
    options: List[dict]
    is_finished: bool


class StoryHistoryItem(BaseModel):
    id: int
    title: str
    theme: str
    main_character: str
    scene: str
    story_status: str
    created_at: str

    model_config = {"from_attributes": True}


class StorySessionDetail(BaseModel):
    session_id: int
    story_id: int
    current_scene_index: int
    is_finished: bool
    messages: List[dict]
    choices: List[dict]


class StoryStartStreamRequest(BaseModel):
    session_id: int
