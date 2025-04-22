from enum import Enum

from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.types.localization_types import CurrencyType

class WalletType(str, Enum):
    BONUS = "bonus"
    GIFT = "gift"





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