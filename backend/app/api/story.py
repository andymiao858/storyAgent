from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.response import success_response, error_response
from app.db.session import get_db
from app.models.child_profile import ChildProfile
from app.models.story import Story, StorySession, StoryMessage, StoryChoice
from app.models.user import User
from app.schemas.story import StoryStartRequest, StoryContinueRequest
from app.services.story_service import StoryService

router = APIRouter(prefix="/api/story", tags=["故事"])


@router.post("/start")
async def start_story(
    req: StoryStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    child = db.query(ChildProfile).filter(ChildProfile.id == req.child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="儿童档案不存在")
    if child.parent_id != current_user.id and current_user.role != "parent":
        raise HTTPException(status_code=403, detail="无权限访问该儿童档案")

    service = StoryService(db)
    result = await service.start_story(
        child=child,
        theme=req.theme,
        main_character=req.main_character,
        scene=req.scene,
    )
    return success_response(data=result)


@router.post("/continue")
async def continue_story(
    req: StoryContinueRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(StorySession).filter(StorySession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="故事会话不存在")
    if session.is_finished:
        raise HTTPException(status_code=400, detail="故事已结束")

    service = StoryService(db)
    result = await service.continue_story(
        session=session,
        selected_option=req.selected_option,
    )
    return success_response(data=result)


@router.get("/history/{child_id}")
def get_story_history(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    child = db.query(ChildProfile).filter(ChildProfile.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="儿童档案不存在")
    if child.parent_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限")

    stories = (
        db.query(Story)
        .filter(Story.child_id == child_id)
        .order_by(Story.created_at.desc())
        .all()
    )
    data = []
    for s in stories:
        latest_session = (
            db.query(StorySession)
            .filter(StorySession.story_id == s.id)
            .order_by(StorySession.created_at.desc())
            .first()
        )
        data.append({
            "id": s.id,
            "title": s.title,
            "theme": s.theme,
            "main_character": s.main_character,
            "scene": s.scene,
            "story_status": s.story_status,
            "session_id": latest_session.id if latest_session else None,
            "created_at": s.created_at.isoformat() if s.created_at else "",
        })
    return success_response(data=data)


@router.get("/session/{session_id}")
def get_session_detail(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(StorySession).filter(StorySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    story = db.query(Story).filter(Story.id == session.story_id).first()

    messages = (
        db.query(StoryMessage)
        .filter(StoryMessage.session_id == session_id)
        .order_by(StoryMessage.created_at)
        .all()
    )
    choices = (
        db.query(StoryChoice)
        .filter(StoryChoice.session_id == session_id)
        .order_by(StoryChoice.selected_at)
        .all()
    )

    state_json = session.story_state_json or {}
    last_options = state_json.get("last_options", [])

    return success_response(data={
        "session_id": session.id,
        "story_id": session.story_id,
        "current_scene_index": session.current_scene_index,
        "is_finished": session.is_finished,
        "last_options": last_options,
        "story": {
            "title": story.title if story else "",
            "theme": story.theme if story else "",
            "main_character": story.main_character if story else "",
            "scene": story.scene if story else "",
        } if story else None,
        "messages": [
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat() if m.created_at else ""}
            for m in messages
        ],
        "choices": [
            {
                "scene_index": c.scene_index,
                "option_key": c.option_key,
                "option_text": c.option_text,
                "selected_at": c.selected_at.isoformat() if c.selected_at else "",
            }
            for c in choices
        ],
    })


@router.post("/start/stream")
async def start_story_stream(
    req: StoryStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    child = db.query(ChildProfile).filter(ChildProfile.id == req.child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="儿童档案不存在")
    if child.parent_id != current_user.id and current_user.role != "parent":
        raise HTTPException(status_code=403, detail="无权限访问该儿童档案")

    service = StoryService(db)
    return StreamingResponse(
        service.start_story_stream(child=child, theme=req.theme,
                                   main_character=req.main_character, scene=req.scene),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/continue/stream")
async def continue_story_stream(
    req: StoryContinueRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(StorySession).filter(StorySession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="故事会话不存在")
    if session.is_finished:
        raise HTTPException(status_code=400, detail="故事已结束")

    service = StoryService(db)
    return StreamingResponse(
        service.continue_story_stream(session=session, selected_option=req.selected_option),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/story/{story_id}/session")
def get_latest_session_for_story(
    story_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the latest session for a story (used to resume)."""
    session = (
        db.query(StorySession)
        .filter(StorySession.story_id == story_id)
        .order_by(StorySession.created_at.desc())
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="没有找到该故事的会话")
    return success_response(data={"session_id": session.id})
