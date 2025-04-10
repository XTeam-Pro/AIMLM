import re
from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, Field
from typing import Optional
import uuid
from datetime import datetime
from decimal import Decimal

from app.schemas.types.localization_types import TimeZoneNames
from app.schemas.types.gamification_types import RankType
from app.schemas.types.user_types import UserRole, UserStatus


class UserUpdateMe(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = Field(default=None, max_length=255)

# Models:
class UserBase(BaseModel):
    email: str | EmailStr
    username: str
    phone: str
    full_name: str
    mentees_count: int

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


class UserRegister(UserBase):
    hashed_password: str
    address: str
    postcode: str
    role: UserRole
    status: UserStatus
    cash_balance: float
    pv_balance: float

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
    status: UserStatus
    role: UserRole
    timezone: TimeZoneNames
    mentees_count: int
    mentor_id: Optional[uuid.UUID]
    rank_id: RankType
    team_id: Optional[uuid.UUID]
    total_personal_sales: Decimal
    total_team_sales: Decimal


class UserUpdate(BaseModel):
    email: Optional[EmailStr]
    phone: Optional[str]
    full_name: Optional[str]
    role: Optional[UserRole]
    status: UserStatus
    timezone: TimeZoneNames
    mentor_id: Optional[uuid.UUID]
    mentees_count: int
    cash_balance: Optional[float]
    pv_balance: Optional[float]
    rank_id: RankType
    team_id: Optional[uuid.UUID]
    total_personal_sales: Decimal
    total_team_sales: Decimal


class UserPublic(UserBase):
    id: uuid.UUID
    role: UserRole
    status: UserStatus
    cash_balance: Decimal
    pv_balance: Decimal
    registration_date: datetime
    timezone: TimeZoneNames
    mentees_count: int
    rank_id: RankType
    team_id: Optional[uuid.UUID]
    total_personal_sales: Decimal
    total_team_sales: Decimal
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UsersPublic(BaseModel):
    data: list[UserPublic]
    count: int