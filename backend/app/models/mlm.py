import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship
if TYPE_CHECKING:
    from app.models.user import User


class UserMLM(SQLModel, table=True):
    __tablename__ = "user_mlm"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", unique=True)

    contract_type: str
    current_rank: str
    current_club: str

    personal_volume: Decimal = Field(default=Decimal(0))
    group_volume: Decimal = Field(default=Decimal(0))
    accumulated_volume: Decimal = Field(default=Decimal(0))
    binary_volume_left: Decimal = Field(default=Decimal(0))
    binary_volume_right: Decimal = Field(default=Decimal(0))

    sponsor_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
    placement_sponsor_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")

    user: "User" = Relationship(
        back_populates="mlm_data",
        sa_relationship_kwargs={"foreign_keys": "[UserMLM.user_id]"}
    )
    mentor_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
    mentor: Optional["User"] = Relationship(
        back_populates="mentees",
        sa_relationship_kwargs={
            "foreign_keys": "[UserMLM.mentor_id]",
            "remote_side": "User.id"
        }
    )
    business_centers: list["BusinessCenter"] = Relationship(back_populates="owner")
    bonuses: list["Bonus"] = Relationship(back_populates="user")
    activities: list["UserActivity"] = Relationship(back_populates="user")
    ranks_history: list["UserRankHistory"] = Relationship(back_populates="user")

class BusinessCenter(SQLModel, table=True):
    __tablename__ = "business_centers"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    parent_center_id: Optional[uuid.UUID] = Field(foreign_key="business_centers.id", default=None)
    position_in_parent: Optional[str] = Field(default=None)
    owner_id: uuid.UUID = Field(foreign_key="user_mlm.id")
    center_number: int = Field(..., ge=1, le=4)
    left_volume: Decimal = Field(default=Decimal(0))
    right_volume: Decimal = Field(default=Decimal(0))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    owner: "UserMLM" = Relationship(back_populates="business_centers")

class UserActivity(SQLModel, table=True):
    __tablename__ = "user_activities"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user_mlm.id")
    activity_type: str
    period_start: datetime
    period_end: datetime
    personal_volume: Decimal = Field(...)
    is_confirmed: bool = Field(default=False)
    confirmed_at: Optional[datetime] = Field(default=None)
    user: "UserMLM" = Relationship(back_populates="activities")

class Bonus(SQLModel, table=True):
    __tablename__ = "bonuses"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user_mlm.id")
    bonus_type: str
    amount: Decimal = Field(...)
    currency: str
    calculation_period: str
    is_paid: bool = Field(default=False)
    paid_at: Optional[datetime] = Field(default=None)
    user: "UserMLM" = Relationship(back_populates="bonuses")

class UserRankHistory(SQLModel, table=True):
    __tablename__ = "user_rank_history"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user_mlm.id")
    rank: str
    club: str
    achieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    qualification_period: str
    group_volume: Decimal = Field(...)
    personal_volume: Decimal = Field(...)
    user: "UserMLM" = Relationship(back_populates="ranks_history")

class UserHierarchy(SQLModel, table=True):
    __tablename__ = "user_hierarchy"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ancestor_id: uuid.UUID = Field(foreign_key="users.id")
    descendant_id: uuid.UUID = Field(foreign_key="users.id")
    level: int

class GenerationBonusMatrix(SQLModel, table=True):
    __tablename__ = "generation_bonus_matrix"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    rank: str
    generation: int
    bonus_percentage: Decimal = Field(...)