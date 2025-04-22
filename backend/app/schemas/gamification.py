from pydantic import BaseModel, ConfigDict, Field
import uuid
from decimal import Decimal
from typing import Optional
from datetime import datetime, timezone

from app.schemas.types.common_types import MLMRankType
from app.schemas.types.gamification_types import ChallengeType, RankType
from app.schemas.users import UserPublic


class AchievementBase(BaseModel):
    name: str
    description: str
    tier: str
    points_required: Decimal
    is_secret: bool
    rank: Optional[MLMRankType] = Field(default=None)


class AchievementCreate(AchievementBase):
    pass


class AchievementUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    tier: Optional[str]
    points_required: Optional[Decimal]
    is_secret: Optional[bool]
    #rank_requirement: MLMRankType = Field(default=MLMRankType.NEWBIE)


class AchievementPublic(AchievementBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class UserAchievementBase(BaseModel):
    progress: Decimal = Field(default=Decimal(0))
    is_unlocked: bool = Field(default=False)
    unlocked_at: Optional[datetime] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)

# Схема для создания нового UserAchievement
class UserAchievementCreate(UserAchievementBase):
    user_id: uuid.UUID
    achievement_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class UserAchievementUpdate(BaseModel):
    progress: Optional[Decimal]
    is_unlocked: Optional[bool]
    unlocked_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class UserAchievementPublic(UserAchievementBase):
    id: uuid.UUID
    user_id: uuid.UUID
    achievement_id: uuid.UUID
    achievement: AchievementPublic | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)

class ChallengeBase(BaseModel):
    name: str
    description: str
    challenge_type: ChallengeType = Field(default=ChallengeType.PERSONAL)
    start_date: datetime
    end_date: datetime
    reward_type: str # PV, product, rank_boost
    reward_value: Decimal
    min_rank: MLMRankType = Field(default=MLMRankType.NEWBIE)
    is_active: bool = Field(default=True) # switch off the challenge temporarily
    created_by: uuid.UUID


class ChallengeCreate(ChallengeBase):
    pass


class ChallengeUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    challenge_type: ChallengeType
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    reward_type: Optional[str]
    reward_value: Optional[Decimal]
    min_rank: Optional[uuid.UUID]
    is_active: Optional[bool]


class ChallengePublic(ChallengeBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class ChallengeParticipantBase(BaseModel):
    current_progress: Decimal
    is_completed: bool
    completed_at: Optional[datetime]
    reward_issued: bool


class ChallengeParticipantCreate(ChallengeParticipantBase):
    challenge_id: uuid.UUID
    user_id: Optional[uuid.UUID]
    team_id: Optional[uuid.UUID]


class ChallengeParticipantUpdate(ChallengeParticipantBase):
    pass


class ChallengeParticipantPublic(ChallengeParticipantBase):
    id: uuid.UUID
    challenge_id: uuid.UUID
    user_id: Optional[uuid.UUID]
    team_id: Optional[uuid.UUID]
    model_config = ConfigDict(from_attributes=True)


class UserRankBase(BaseModel):
    name: RankType
    level: int
    min_pv: Decimal
    min_team_pv: Decimal
    min_mentees: int
    bonus_percentage: Decimal
    challenge_unlock: bool


class UserRankCreate(UserRankBase):
    pass


class UserRankUpdate(BaseModel):
    name: RankType
    level: Optional[int]
    min_pv: Optional[Decimal]
    min_team_pv: Optional[Decimal]
    min_mentees: Optional[int]
