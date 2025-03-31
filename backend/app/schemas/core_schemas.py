import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, Field

from app.models.core import User
from app.schemas.gamification_schemas import AchievementPublic


class Token(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")


class TokenData(BaseModel):
    user_id: Optional[uuid.UUID] = Field(default=None)

class TokenPayload(BaseModel):
    sub: str | None = None

class PasswordChange(BaseModel):
    current_password: str = Field(...,)
    new_password: str = Field(..., min_length=8, max_length=40)


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(...,)

class NewPassword(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)

class PasswordReset(BaseModel):
    token: str = Field(...,)
    new_password: str = Field(..., min_length=8)

class UpdatePassword(BaseModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)

class Message(BaseModel):
    message: str = Field(..., max_length=100)

class UserRole(str, Enum):
    CLIENT = "client"
    MANAGER = "manager"
    MENTOR = "mentor"
    ADMIN = "admin"


class UserStatus(str, Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    PENDING = "pending"
    BLOCKED = "blocked"


class ProductCategory(str, Enum):
    COSMETICS = "cosmetics"
    NUTRITION = "nutrition"
    COURSE = "course"
    WEBINAR = "webinar"
    COLLECTION = "collection"


class InteractionType(str, Enum):
    VIEW = "view"
    PURCHASE = "purchase"
    CART_ADD = "cart_add"
    FAVORITE = "favorite"
    WEBINAR_REGISTER = "webinar_register"
    WEBINAR_ATTEND = "webinar_attend"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"


class TransactionType(str, Enum):
    PURCHASE = "purchase"    # Покупка товара (amount < 0, points > 0)
    BONUS = "bonus"          # Бонус за активность (amount = 0, points > 0)
    PENALTY = "penalty"      # Штраф (amount = 0, points < 0)
    ACHIEVEMENT = "achievement" # Награда за достижение
    REFERRAL = "referral"    # Реферальный бонус (amount > 0)

class TransactionStatus(str, Enum):
    PENDING = "pending"
    FAILED = "failed"
    COMPLETED = "completed"


class TimeZoneBase(BaseModel):
    name: str = Field(..., max_length=50)
    offset: str = Field(..., max_length=6, pattern=r"^[+-]\d{2}:\d{2}$")


class TimeZoneCreate(TimeZoneBase):
    pass


class TimeZoneUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=50)
    offset: Optional[str] = Field(default=None, max_length=6, pattern=r"^[+-]\d{2}:\d{2}$")


class TimeZonePublic(TimeZoneBase):
    id: int = Field(...)

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: str | EmailStr = Field(..., max_length=255)
    username: str = Field(..., max_length=100, min_length=6)
    phone: str = Field(..., max_length=20, pattern=r"^\+?[1-9]\d{1,14}$")
    full_name: str = Field(..., max_length=100)

class UserRegister(UserBase):
    hashed_password: str = Field(..., min_length=8, max_length=64)
    address: str = Field(...,
                         min_length=5,
                         max_length=200,
                         examples=["123 Main St, Apt 4B, New York"],
                         description="Full street address including apartment number")
    postcode: str = Field(...,
                          min_length=3,
                          max_length=12,
                          examples=["10001", "SW1A 1AA"],
                          description="Postal/ZIP code in local format")
    role: UserRole = Field(default=UserRole.CLIENT)
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    balance: Optional[float] = Field(default=0, ge=0)

    @field_validator('address')
    def validate_address(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r'^[\w\s\-,.#]+$', v):
            raise ValueError(
                "Address contains invalid characters. Only letters, numbers, spaces, hyphens, commas, dots and # are allowed")
        if len(v.split(',')) < 2:
            raise ValueError("Address should include at least street and city separated by comma")
        return v.title()

    @field_validator('postcode')
    def validate_postcode(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r'^[A-Z0-9\- ]{3,12}$', v):
            raise ValueError(
                "Postcode must contain only letters, numbers, spaces or hyphens, "
                "3-12 characters long"
            )
        return v

    @field_validator('hashed_password')
    def validate_password_complexity(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

    @field_validator('phone')
    def validate_phone(cls, v):
        if not v.startswith('+'):
            raise ValueError('Phone must start with +')
        if len(v) < 10:
            raise ValueError('Phone too short')
        return v

    @field_validator('email')
    def validate_email_domain(cls, v):
        if 'example.com' in v:
            raise ValueError('Example.com domain is not allowed')
        return v


class UserCreate(UserRegister):
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    role: UserRole = Field(default=UserRole.CLIENT)
    timezone_id: Optional[int] = Field(default=0)
    mentor_id: Optional[uuid.UUID] = Field(default=None)


class UserUpdate(BaseModel):
    email: EmailStr = Field(default=None)
    phone: Optional[str] = Field(default=None, max_length=20, pattern=r"^\+?[1-9]\d{1,14}$")
    full_name: Optional[str] = Field(default=None, max_length=100)
    role: UserRole = Field(default=None)
    status: Optional[UserStatus] = Field(default=None)
    timezone_id: Optional[int] = Field(default=None)
    mentor_id: Optional[uuid.UUID] = Field(default=None)
    balance: Optional[float] = Field(default=None, ge=0)

class UserUpdateMe(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UserPublic(UserBase):
    id: uuid.UUID = Field(...)
    role: UserRole = Field(...)
    status: UserStatus = Field(...)
    balance: float = Field(...)
    registration_date: datetime = Field(...)
    timezone: Optional[TimeZonePublic] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)

class UsersPublic(BaseModel):
    data: list[User]
    count: int

class ProductBase(BaseModel):
    id: uuid.UUID = Field(...)
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=2000)
    category: ProductCategory = Field(...)
    price: float = Field(..., ge=0)
    points_value: float = Field(..., ge=0)


class ProductCreate(ProductBase):
    image_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    webinar_link: str = Field(default=None, max_length=500)
    is_collection: bool = Field(default=False)
    collection_items: Optional[List[Dict[str, Any]]] = Field(default=None)

    @field_validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return round(v, 2)

    @field_validator('webinar_link')
    def validate_webinar_link(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Webinar link must start with http:// or https://')
        return v


class ProductUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)
    category: Optional[ProductCategory] = Field(default=None)
    price: Optional[float] = Field(default=None, ge=0)
    points_value: Optional[float] = Field(default=None, ge=0)
    image_url: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)
    webinar_link: Optional[str] = Field(default=None, max_length=500)
    is_collection: Optional[bool] = Field(default=None)
    collection_items: Optional[List[Dict[str, Any]]] = Field(default=None)


