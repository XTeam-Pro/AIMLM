
import uuid
from datetime import datetime, timezone
from typing import Optional


from sqlmodel import SQLModel, Field, Relationship

from app.models.common import Transaction, UserProductInteraction, Product, Purchase,CartItem
from app.models.gamification import Team
from app.models.mlm import UserMLM

from app.schemas.types.gamification_types import RankType

from app.schemas.types.user_types import UserRole, UserStatus


class TimeZone(SQLModel, table=True):
    __tablename__ = "time_zones"
    name: str = Field(primary_key=True)
    offset: str = Field(max_length=6, regex=r"^[+-]\d{2}:\d{2}$")  # e.g. "+03:00"

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(..., unique=True, index=True, max_length=255)
    phone: str = Field(..., max_length=20)
    username: str = Field(..., max_length=100)
    full_name: str = Field(..., max_length=100)
    postcode: str = Field(max_length=12)
    address: str = Field(max_length=200)
    role: str = Field(default=UserRole.CLIENT)
    status: str = Field(default=UserStatus.ACTIVE)
    hashed_password: str = Field(..., max_length=128)
    registration_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = Field(default=True)
    rank: Optional[str] = Field(default=RankType.NEWBIE)

    mentor_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
    mentor: Optional["User"] = Relationship(back_populates="mentees", sa_relationship_kwargs={"remote_side": "User.id"})
    mentees: list["User"] = Relationship(back_populates="mentor")

    team_id: Optional[uuid.UUID] = Field(default=None, foreign_key="challenge_teams.id")
    team: Optional[Team] = Relationship(
        back_populates="members",
        sa_relationship_kwargs={"foreign_keys": "[User.team_id]"}
    )
    captained_teams: list[Team] = Relationship(
        back_populates="captain",
        sa_relationship_kwargs={"foreign_keys": "[Team.captain_id]"}
    )

    purchases: list[Purchase] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[Purchase.user_id]"}
    )
    buyer_transactions: list[Transaction] = Relationship(
        back_populates="buyer",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.buyer_id]"}
    )

    seller_transactions: list[Transaction] = Relationship(
        back_populates="seller",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.seller_id]"}
    )
    interactions: list[UserProductInteraction] = Relationship(back_populates="user")

    mlm_data: Optional[UserMLM] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[UserMLM.user_id]"}
    )
    cart_items: list[CartItem] = Relationship(back_populates="user")






