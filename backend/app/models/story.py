from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from app.db.session import Base


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("child_profiles.id"), nullable=False, index=True)
    title = Column(String(255), default="")
    theme = Column(String(100), nullable=False)
    main_character = Column(String(100), nullable=False)
    scene = Column(String(100), nullable=False)
    story_status = Column(String(50), default="in_progress")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class StorySession(Base):
    __tablename__ = "story_sessions"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False, index=True)
    child_id = Column(Integer, ForeignKey("child_profiles.id"), nullable=False, index=True)
    current_scene_index = Column(Integer, default=0)
    story_state_json = Column(JSON, default=dict)
    is_finished = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class StoryMessage(Base):
    __tablename__ = "story_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("story_sessions.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class StoryChoice(Base):
    __tablename__ = "story_choices"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("story_sessions.id"), nullable=False, index=True)
    scene_index = Column(Integer, nullable=False)
    option_key = Column(String(10), nullable=False)
    option_text = Column(String(500), nullable=False)
    selected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class GrowthReport(Base):
    __tablename__ = "growth_reports"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("child_profiles.id"), nullable=False, index=True)
    report_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    summary = Column(Text, default="")
    behavior_tags = Column(JSON, default=list)
    recommendations = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SafetyAuditLog(Base):
    __tablename__ = "safety_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("story_sessions.id"), nullable=False, index=True)
    scene_index = Column(Integer, nullable=False)
    original_text = Column(Text, nullable=False)
    audit_result = Column(String(50), nullable=False)
    risk_type = Column(String(100), default="")
    revised_text = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
