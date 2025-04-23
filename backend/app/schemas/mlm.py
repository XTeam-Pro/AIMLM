from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlmodel import Field

from app.schemas.types.common_types import ContractType, MLMRankType
from app.schemas.types.gamification_types import BonusType, ClubType


# Models:
class UserMLMBase(BaseModel):
    contract_type: ContractType = Field(default=ContractType.BASIC)
    current_rank: MLMRankType = Field(default=MLMRankType.NEWBIE)
    current_club: ClubType = Field(default=ClubType.PREMIER)
    personal_volume: Decimal = Field(default=Decimal(0))
    group_volume: Decimal = Field(default=Decimal(0))
    accumulated_volume: Decimal = Field(default=Decimal(0))
    binary_volume_left: Decimal = Field(default=Decimal(0))
    binary_volume_right: Decimal = Field(default=Decimal(0))
    mentor_id: Optional[uuid.UUID] = None
    placement_sponsor_id: Optional[uuid.UUID] = Field(default=None)

class UserMLMInput(UserMLMBase):
    model_config = ConfigDict(from_attributes=True)

class UserMLMCreate(UserMLMInput):
    user_id: uuid.UUID = Field(...,)

class UserMLMUpdate(BaseModel):
    contract_type: Optional[ContractType] = None
    current_rank: Optional[MLMRankType] = None
    current_club: Optional[ClubType] = None
    personal_volume: Optional[Decimal] = None
    group_volume: Optional[Decimal] = None
    accumulated_volume: Optional[Decimal] = None
    binary_volume_left: Optional[Decimal] = None
    binary_volume_right: Optional[Decimal] = None
    placement_sponsor_id: uuid.UUID | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class BusinessCenterBase(BaseModel):
    center_number: int
    left_volume: Decimal = Field(default=Decimal(0))
    right_volume: Decimal = Field(default=Decimal(0))

class BusinessCenterCreate(BusinessCenterBase):
    owner_id: uuid.UUID

class BusinessCenterUpdate(BusinessCenterBase):
    owner_id: Optional[uuid.UUID] = None


class UserMLMPublic(UserMLMBase):
    id: uuid.UUID
    user_id: uuid.UUID
    business_centers: List["BusinessCenterPublic"] = []
    bonuses: List["BonusPublic"] = []
    activities: List["UserActivityPublic"] = []
    ranks_history: List["UserRankHistoryPublic"] = []

    model_config = ConfigDict(from_attributes=True)


class BusinessCenterPublic(BusinessCenterBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    owner: UserMLMPublic

    class Config:
        orm_mode = True

class UserActivityBase(BaseModel):
    activity_type: str
    period_start: datetime
    period_end: datetime
    personal_volume: Decimal
    is_confirmed: bool = Field(default=False)
    confirmed_at: Optional[datetime] = None

class UserActivityCreate(UserActivityBase):
    user_id: uuid.UUID

class UserActivityUpdate(UserActivityBase):
    user_id: Optional[uuid.UUID] = None

class UserActivityPublic(UserActivityBase):
    id: uuid.UUID
    user_id: uuid.UUID
    user: UserMLMPublic

    model_config = ConfigDict(from_attributes=True)

class BonusBase(BaseModel):
    bonus_type: BonusType
    amount: Decimal
    currency: str
    calculation_period: str
    is_paid: bool = Field(default=False)
    paid_at: Optional[datetime] = None

class BonusCreate(BonusBase):
    user_id: uuid.UUID

class BonusUpdate(BonusBase):
    user_id: Optional[uuid.UUID] = None

class BonusPublic(BonusBase):
    id: uuid.UUID
    user_id: uuid.UUID
    user: UserMLMPublic

    model_config = ConfigDict(from_attributes=True)

class UserRankHistoryBase(BaseModel):
    rank: str
    club: str
    achieved_at: datetime
    qualification_period: str
    group_volume: Decimal
    personal_volume: Decimal

class UserRankHistoryCreate(UserRankHistoryBase):
    user_id: uuid.UUID

class UserRankHistoryUpdate(UserRankHistoryBase):
    user_id: Optional[uuid.UUID] = None

class UserRankHistoryPublic(UserRankHistoryBase):
    id: uuid.UUID
    user_id: uuid.UUID
    user: UserMLMPublic

    model_config = ConfigDict(from_attributes=True)

class UserHierarchyBase(BaseModel):
    ancestor_id: uuid.UUID
    descendant_id: uuid.UUID
    level: int

class UserHierarchyCreate(UserHierarchyBase):
    pass

class UserHierarchyUpdate(UserHierarchyBase):
    pass

class UserHierarchyPublic(UserHierarchyBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class GenerationBonusMatrixBase(BaseModel):
    rank: str
    generation: int
    bonus_percentage: Decimal


class GenerationBonusMatrixCreate(GenerationBonusMatrixBase):
    pass

class GenerationBonusMatrixList(BaseModel):
    rows: list[GenerationBonusMatrixCreate]

class GenerationBonusMatrixUpdate(GenerationBonusMatrixBase):
    pass

class GenerationBonusMatrixPublic(GenerationBonusMatrixBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)