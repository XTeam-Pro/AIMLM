
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional


from sqlmodel import SQLModel, Field, Relationship

from app.models.common import Transaction, UserProductInteraction, Purchase,CartItem
from app.models.mlm import UserMLM
from app.schemas.types.common_types import MLMRankType
from app.schemas.types.localization_types import CurrencyType

from app.schemas.types.user_types import UserRole, UserStatus, WalletType


class ExchangeRate(SQLModel, table=True):
    __tablename__ = "exchange_rates" #TODO: we are going to have some external API for this

    id: int | None = Field(default=None, primary_key=True)
    from_currency: CurrencyType = Field(index=True)
    to_currency: CurrencyType = Field(index=True)
    rate: Decimal = Field(..., ge=0)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Wallet(SQLModel, table=True):
    __tablename__ = "wallets" #TODO: we are going to have some external API for this
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    currency: str = Field(default=CurrencyType.RUB)
    type: str = Field(default=WalletType.BONUS)
    balance: Decimal = Field(default=0, ge=0)
    is_active: bool = Field(default=True)

    user: "User" = Relationship(back_populates="wallets")


class TimeZone(SQLModel, table=True):
    __tablename__ = "time_zones"  #TODO: we are going to have some external API for this
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    country: str = Field(nullable=False)
    name: str = Field(nullable=False)
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
    country: str = Field(max_length=100)
    role: str = Field(default=UserRole.CLIENT)
    status: str = Field(default=UserStatus.ACTIVE)
    referral_code: str = Field(default_factory=lambda: uuid.uuid4().hex[:8], unique=True, index=True)
    hashed_password: str = Field(..., max_length=128)
    registration_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = Field(default=True)
    rank: Optional[str] = Field(default=None)

    wallets: list["Wallet"] = Relationship(back_populates="user")

    mentees: list["UserMLM"] = Relationship(
        back_populates="mentor",
        sa_relationship_kwargs={
            "foreign_keys": "[UserMLM.mentor_id]"
        }
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






