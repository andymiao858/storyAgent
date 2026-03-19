"""LangGraph workflow orchestration for story generation."""
import logging

from langgraph.graph import StateGraph, END

from app.agents.state import StoryState
from app.agents.nodes import (
    user_profile_node,
    story_planning_node,
    retrieval_node,
    story_generation_node,
    safety_audit_node,
    interaction_control_node,
    summary_node,
)

logger = logging.getLogger(__name__)


def _should_end(state: StoryState) -> str:
    if state.get("story_finished"):
        return "summary"
    return "done"


def build_start_workflow() -> StateGraph:
    """Start workflow with parallel planning + retrieval:

    user_profile ─┬─ story_planning (LLM) ─┬─ story_generation (LLM) ─ safety ─ done
                  └─ retrieval (FAISS)     ─┘

    Planning and retrieval run in parallel since retrieval only needs
    theme/character/scene (not the plan). This saves ~0.3s of serial RAG time
    and the two branches join before generation.
    """
    workflow = StateGraph(StoryState)

    workflow.add_node("user_profile", user_profile_node)
    workflow.add_node("story_planning", story_planning_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("story_generation", story_generation_node)
    workflow.add_node("safety_audit", safety_audit_node)
    workflow.add_node("summary", summary_node)

    workflow.set_entry_point("user_profile")

    # Fan out: profile → planning AND retrieval in parallel
    workflow.add_edge("user_profile", "story_planning")
    workflow.add_edge("user_profile", "retrieval")

    # Fan in: both feed into generation
    workflow.add_edge("story_planning", "story_generation")
    workflow.add_edge("retrieval", "story_generation")

    workflow.add_edge("story_generation", "safety_audit")
    workflow.add_conditional_edges(
        "safety_audit",
        _should_end,
        {"summary": "summary", "done": END},
    )
    workflow.add_edge("summary", END)

    return workflow.compile()


def build_continue_workflow() -> StateGraph:
    """Continue workflow: interaction_control → retrieval → generation → safety"""
    workflow = StateGraph(StoryState)

    workflow.add_node("interaction_control", interaction_control_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("story_generation", story_generation_node)
    workflow.add_node("safety_audit", safety_audit_node)
    workflow.add_node("summary", summary_node)

    workflow.set_entry_point("interaction_control")
    workflow.add_edge("interaction_control", "retrieval")
    workflow.add_edge("retrieval", "story_generation")
    workflow.add_edge("story_generation", "safety_audit")
    workflow.add_conditional_edges(
        "safety_audit",
        _should_end,
        {"summary": "summary", "done": END},
    )
    workflow.add_edge("summary", END)

    return workflow.compile()
