"""Story service: orchestrates LangGraph workflow + database persistence."""
import asyncio
import json
import logging
from typing import AsyncGenerator

from sqlalchemy.orm import Session

from app.agents.state import StoryState
from app.agents.workflow import build_start_workflow, build_continue_workflow
from app.agents.nodes import (
    user_profile_node,
    story_planning_node,
    retrieval_node,
    interaction_control_node,
    safety_audit_node,
    generate_options,
    _build_generation_messages,
)
from app.models.child_profile import ChildProfile
from app.models.parent_settings import ParentSettings
from app.models.story import (
    Story, StorySession, StoryMessage, StoryChoice,
    SafetyAuditLog, GrowthReport,
)
from app.utils.llm import get_llm

logger = logging.getLogger(__name__)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class StoryService:
    def __init__(self, db: Session):
        self.db = db

    def _rebuild_history_from_db(self, session_id: int) -> list:
        """Rebuild interaction history from stored messages and choices."""
        messages = (
            self.db.query(StoryMessage)
            .filter(StoryMessage.session_id == session_id, StoryMessage.role == "narrator")
            .order_by(StoryMessage.created_at)
            .all()
        )
        choices = (
            self.db.query(StoryChoice)
            .filter(StoryChoice.session_id == session_id)
            .order_by(StoryChoice.selected_at)
            .all()
        )
        choice_map = {c.scene_index: c for c in choices}

        history = []
        for i, msg in enumerate(messages):
            entry = {
                "scene_index": i,
                "text": msg.content,
                "choice": "",
                "choice_key": "",
            }
            if i in choice_map:
                entry["choice"] = choice_map[i].option_text
                entry["choice_key"] = choice_map[i].option_key
            history.append(entry)
        return history

    async def start_story(self, child: ChildProfile, theme: str, main_character: str, scene: str) -> dict:
        story = Story(
            child_id=child.id,
            theme=theme,
            main_character=main_character,
            scene=scene,
            story_status="in_progress",
        )
        self.db.add(story)
        self.db.commit()
        self.db.refresh(story)

        session = StorySession(
            story_id=story.id,
            child_id=child.id,
            current_scene_index=0,
            story_state_json={},
            is_finished=False,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        parent_settings = self.db.query(ParentSettings).filter(
            ParentSettings.parent_id == child.parent_id
        ).first()
        blocked_topics = parent_settings.blocked_topics if parent_settings else []

        initial_state: StoryState = {
            "parent_id": child.parent_id,
            "child_id": child.id,
            "child_profile": {
                "nickname": child.nickname,
                "age": child.age,
                "interests": child.interests or [],
                "reading_level": child.reading_level,
            },
            "story_id": story.id,
            "session_id": session.id,
            "story_theme": theme,
            "main_character": main_character,
            "scene": scene,
            "current_scene_index": 0,
            "interaction_history": [],
            "story_finished": False,
            "blocked_topics": blocked_topics or [],
            "retrieved_docs": [],
        }

        workflow = build_start_workflow()
        result = await workflow.ainvoke(initial_state)

        story.title = result.get("story_plan", {}).get("story_title", f"{main_character}的{theme}故事")
        scene_text = result.get("current_scene_text", "故事开始了...")
        options = result.get("options", [])
        is_finished = result.get("story_finished", False)

        self.db.add(StoryMessage(
            session_id=session.id,
            role="narrator",
            content=scene_text,
        ))

        session.story_state_json = {
            "story_plan": result.get("story_plan", {}),
            "child_profile": result.get("child_profile", {}),
            "interaction_history": result.get("interaction_history", []),
            "retrieved_docs": result.get("retrieved_docs", []),
            "blocked_topics": blocked_topics or [],
            "last_scene_text": scene_text,
            "last_options": options,
        }
        session.current_scene_index = result.get("current_scene_index", 0)
        session.is_finished = is_finished

        safety = result.get("safety_result", {})
        if safety and safety.get("status") != "safe":
            self.db.add(SafetyAuditLog(
                session_id=session.id,
                scene_index=0,
                original_text=safety.get("original_text", ""),
                audit_result=safety.get("status", ""),
                risk_type=safety.get("risk_type", ""),
                revised_text=safety.get("revised_text", ""),
            ))

        if is_finished:
            story.story_status = "completed"
            summary = result.get("final_summary", "")
            if summary:
                self.db.add(StoryMessage(
                    session_id=session.id,
                    role="system",
                    content=summary,
                ))

        self.db.commit()

        return {
            "story_id": story.id,
            "session_id": session.id,
            "title": story.title,
            "first_scene_text": scene_text,
            "options": options,
            "is_finished": is_finished,
        }

    async def continue_story(self, session: StorySession, selected_option: str) -> dict:
        state_json = session.story_state_json or {}

        child = self.db.query(ChildProfile).filter(ChildProfile.id == session.child_id).first()
        story = self.db.query(Story).filter(Story.id == session.story_id).first()

        # Resolve option_text from last_options for display
        last_options = state_json.get("last_options", [])
        option_text = selected_option
        for opt in last_options:
            if opt.get("key") == selected_option:
                option_text = opt.get("text", selected_option)
                break

        self.db.add(StoryChoice(
            session_id=session.id,
            scene_index=session.current_scene_index,
            option_key=selected_option,
            option_text=option_text,
        ))
        self.db.commit()

        # Rebuild full interaction_history from DB if state_json history is empty
        interaction_history = state_json.get("interaction_history", [])
        if not interaction_history and session.current_scene_index > 0:
            interaction_history = self._rebuild_history_from_db(session.id)

        continue_state: StoryState = {
            "parent_id": child.parent_id if child else 0,
            "child_id": session.child_id,
            "child_profile": state_json.get("child_profile", {
                "nickname": child.nickname if child else "",
                "age": child.age if child else 5,
                "interests": child.interests if child else [],
                "reading_level": child.reading_level if child else "beginner",
            }),
            "story_id": session.story_id,
            "session_id": session.id,
            "story_theme": story.theme if story else "",
            "main_character": story.main_character if story else "",
            "scene": story.scene if story else "",
            "story_plan": state_json.get("story_plan", {}),
            "retrieved_docs": state_json.get("retrieved_docs", []),
            "current_scene_index": session.current_scene_index,
            "current_scene_text": state_json.get("last_scene_text", ""),
            "options": last_options,
            "selected_option": selected_option,
            "interaction_history": interaction_history,
            "story_finished": False,
            "blocked_topics": state_json.get("blocked_topics", []),
        }

        workflow = build_continue_workflow()
        result = await workflow.ainvoke(continue_state)

        scene_text = result.get("current_scene_text", "")
        options = result.get("options", [])
        is_finished = result.get("story_finished", False)

        self.db.add(StoryMessage(
            session_id=session.id,
            role="narrator",
            content=scene_text,
        ))

        session.current_scene_index = result.get("current_scene_index", session.current_scene_index + 1)
        session.is_finished = is_finished
        session.story_state_json = {
            **state_json,
            "interaction_history": result.get("interaction_history", []),
            "child_profile": result.get("child_profile", state_json.get("child_profile", {})),
            "last_scene_text": scene_text,
            "last_options": options,
        }

        safety = result.get("safety_result", {})
        if safety and safety.get("status") != "safe":
            self.db.add(SafetyAuditLog(
                session_id=session.id,
                scene_index=session.current_scene_index,
                original_text=safety.get("original_text", ""),
                audit_result=safety.get("status", ""),
                risk_type=safety.get("risk_type", ""),
                revised_text=safety.get("revised_text", ""),
            ))

        if is_finished:
            story = self.db.query(Story).filter(Story.id == session.story_id).first()
            if story:
                story.story_status = "completed"

            summary_text = result.get("final_summary", "")
            parent_suggestion = result.get("parent_suggestion", "")
            if summary_text:
                self.db.add(StoryMessage(
                    session_id=session.id,
                    role="system",
                    content=json.dumps({"summary": summary_text, "parent_suggestion": parent_suggestion}, ensure_ascii=False),
                ))

        self.db.commit()

        response = {
            "next_scene_text": scene_text,
            "options": options,
            "is_finished": is_finished,
        }
        if is_finished:
            response["summary"] = result.get("final_summary", "")
            response["parent_suggestion"] = result.get("parent_suggestion", "")

        return response

    # ------------------------------------------------------------------ #
    #  Streaming variants
    # ------------------------------------------------------------------ #

    def _build_initial_state(self, child: ChildProfile, theme: str,
                             main_character: str, scene: str,
                             story: Story, session: StorySession,
                             blocked_topics: list) -> StoryState:
        return {
            "parent_id": child.parent_id,
            "child_id": child.id,
            "child_profile": {
                "nickname": child.nickname,
                "age": child.age,
                "interests": child.interests or [],
                "reading_level": child.reading_level,
            },
            "story_id": story.id,
            "session_id": session.id,
            "story_theme": theme,
            "main_character": main_character,
            "scene": scene,
            "current_scene_index": 0,
            "interaction_history": [],
            "story_finished": False,
            "blocked_topics": blocked_topics or [],
            "retrieved_docs": [],
        }

    async def _stream_scene_text(self, state: StoryState) -> AsyncGenerator[tuple[str, str], None]:
        """Stream scene text tokens. Yields (event_type, data_json) tuples.

        After all tokens are yielded, the final tuple is ("_scene_done", full_text).
        """
        messages, is_last, _ = _build_generation_messages(state, plain_text=True)
        llm = get_llm(temperature=0.85)
        full_text = ""
        async for chunk in llm.astream(messages):
            token = chunk.content
            if token:
                full_text += token
                yield ("token", json.dumps({"text": token}, ensure_ascii=False))
        yield ("_scene_done", full_text)

    def _run_safety_check(self, text: str, blocked: list) -> tuple[str, dict]:
        """Synchronous rule-based safety check. Returns (text, safety_result)."""
        state_stub = {"current_scene_text": text, "blocked_topics": blocked}
        result = safety_audit_node(state_stub)
        revised_text = result.get("current_scene_text", text)
        safety = result.get("safety_result", {"status": "safe"})
        return revised_text, safety

    async def start_story_stream(self, child: ChildProfile, theme: str,
                                  main_character: str, scene: str) -> AsyncGenerator[str, None]:
        """Streaming version of start_story. Yields SSE-formatted strings."""
        # 1. DB records
        story = Story(child_id=child.id, theme=theme, main_character=main_character,
                      scene=scene, story_status="in_progress")
        self.db.add(story)
        self.db.commit()
        self.db.refresh(story)

        session = StorySession(story_id=story.id, child_id=child.id,
                               current_scene_index=0, story_state_json={}, is_finished=False)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        parent_settings = self.db.query(ParentSettings).filter(
            ParentSettings.parent_id == child.parent_id).first()
        blocked_topics = parent_settings.blocked_topics if parent_settings else []

        state = self._build_initial_state(child, theme, main_character, scene,
                                          story, session, blocked_topics)

        # Send init event immediately
        yield _sse("init", {"story_id": story.id, "session_id": session.id})

        # 2. User profile
        state = {**state, **user_profile_node(state)}

        # 3. Planning + retrieval in parallel
        loop = asyncio.get_event_loop()
        planning_task = loop.run_in_executor(None, story_planning_node, state)
        retrieval_task = loop.run_in_executor(None, retrieval_node, state)
        plan_result, retrieval_result = await asyncio.gather(planning_task, retrieval_task)
        state = {**state, **plan_result, **retrieval_result}

        # Send title
        title = state.get("story_plan", {}).get("story_title", f"{main_character}的{theme}故事")
        story.title = title
        yield _sse("title", {"title": title})

        # 4. Stream scene text
        scene_text = ""
        async for event_type, payload in self._stream_scene_text(state):
            if event_type == "_scene_done":
                scene_text = payload
            else:
                yield f"event: {event_type}\ndata: {payload}\n\n"

        is_last = state.get("current_scene_index", 0) >= (
            len(state.get("story_plan", {}).get("scenes", [])) or 5) - 1

        # 5. Safety check + options in parallel
        safe_text, safety = self._run_safety_check(scene_text, blocked_topics)
        if safe_text != scene_text:
            scene_text = safe_text

        options = []
        if not is_last:
            options = await generate_options(scene_text, state)

        # 6. Persist
        self.db.add(StoryMessage(session_id=session.id, role="narrator", content=scene_text))
        session.story_state_json = {
            "story_plan": state.get("story_plan", {}),
            "child_profile": state.get("child_profile", {}),
            "interaction_history": [],
            "retrieved_docs": state.get("retrieved_docs", []),
            "blocked_topics": blocked_topics or [],
            "last_scene_text": scene_text,
            "last_options": options,
        }
        session.current_scene_index = 0
        session.is_finished = is_last

        if safety.get("status") != "safe":
            self.db.add(SafetyAuditLog(
                session_id=session.id, scene_index=0,
                original_text=safety.get("original_text", ""),
                audit_result=safety.get("status", ""),
                risk_type=safety.get("risk_type", ""),
                revised_text=safety.get("revised_text", ""),
            ))
        if is_last:
            story.story_status = "completed"
        self.db.commit()

        yield _sse("complete", {
            "scene_text": scene_text,
            "options": options,
            "is_finished": is_last,
            "scene_index": 0,
        })

    async def continue_story_stream(self, session: StorySession,
                                     selected_option: str) -> AsyncGenerator[str, None]:
        """Streaming version of continue_story. Yields SSE-formatted strings."""
        state_json = session.story_state_json or {}
        child = self.db.query(ChildProfile).filter(ChildProfile.id == session.child_id).first()
        story = self.db.query(Story).filter(Story.id == session.story_id).first()

        # Resolve option text
        last_options = state_json.get("last_options", [])
        option_text = selected_option
        for opt in last_options:
            if opt.get("key") == selected_option:
                option_text = opt.get("text", selected_option)
                break

        self.db.add(StoryChoice(
            session_id=session.id, scene_index=session.current_scene_index,
            option_key=selected_option, option_text=option_text,
        ))
        self.db.commit()

        # Rebuild history if needed
        interaction_history = state_json.get("interaction_history", [])
        if not interaction_history and session.current_scene_index > 0:
            interaction_history = self._rebuild_history_from_db(session.id)

        state: StoryState = {
            "parent_id": child.parent_id if child else 0,
            "child_id": session.child_id,
            "child_profile": state_json.get("child_profile", {
                "nickname": child.nickname if child else "",
                "age": child.age if child else 5,
                "interests": child.interests if child else [],
                "reading_level": child.reading_level if child else "beginner",
            }),
            "story_id": session.story_id,
            "session_id": session.id,
            "story_theme": story.theme if story else "",
            "main_character": story.main_character if story else "",
            "scene": story.scene if story else "",
            "story_plan": state_json.get("story_plan", {}),
            "retrieved_docs": state_json.get("retrieved_docs", []),
            "current_scene_index": session.current_scene_index,
            "current_scene_text": state_json.get("last_scene_text", ""),
            "options": last_options,
            "selected_option": selected_option,
            "interaction_history": interaction_history,
            "story_finished": False,
            "blocked_topics": state_json.get("blocked_topics", []),
        }

        # 1. Interaction control
        ic_updates = interaction_control_node(state)
        state = {**state, **ic_updates}

        # 2. Retrieval
        loop = asyncio.get_event_loop()
        ret_result = await loop.run_in_executor(None, retrieval_node, state)
        state = {**state, **ret_result}

        # 3. Stream scene text
        scene_text = ""
        async for event_type, payload in self._stream_scene_text(state):
            if event_type == "_scene_done":
                scene_text = payload
            else:
                yield f"event: {event_type}\ndata: {payload}\n\n"

        scenes = state.get("story_plan", {}).get("scenes", [])
        total_scenes = len(scenes) if scenes else 5
        new_scene_index = state.get("current_scene_index", 1)
        is_finished = new_scene_index >= total_scenes - 1

        # 4. Safety + options
        blocked = state.get("blocked_topics", [])
        safe_text, safety = self._run_safety_check(scene_text, blocked)
        if safe_text != scene_text:
            scene_text = safe_text

        options = []
        if not is_finished:
            options = await generate_options(scene_text, state)

        # 5. Persist
        self.db.add(StoryMessage(session_id=session.id, role="narrator", content=scene_text))
        session.current_scene_index = new_scene_index
        session.is_finished = is_finished
        session.story_state_json = {
            **state_json,
            "interaction_history": state.get("interaction_history", []),
            "child_profile": state.get("child_profile", state_json.get("child_profile", {})),
            "last_scene_text": scene_text,
            "last_options": options,
        }

        if safety.get("status") != "safe":
            self.db.add(SafetyAuditLog(
                session_id=session.id, scene_index=new_scene_index,
                original_text=safety.get("original_text", ""),
                audit_result=safety.get("status", ""),
                risk_type=safety.get("risk_type", ""),
                revised_text=safety.get("revised_text", ""),
            ))

        summary_text = ""
        if is_finished:
            if story:
                story.story_status = "completed"
            # Quick summary (non-streaming)
            from app.agents.nodes import summary_node
            summary_state = {**state, "current_scene_text": scene_text}
            summary_result = await loop.run_in_executor(None, summary_node, summary_state)
            summary_text = summary_result.get("final_summary", "")
            parent_suggestion = summary_result.get("parent_suggestion", "")
            if summary_text:
                self.db.add(StoryMessage(
                    session_id=session.id, role="system",
                    content=json.dumps({"summary": summary_text, "parent_suggestion": parent_suggestion}, ensure_ascii=False),
                ))

        self.db.commit()

        complete_data = {
            "scene_text": scene_text,
            "options": options,
            "is_finished": is_finished,
            "scene_index": new_scene_index,
        }
        if is_finished:
            complete_data["summary"] = summary_text
        yield _sse("complete", complete_data)
