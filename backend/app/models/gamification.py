from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid

from sqlmodel import SQLModel, Field


class Achievement(SQLModel, table=True):
    __tablename__ = "achievements"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    description: str
    tier: str
    points_required: Decimal
    is_secret: bool = Field(default=False)
    rank: str = Field(default=None)

class UserAchievement(SQLModel, table=True):
    __tablename__ = "user_achievements"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    achievement_id: uuid.UUID = Field(foreign_key="achievements.id")
    is_unlocked: bool = Field(default=False)
    unlocked_at: Optional[datetime] = Field(default=None)
    progress: Decimal = Field(default=Decimal(0))

class Challenge(SQLModel, table=True):
    __tablename__ = "challenges"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    description: str
    challenge_type: str
    start_date: datetime
    end_date: datetime
    reward_type: str
    reward_value: Decimal
    min_rank: str
    is_active: bool = Field(default=True)
    created_by: uuid.UUID = Field(foreign_key="users.id")

class UserChallenge(SQLModel, table=True):
    __tablename__ = "challenge_participants" # TODO how to connect user/users to it 
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    challenge_id: uuid.UUID = Field(foreign_key="challenges.id")
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
    current_progress: Decimal = Field(default=Decimal(0))
    is_completed: bool = Field(default=False)
    completed_at: Optional[datetime] = Field(default=None)
    reward_issued: bool = Field(default=False)

