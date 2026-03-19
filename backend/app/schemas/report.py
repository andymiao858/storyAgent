from typing import List, Optional
from pydantic import BaseModel


class GrowthReportResponse(BaseModel):
    id: int
    child_id: int
    report_date: str
    summary: str
    behavior_tags: list
    recommendations: str

    model_config = {"from_attributes": True}
