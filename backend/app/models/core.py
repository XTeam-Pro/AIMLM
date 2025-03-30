import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict

from pydantic import EmailStr
from sqlalchemy import JSON
from sqlmodel import SQLModel, Field, Relationship


from app.models.gamification import UserAchievement, Achievement



class TimeZone(SQLModel, table=True):
    __tablename__ = "time_zones"
    id: int = Field(primary_key=True)
    name: str = Field(max_length=50)
    offset: str = Field(max_length=6)  # "+03:00"

class UserBase(SQLModel):
    email: str = Field(unique=True)
    phone: str
    username: str
    full_name: str
    postcode: str
    address: str
    role: str
    status: str
    timezone_id: Optional[int] = Field(foreign_key="time_zones.id")
    mentor_id: Optional[uuid.UUID] = Field(foreign_key="users.id")
    balance: float
    registration_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class User(UserBase, table=True):
    __tablename__ = "users"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    timezone: Optional["TimeZone"] = Relationship()
    mentor: Optional["User"] = Relationship(back_populates="mentees", sa_relationship_kwargs={"remote_side": "User.id"})
    mentees: List["User"] = Relationship(back_populates="mentor")
    transactions: List["Transaction"] = Relationship(back_populates="user")
    interactions: List["UserProductInteraction"] = Relationship(back_populates="user")
    cart_items: List["CartItem"] = Relationship(back_populates="user")
    achievements: List["UserAchievement"] = Relationship(back_populates="user")

class Product(SQLModel, table=True):
    __tablename__ = "products"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: str
    category: str
    price: float
    points_value: float
    image_url: str
    webinar_link: str
    is_active: bool
    is_collection: bool
    collection_items: Optional[List[Dict[str, Any]]] = Field(default=None, sa_type=JSON)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    interactions: List["UserProductInteraction"] = Relationship(back_populates="product")

class CartItem(SQLModel, table=True):
    __tablename__ = "cart_items"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    product_id: uuid.UUID = Field(foreign_key="products.id")
    quantity: int
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user: User = Relationship(back_populates="cart_items")
    product: Product = Relationship()




class UserProductInteraction(SQLModel, table=True):
    __tablename__ = "user_product_interactions"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    product_id: Optional[uuid.UUID] = Field(foreign_key="products.id")
    interaction_type: str
    points_awarded: float
    interaction_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    achievement_id: Optional[uuid.UUID] = Field(foreign_key="achievements.id")
    additional_info: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)
    user: User = Relationship(back_populates="interactions")
    product: Optional[Product] = Relationship(back_populates="interactions")
    achievement: Optional["Achievement"] = Relationship()


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    amount: float
    points: float
    type: str
    status: str = Field(default="pending")
    product_id: Optional[uuid.UUID] = Field(foreign_key="products.id")
    achievement_id: Optional[uuid.UUID] = Field(foreign_key="achievements.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    additional_info: Dict[str, Any] = Field(default=None, sa_type=JSON) # Referral level is being held: {"referral_level": 3, "mentor_id": "uuid"}
    user: User = Relationship(back_populates="transactions")
    product: Product = Relationship()
    achievement: Optional["Achievement"] = Relationship()