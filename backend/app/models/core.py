
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import JSON
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

from app.models.gamification import UserAchievement, Achievement


class TimeZone(SQLModel, table=True):
    __tablename__ = "time_zones"
    id: int = Field(primary_key=True)
    name: str = Field(max_length=50)
    offset: str = Field(max_length=6, regex=r"^[+-]\d{2}:\d{2}$")  # e.g. "+03:00"


class UserRole(str, Enum):
    CLIENT = "client"
    MANAGER = "manager"
    MENTOR = "mentor"
    DISTRIBUTOR = "distributor"
    ADMIN = "admin"


class UserStatus(str, Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    PENDING = "pending"
    BLOCKED = "blocked"


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True, max_length=255)
    phone: str = Field(max_length=20, regex=r"^\+?[1-9]\d{1,14}$")
    username: str = Field(max_length=100, min_length=6)
    full_name: str = Field(max_length=100)
    postcode: str = Field(max_length=12)
    address: str = Field(max_length=200)
    role: str = Field(default=UserRole.CLIENT)
    status: str = Field(default=UserStatus.ACTIVE)
    cash_balance: Decimal = Field(default=Decimal(0), max_digits=12, decimal_places=2)
    pv_balance: Decimal = Field(default=Decimal(0), max_digits=12, decimal_places=2)
    timezone_id: Optional[int] = Field(default=None, foreign_key="time_zones.id")
    mentor_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
    registration_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class User(UserBase, table=True):
    __tablename__ = "users"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field(max_length=128)

    # Relationships
    timezone: Optional["TimeZone"] = Relationship()
    mentor: Optional["User"] = Relationship(
        back_populates="mentees",
        sa_relationship_kwargs={"remote_side": "User.id"}
    )
    mentees: List["User"] = Relationship(back_populates="mentor")
    transactions: List["Transaction"] = Relationship(back_populates="user")
    interactions: List["UserProductInteraction"] = Relationship(back_populates="user")
    cart_items: List["CartItem"] = Relationship(back_populates="user")
    achievements: List["UserAchievement"] = Relationship(back_populates="user")


class ProductCategory(str, Enum):
    COSMETICS = "cosmetics"
    NUTRITION = "nutrition"
    COURSE = "course"
    WEBINAR = "webinar"
    COLLECTION = "collection"


class Product(SQLModel, table=True):
    __tablename__ = "products"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=100)
    description: str = Field(max_length=2000)
    category: str
    price: Decimal = Field(max_digits=12, decimal_places=2, ge=0)
    pv_value: Decimal = Field(default=Decimal(0), max_digits=12, decimal_places=2, ge=0)
    image_url: Optional[str] = Field(default=None, max_length=500)
    webinar_link: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    is_collection: bool = Field(default=False)
    collection_items: Optional[List[Dict[str, Any]]] = Field(default=None, sa_type=JSON)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    interactions: List["UserProductInteraction"] = Relationship(back_populates="product")


class CartItem(SQLModel, table=True):
    __tablename__ = "cart_items"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    product_id: uuid.UUID = Field(foreign_key="products.id")
    quantity: int = Field(default=1, ge=1)
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    user: "User" = Relationship(back_populates="cart_items")
    product: "Product" = Relationship()


class InteractionType(str, Enum):
    VIEW = "view"
    PURCHASE = "purchase"
    CART_ADD = "cart_add"
    FAVORITE = "favorite"
    WEBINAR_REGISTER = "webinar_register"
    WEBINAR_ATTEND = "webinar_attend"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"


class UserProductInteraction(SQLModel, table=True):
    __tablename__ = "user_product_interactions"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    product_id: Optional[uuid.UUID] = Field(default=None, foreign_key="products.id")
    interaction_type: str
    pv_awarded: Decimal = Field(default=Decimal(0), max_digits=12, decimal_places=2, ge=0)
    interaction_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    achievement_id: Optional[uuid.UUID] = Field(default=None, foreign_key="achievements.id")
    additional_info: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)

    # Relationships
    user: "User" = Relationship(back_populates="interactions")
    product: Optional["Product"] = Relationship(back_populates="interactions")
    achievement: Optional["Achievement"] = Relationship()


class TransactionType(str, Enum):
    PURCHASE = "purchase"
    BONUS = "bonus"
    PENALTY = "penalty"
    ACHIEVEMENT = "achievement"
    REFERRAL = "referral"
    CASH_OUT = "cash_out"
    CASH_IN = "cash_in"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    FAILED = "failed"
    COMPLETED = "completed"


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    cash_amount: Decimal = Field(max_digits=12, decimal_places=2)
    pv_amount: Decimal = Field(max_digits=12, decimal_places=2)
    type: str = Field(default=TransactionStatus.PENDING)
    product_id: Optional[uuid.UUID] = Field(default=None, foreign_key="products.id")
    achievement_id: Optional[uuid.UUID] = Field(default=None, foreign_key="achievements.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    additional_info: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)

    # Relationships
    user: "User" = Relationship(back_populates="transactions")
    product: Optional["Product"] = Relationship()
    achievement: Optional["Achievement"] = Relationship()