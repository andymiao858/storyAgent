from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import require_parent
from app.core.response import success_response
from app.db.session import get_db
from app.models.parent_settings import ParentSettings
from app.models.user import User
from app.schemas.settings import ParentSettingsUpdate, ParentSettingsResponse

router = APIRouter(prefix="/api/parent", tags=["家长设置"])


@router.get("/settings")
def get_settings(
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    settings_obj = (
        db.query(ParentSettings)
        .filter(ParentSettings.parent_id == parent.id)
        .first()
    )
    if not settings_obj:
        settings_obj = ParentSettings(parent_id=parent.id)
        db.add(settings_obj)
        db.commit()
        db.refresh(settings_obj)
    return success_response(data=ParentSettingsResponse.model_validate(settings_obj).model_dump())


@router.put("/settings")
def update_settings(
    req: ParentSettingsUpdate,
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    settings_obj = (
        db.query(ParentSettings)
        .filter(ParentSettings.parent_id == parent.id)
        .first()
    )
    if not settings_obj:
        settings_obj = ParentSettings(parent_id=parent.id)
        db.add(settings_obj)
        db.commit()
        db.refresh(settings_obj)

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings_obj, key, value)

    db.commit()
    db.refresh(settings_obj)
    return success_response(data=ParentSettingsResponse.model_validate(settings_obj).model_dump())
