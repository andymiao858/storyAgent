from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import require_parent
from app.core.response import success_response
from app.db.session import get_db
from app.models.child_profile import ChildProfile
from app.models.story import GrowthReport, Story, StorySession, StoryChoice
from app.models.user import User
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/reports", tags=["成长报告"])


@router.get("/{child_id}")
def get_reports(
    child_id: int,
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id, ChildProfile.parent_id == parent.id
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail="儿童档案不存在")

    reports = (
        db.query(GrowthReport)
        .filter(GrowthReport.child_id == child_id)
        .order_by(GrowthReport.report_date.desc())
        .all()
    )
    data = []
    for r in reports:
        data.append({
            "id": r.id,
            "child_id": r.child_id,
            "report_date": r.report_date.isoformat() if r.report_date else "",
            "summary": r.summary,
            "behavior_tags": r.behavior_tags,
            "recommendations": r.recommendations,
        })
    return success_response(data=data)


@router.get("/{child_id}/latest")
async def get_latest_report(
    child_id: int,
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id, ChildProfile.parent_id == parent.id
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail="儿童档案不存在")

    service = ReportService(db)
    report = await service.generate_or_get_latest_report(child)
    return success_response(data=report)
