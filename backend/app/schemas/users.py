import re
from decimal import Decimal

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, Field
from typing import Optional
import uuid
from datetime import datetime

from app.schemas.types.localization_types import CurrencyType

from app.schemas.types.user_types import  WalletType
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
    name: Optional[str] = Field(default=None, max_length=100)
    surname: Optional[str] = Field(default=None, max_length=100)
    patronymic: Optional[str] = Field(default=None, max_length=100)
    email: Optional[EmailStr] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    country: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)

    @field_validator('email')
    def validate_email_rfc(cls, v):
        if v is None:
            return v
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

    @field_validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        # Basic international phone validation (E.164)
        if not re.match(r"^\+?[1-9]\d{1,14}$", v):
            raise ValueError("Phone number must be in international format (e.g. +1234567890)")
        return v



class UserBase(BaseModel):
    email: EmailStr | str = Field(examples=["sponsor@google.com"])
    name: str = Field(max_length=100)
    surname: str = Field(max_length=100)
    patronymic: str = Field(max_length=100)
    phone: str = Field(max_length=20)
    country: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)

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

    @field_validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        # Basic international phone validation (E.164)
        if not re.match(r"^\+?[1-9]\d{1,14}$", v):
            raise ValueError("Phone number must be in international format (e.g. +1234567890)")
        return v


class TestSponsorCreate(UserBase):
    email: EmailStr | str = Field(examples=["sponsor@google.com"])
    password: str = Field(min_length=8)
    role: str = Field(default="DISTRIBUTOR")
    referral_code: Optional[str] = Field(default=None, max_length=8)

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
    referral_code: Optional[str] = Field(default=None, max_length=8)
    gender: str = Field(default="MALE")

    @field_validator('password')
    def validate_password_complexity(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserRegister):
    pass

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(default=None, max_length=100)
    surname: Optional[str] = Field(default=None, max_length=100)
    patronymic: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    country: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)
    role: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('email')
    def validate_email_rfc(cls, v):
        if v is None:
            return v
        try:
            result = validate_email(v, check_deliverability=False)
            blocked_domains = {'tempmail.com', 'example.com'}
            domain = v.split('@')[-1]
            if domain in blocked_domains:
                raise ValueError('Disposable emails are not allowed')
            return result.normalized
        except EmailNotValidError as e:
            raise ValueError(str(e))

    def validate_phone(cls, v):
        if v is None:
            return v
        # Basic international phone validation (E.164)
        if not re.match(r"^\+?[1-9]\d{1,14}$", v):
            raise ValueError("Phone number must be in international format (e.g. +1234567890)")
        return v




class UserPublic(UserBase):
    id: uuid.UUID
    role: str
    status: str
    referral_code: Optional[str] = Field(max_length=16)
    sponsor_id: Optional[uuid.UUID] = None
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
