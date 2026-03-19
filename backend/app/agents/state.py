"""LangGraph state definition for the story generation workflow."""
from typing import List, Optional, TypedDict


class StoryState(TypedDict, total=False):
    parent_id: int
    child_id: int
    child_profile: dict
    story_id: int
    session_id: int
    story_theme: str
    main_character: str
    scene: str
    story_plan: dict
    retrieved_docs: List[str]
    current_scene_index: int
    current_scene_text: str
    options: List[dict]
    selected_option: str
    interaction_history: List[dict]
    story_finished: bool
    safety_result: dict
    final_summary: str
    parent_suggestion: str
    blocked_topics: List[str]
    error: Optional[str]
