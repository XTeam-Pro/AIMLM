from __future__ import annotations
from typing import TYPE_CHECKING

import uuid
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field, Relationship
from app.schemas.gamification_schemas import AchievementTier
if TYPE_CHECKING:
    from app.models.core import User


class Achievement(SQLModel, table=True):
    __tablename__ = "achievements"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100)
    description: str = Field(max_length=500)
    tier: AchievementTier
    points_required: float = Field(ge=0)
    image_url: str = Field(max_length=500) # different images for different achievement tiers
    is_secret: bool = Field(default=False)

class UserAchievement(SQLModel, table=True):
    __tablename__ = "user_achievements"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    achievement_id: uuid.UUID = Field(foreign_key="achievements.id")
    unlocked_at: datetime = Field(default_factory= lambda: datetime.now(timezone.utc))
    progress: float = Field(default=None)  # For progressive achievements
    user: User = Relationship(back_populates="achievements")
    achievement: Achievement = Relationship()