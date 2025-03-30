

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
import uuid

class AchievementTier(str, Enum):
    """Achievement level in the gamification system"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class AchievementBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    tier: AchievementTier = Field(...,)
    points_required: float = Field(..., ge=0)
    image_url: str = Field(..., max_length=500)
    is_secret: bool = Field(default=False)

class AchievementCreate(AchievementBase):
    pass

class AchievementUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    tier: Optional[AchievementTier] = None
    points_required: Optional[float] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=500)
    is_secret: Optional[bool] = None

class AchievementPublic(AchievementBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class UserAchievementBase(BaseModel):
    progress: Optional[float] = Field(None ,ge=0, le=100,)

class UserAchievementCreate(UserAchievementBase):
    achievement_id: uuid.UUID = Field(...,)

class UserAchievementUpdate(UserAchievementBase):
    pass

class UserAchievementPublic(UserAchievementBase):
    id: uuid.UUID
    achievement: AchievementPublic
    unlocked_at: datetime
    user_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

    @property
    def is_unlocked(self) -> bool:
        """
        Checks whether an achievement is unlocked or not
        """
        return self.progress is None or self.progress >= 100