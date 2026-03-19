from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import require_parent
from app.core.response import success_response
from app.db.session import get_db
from app.models.child_profile import ChildProfile
from app.models.user import User
from app.schemas.child import ChildCreate, ChildUpdate, ChildResponse

router = APIRouter(prefix="/api/children", tags=["儿童档案"])


@router.get("")
def list_children(
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    children = (
        db.query(ChildProfile)
        .filter(ChildProfile.parent_id == parent.id, ChildProfile.is_active == True)
        .all()
    )
    data = [ChildResponse.model_validate(c).model_dump() for c in children]
    return success_response(data=data)


@router.post("")
def create_child(
    req: ChildCreate,
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    child = ChildProfile(
        parent_id=parent.id,
        nickname=req.nickname,
        age=req.age,
        avatar_url=req.avatar_url or "",
        interests=req.interests,
        reading_level=req.reading_level,
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    return success_response(data=ChildResponse.model_validate(child).model_dump())


@router.get("/{child_id}")
def get_child(
    child_id: int,
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    child = (
        db.query(ChildProfile)
        .filter(ChildProfile.id == child_id, ChildProfile.parent_id == parent.id)
        .first()
    )
    if not child:
        raise HTTPException(status_code=404, detail="儿童档案不存在")
    return success_response(data=ChildResponse.model_validate(child).model_dump())


@router.put("/{child_id}")
def update_child(
    child_id: int,
    req: ChildUpdate,
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    child = (
        db.query(ChildProfile)
        .filter(ChildProfile.id == child_id, ChildProfile.parent_id == parent.id)
        .first()
    )
    if not child:
        raise HTTPException(status_code=404, detail="儿童档案不存在")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(child, key, value)

    db.commit()
    db.refresh(child)
    return success_response(data=ChildResponse.model_validate(child).model_dump())
