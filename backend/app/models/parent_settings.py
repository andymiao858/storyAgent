from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, ForeignKey, JSON
from app.db.session import Base


class ParentSettings(Base):
    __tablename__ = "parent_settings"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    blocked_topics = Column(JSON, default=list)
    preferred_themes = Column(JSON, default=list)
    daily_limit_minutes = Column(Integer, default=60)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
