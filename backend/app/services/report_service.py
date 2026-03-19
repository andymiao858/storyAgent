"""Growth report generation service."""
import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, SystemMessage

from app.models.child_profile import ChildProfile
from app.models.story import Story, StorySession, StoryChoice, StoryMessage, GrowthReport
from app.utils.llm import get_llm

logger = logging.getLogger(__name__)


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    async def generate_or_get_latest_report(self, child: ChildProfile) -> dict:
        existing = (
            self.db.query(GrowthReport)
            .filter(GrowthReport.child_id == child.id)
            .order_by(GrowthReport.report_date.desc())
            .first()
        )

        stories = (
            self.db.query(Story)
            .filter(Story.child_id == child.id)
            .order_by(Story.created_at.desc())
            .limit(20)
            .all()
        )

        if not stories:
            return {
                "id": 0,
                "child_id": child.id,
                "report_date": datetime.now(timezone.utc).isoformat(),
                "summary": f"{child.nickname}还没有开始故事冒险，快去开始第一个故事吧！",
                "behavior_tags": [],
                "recommendations": "鼓励孩子选择一个感兴趣的主题，开始第一个故事旅程。",
            }

        total_stories = len(stories)
        completed = sum(1 for s in stories if s.story_status == "completed")
        themes = list(set(s.theme for s in stories))

        all_choices = []
        for s in stories[:10]:
            sessions = self.db.query(StorySession).filter(StorySession.story_id == s.id).all()
            for sess in sessions:
                choices = self.db.query(StoryChoice).filter(StoryChoice.session_id == sess.id).all()
                all_choices.extend([c.option_text for c in choices])

        llm = get_llm(temperature=0.6)
        prompt = f"""你是一位儿童教育专家，请根据以下数据为家长生成一份成长报告。

儿童信息：
- 昵称：{child.nickname}
- 年龄：{child.age}岁
- 兴趣：{', '.join(child.interests or [])}
- 阅读水平：{child.reading_level}

阅读数据：
- 总故事数：{total_stories}
- 完成故事数：{completed}
- 涉及主题：{', '.join(themes)}
- 互动选择数：{len(all_choices)}

孩子的部分互动选择：
{chr(10).join(all_choices[:15])}

请生成JSON格式的成长报告：
{{"summary": "成长总结(100-150字)", "behavior_tags": ["品质标签1", "品质标签2", ...], "recommendations": "给家长的建议(80-120字)"}}"""

        messages = [
            SystemMessage(content="你是一位专业的儿童教育心理专家，善于从儿童的行为数据中发现成长特点并给出积极的引导建议。"),
            HumanMessage(content=prompt),
        ]

        try:
            response = llm.invoke(messages)
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            result = json.loads(content)
        except Exception as e:
            logger.warning(f"LLM report generation failed: {e}")
            result = {
                "summary": f"{child.nickname}已经完成了{completed}个故事，展现了对{', '.join(themes[:3])}主题的浓厚兴趣。",
                "behavior_tags": ["积极探索", "好奇心强"],
                "recommendations": "继续鼓励孩子探索不同主题的故事，培养多元化的兴趣。",
            }

        report = GrowthReport(
            child_id=child.id,
            summary=result.get("summary", ""),
            behavior_tags=result.get("behavior_tags", []),
            recommendations=result.get("recommendations", ""),
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        return {
            "id": report.id,
            "child_id": report.child_id,
            "report_date": report.report_date.isoformat() if report.report_date else "",
            "summary": report.summary,
            "behavior_tags": report.behavior_tags,
            "recommendations": report.recommendations,
        }
