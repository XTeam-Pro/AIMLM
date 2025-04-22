import re
from decimal import Decimal

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, Field
from typing import Optional
import uuid
from datetime import datetime

from app.schemas.types.common_types import MLMRankType
from app.schemas.types.localization_types import CountryEnum, CurrencyType

from app.schemas.types.user_types import UserRole, UserStatus, WalletType
from app.schemas.mlm import  UserMLMInput

class WalletBase(BaseModel):
    currency: CurrencyType = Field(...,)
    balance: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    is_active: bool = Field(default=True, description="Whether a wallet is active or not")
    type: WalletType = Field(default=WalletType.BONUS)
    @field_validator("balance")
    def validate_balance_positive(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Balance cannot be negative")
        return v



class WalletCreate(WalletBase):
    user_id: uuid.UUID = Field(..., )


class WalletUpdate(BaseModel):
    balance: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    is_active: bool | None = Field(default=None)

    @field_validator("balance")
    def validate_balance_if_provided(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("Balance cannot be negative")
        return v


class WalletPublic(WalletBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class UserUpdateMe(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = Field(default=None, max_length=255)

    @field_validator('email')
    def validate_email_rfc(cls, v):
        try:
            result = validate_email(v, check_deliverability=False)
            if v.lower() != "admin@example.com":
                blocked_domains = {'tempmail.com', 'example.com'}
                domain = v.split('@')[-1]
                if domain in blocked_domains:
                    raise ValueError('Disposable emails are not allowed')
            return result.normalized
        except EmailNotValidError as e:
            raise ValueError(str(e))


class UserBase(BaseModel):
    email: str | EmailStr
    username: str
    phone: str
    full_name: str
    country: CountryEnum = None
    @field_validator('email')
    def validate_email_rfc(cls, v):
        try:
            result = validate_email(v, check_deliverability=False)
            if v.lower() != "admin@example.com":
                blocked_domains = {'tempmail.com', 'example.com'}
                domain = v.split('@')[-1]
                if domain in blocked_domains:
                    raise ValueError('Disposable emails are not allowed')
            return result.normalized
        except EmailNotValidError as e:
            raise ValueError(str(e))

    model_config = ConfigDict(from_attributes=True)


class TestSponsorCreate(UserBase):
    email: EmailStr = Field(examples=["sponsor@google.com"])
    username: str = Field(max_length=100)
    phone: str = Field(max_length=20)
    full_name: str = Field(max_length=255)
    password: str = Field(min_length=8)
    rank: MLMRankType = Field(default=MLMRankType.NEWBIE)
    country: CountryEnum = None
    role: UserRole = Field(default=UserRole.DISTRIBUTOR)
    registration_date: datetime = Field(default=lambda: datetime.now())
    address: str
    postcode: str

    @field_validator('password')
    def validate_password_complexity(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserRegister(UserBase):
    password: str
    address: str = Field(examples=["Nevsky Prospekt, Saint Petersburg"])
    referral_code: Optional[str] = Field(default=None, max_length=12)
    postcode: str
    role: UserRole = Field(default=UserRole.CLIENT)
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    rank: MLMRankType | None = Field(default=MLMRankType.NEWBIE)

    @field_validator('address')
    def validate_address(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r'^[\w\s\-,.#]+$', v):
            raise ValueError("Address contains invalid characters.")
        if len(v.split(',')) < 2:
            raise ValueError("Address should include at least street and city separated by comma")
        return v.title()

    @field_validator('postcode')
    def validate_postcode(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r'^[A-Z0-9\- ]{3,12}$', v):
            raise ValueError("Postcode must contain only letters, numbers, spaces or hyphens")
        return v

    @field_validator('password')
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

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserRegister):
    pass

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = Field(default=UserRole.CLIENT)
    status: Optional[UserStatus] = Field(default=UserStatus.ACTIVE)
    country: Optional[CountryEnum] = None
    rank: Optional[MLMRankType] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('email')
    def validate_email_rfc(cls, v):
        from email_validator import validate_email, EmailNotValidError
        try:
            result = validate_email(v, check_deliverability=False)
            blocked_domains = {'tempmail.com', 'example.com'}
            domain = v.split('@')[-1]
            if domain in blocked_domains:
                raise ValueError('Disposable emails are not allowed')
            return result.normalized
        except EmailNotValidError as e:
            raise ValueError(str(e))

    @field_validator('phone')
    def validate_phone(cls, v):
        if not v.startswith('+'):
            raise ValueError('Phone must start with +')
        if len(v) < 10:
            raise ValueError('Phone too short')
        return v

class UserPublic(UserBase):
    id: uuid.UUID
    address: str
    postcode: str
    role: UserRole
    rank: MLMRankType | None
    status: UserStatus
    country: Optional[CountryEnum] = None
    referral_code: Optional[str] = Field(max_length=12)
    registration_date: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True, extra="forbid")

class UserWithMLM(BaseModel):
    user: UserPublic
    mlm: Optional[UserMLMInput] = None


class UsersPublic(BaseModel):
    data: list[UserWithMLM]
    count: int


class CreateRequest(BaseModel):
    user: UserCreate | UserPublic
    mlm: UserMLMInput
