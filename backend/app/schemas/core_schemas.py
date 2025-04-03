import re
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, Field

from app.schemas.gamification_schemas import AchievementPublic
from app.schemas.types import UserRole, UserStatus, ProductCategory, InteractionType, TransactionType, TransactionStatus


class Token(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")


class TokenData(BaseModel):
    user_id: Optional[uuid.UUID] = Field(default=None)


class TokenPayload(BaseModel):
    sub: str | None = None


class PasswordChange(BaseModel):
    current_password: str = Field(...)
    new_password: str = Field(..., min_length=8, max_length=40)


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(...)


class NewPassword(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


class PasswordReset(BaseModel):
    token: str = Field(...)
    new_password: str = Field(..., min_length=8)


class UpdatePassword(BaseModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class Message(BaseModel):
    message: str = Field(..., max_length=100)



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
    username: str = Field(
        ...,
        min_length=6,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
        examples=["john_doe123"],
        description="Username may only contain letters, numbers and underscores"
    )
    phone: str = Field(..., max_length=20, pattern=r"^\+?[1-9]\d{1,14}$")
    full_name: str = Field(..., max_length=100)

    @field_validator('email')
    def validate_email_rfc(cls, v):
        try:
            result = validate_email(v, check_deliverability=False)
            # Whitelist admin@example.com
            if v.lower() != "admin@example.com":
                blocked_domains = {'tempmail.com', 'example.com'}
                domain = v.split('@')[-1]
                if domain in blocked_domains:
                    raise ValueError('Disposable emails are not allowed')
            return result.normalized
        except EmailNotValidError as e:
            raise ValueError(str(e))


class UserRegister(UserBase):
    hashed_password: str = Field(..., min_length=8, max_length=64, examples=["String123"])
    address: str = Field(
        ...,
        min_length=5,
        max_length=200,
        examples=["123 Main St, Apt 4B, New York"],
        description="Full street address including apartment number"
    )
    postcode: str = Field(
        ...,
        min_length=3,
        max_length=12,
        examples=["10001", "SW1A 1AA"],
        description="Postal/ZIP code in local format"
    )
    role: UserRole = Field(default=UserRole.CLIENT)
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    cash_balance: float = Field(default=0.0, ge=0, description="Real money balance")
    pv_balance: float = Field(default=0.0, ge=0, description="Personal Volume points balance")

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


class UserCreate(UserRegister):
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    role: UserRole = Field(default=UserRole.CLIENT)
    timezone_id: Optional[int] = Field(default=1)
    mentor_id: Optional[uuid.UUID] = Field(default=None)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(default=None)
    phone: Optional[str] = Field(default=None, max_length=20, pattern=r"^\+?[1-9]\d{1,14}$")
    full_name: Optional[str] = Field(default=None, max_length=100)
    role: Optional[UserRole] = Field(default=None)
    status: Optional[UserStatus] = Field(default=None)
    timezone_id: Optional[int] = Field(default=None)
    mentor_id: Optional[uuid.UUID] = Field(default=None)
    cash_balance: Optional[float] = Field(default=None, ge=0)
    pv_balance: Optional[float] = Field(default=None, ge=0)


class UserUpdateMe(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = Field(default=None, max_length=255)


class UserPublic(UserBase):
    id: uuid.UUID = Field(...)
    role: UserRole = Field(...)
    status: UserStatus = Field(...)
    cash_balance: Decimal = Field(..., ge=0, description="Real money balance")
    pv_balance: Decimal = Field(..., ge=0, description="Personal Volume points balance")
    registration_date: datetime = Field(...)
    timezone: Optional[TimeZonePublic] = Field(default=None)
    achievements: List[AchievementPublic] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UsersPublic(BaseModel):
    data: list[UserPublic]
    count: int


class ProductBase(BaseModel):
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=2000)
    category: ProductCategory = Field(...)
    price: float = Field(..., ge=0, description="Price in real money")
    pv_value: float = Field(default=0.0, ge=0, description="Personal Volume value")


class ProductCreate(ProductBase):
    image_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    webinar_link: Optional[str] = Field(default=None, max_length=500)
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
    price: Optional[Decimal] = Field(default=None, ge=0)
    pv_value: Optional[float] = Field(default=None, ge=0)
    image_url: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)
    webinar_link: Optional[str] = Field(default=None, max_length=500)
    is_collection: Optional[bool] = Field(default=None)
    collection_items: Optional[List[Dict[str, Any]]] = Field(default=None)


class ProductPublic(ProductBase):
    id: uuid.UUID = Field(...)
    image_url: Optional[str] = Field(default=None)
    is_active: bool = Field(...)
    created_at: datetime = Field(...)
    model_config = ConfigDict(from_attributes=True)


class UserProductInteractionBase(BaseModel):
    interaction_type: InteractionType = Field(...)
    additional_info: Optional[Dict[str, Any]] = Field(default=None)


class UserProductInteractionCreate(UserProductInteractionBase):
    pv_awarded: float = Field(default=0.0, ge=0, description="PV points awarded for this interaction")
    product_id: Optional[uuid.UUID] = Field(default=None)
    user_id: uuid.UUID = Field(...)
    achievement_id: Optional[uuid.UUID] = Field(default=None)


class UserProductInteractionUpdate(BaseModel):
    interaction_type: Optional[InteractionType] = Field(default=None)
    pv_awarded: Optional[float] = Field(default=None, ge=0)
    additional_info: Optional[Dict[str, Any]] = Field(default=None)

    @field_validator('pv_awarded')
    def validate_points(cls, v):
        if v is not None and v < 0:
            raise ValueError('PV awarded cannot be negative')
        return v


class UserProductInteractionPublic(UserProductInteractionBase):
    id: uuid.UUID = Field(...)
    interaction_date: datetime = Field(...)
    user_id: uuid.UUID = Field(...)
    product_id: Optional[uuid.UUID] = Field(default=None)
    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    cash_amount: Decimal = Field(..., ge=0, max_digits=12, decimal_places=2)
    pv_amount: Decimal = Field(..., ge=0, max_digits=12, decimal_places=2)
    type: TransactionType = Field(...)
    additional_info: Optional[Dict[str, Any]] = Field(default=None, description="Additional transaction metadata")


class TransactionCreate(TransactionBase):
    product_id: Optional[uuid.UUID] = Field(default=None)
    status: TransactionStatus = Field(...)
    achievement_id: Optional[uuid.UUID] = Field(default=None)
    user_id: uuid.UUID = Field(...)




class TransactionUpdate(BaseModel):
    cash_amount: Decimal = Field(default=None)
    pv_amount: Optional[float] = Field(default=None, ge=0)
    type: Optional[TransactionType] = Field(default=None)
    status: Optional[TransactionStatus] = Field(default=None)
    additional_info: Optional[Dict[str, Any]] = Field(default=None)


class TransactionPublic(TransactionBase):
    id: uuid.UUID = Field(...)
    created_at: datetime = Field(...)
    user_id: uuid.UUID = Field(...)
    product_id: Optional[uuid.UUID] = Field(default=None)
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


class FavoriteProduct(BaseModel):
    product_id: uuid.UUID = Field(...)
    added_at: datetime = Field(default_factory=datetime.now)


class FavoriteList(BaseModel):
    products: List[FavoriteProduct] = Field(default_factory=list)
    count: int = Field(0)


class BalanceHistory(BaseModel):
    date: datetime
    cash_balance: Decimal
    pv_balance: float
    transaction_id: uuid.UUID


class PurchaseResponse(BaseModel):
    message: str
    pv_earned: float
    new_pv_balance: float
    new_cash_balance: Decimal
    transaction_id: uuid.UUID


class UserBalanceResponse(BaseModel):
    cash_balance: Decimal = Field(..., description="Current cash balance")
    pv_balance: float = Field(..., description="Current PV balance")
    history: List[BalanceHistory] = Field(default_factory=list)