class ProductPublic(ProductBase):
    image_url: Optional[str] = Field(default=None)
    is_active: bool = Field(...)
    created_at: datetime = Field(...)

    model_config = ConfigDict(from_attributes=True)


class UserProductInteractionBase(BaseModel):
    interaction_type: InteractionType = Field(...)
    points_awarded: float = Field(default=0.0, ge=0)
    additional_info: Optional[Dict[str, Any]] = Field(default=None)


class UserProductInteractionCreate(UserProductInteractionBase):
    product_id: Optional[uuid.UUID] = Field(default=None)
    user_id: uuid.UUID = Field(...)
    achievement_id: Optional[uuid.UUID] = Field(default=None)


class UserProductInteractionUpdate(BaseModel):
    interaction_type: Optional[InteractionType] = Field(default=None)
    points_awarded: Optional[float] = Field(default=None, ge=0)
    additional_info: Optional[Dict[str, Any]] = Field(default=None)

    @field_validator('points_awarded')
    def validate_points(cls, v):
        if v is not None and v < 0:
            raise ValueError('Points awarded cannot be negative')
        return v


class UserProductInteractionPublic(UserProductInteractionBase):
    id: uuid.UUID = Field(...)
    interaction_date: datetime = Field(...)
    user_id: uuid.UUID = Field(...)
    product_id: Optional[uuid.UUID] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    amount: float = Field(...)
    points: float = Field(..., ge=0)
    type: TransactionType = Field(...)
    additional_info: Optional[Dict[str, Any]] = Field(default=None, description="Additional transaction metadata")


class TransactionCreate(TransactionBase):
    product_id: Optional[uuid.UUID] = Field(...)
    achievement_id: Optional[uuid.UUID] = Field(default=None)
    user_id: uuid.UUID = Field(...)

    @field_validator('amount')
    def validate_amount(cls, v, values):
        if v <= 0 and values.get('type') != TransactionType.BONUS:
            raise ValueError('Amount must be positive for non-bonus transactions')
        return v

    @field_validator('points')
    def validate_points(cls, v, values):
        if v < 0 and values.get('type') != TransactionType.PENALTY:
            raise ValueError('Points can be negative only for penalty transactions')
        return v


class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(...,)
    points: Optional[float] = Field(default=None, ge=0)
    type: TransactionType = Field(...,)
    status: TransactionStatus = Field(...,)
    additional_info: Optional[Dict[str, Any]] = Field(default=None, description="Updated transaction metadata")

    @field_validator('amount')
    def validate_updated_amount(cls, v, values):
        if v is not None and v <= 0 and values.get('type') != TransactionType.BONUS:
            raise ValueError('Amount must be positive for non-bonus transactions')
        return v


class TransactionPublic(TransactionBase):
    id: uuid.UUID = Field(...)
    created_at: datetime = Field(...)
    user_id: uuid.UUID = Field(...)
    product_id: uuid.UUID = Field(...)
    achievement: Optional[AchievementPublic] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class CartItemBase(BaseModel):
    quantity: int = Field(default=1, ge=1)


class CartItemCreate(CartItemBase):
    product_id: uuid.UUID = Field(...)
    user_id: uuid.UUID = Field(...)


class CartItemUpdate(BaseModel):
    quantity: Optional[int] = Field(default=None, ge=1)


class CartItemPublic(CartItemBase):
    id: uuid.UUID = Field(...)
    product: ProductPublic = Field(...)
    added_at: datetime = Field(...)
    user_id: uuid.UUID = Field(...)

    model_config = ConfigDict(from_attributes=True)