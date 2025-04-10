from typing import Optional

from pydantic import BaseModel, ConfigDict
from app.schemas.types.localization_types import TimeZoneNames


# Models:
class TimeZoneBase(BaseModel):
    name: TimeZoneNames
    offset: str

class TimeZoneCreate(TimeZoneBase):
    pass

class TimeZoneUpdate(BaseModel):
    name: TimeZoneNames
    offset: Optional[str]

class TimeZonePublic(TimeZoneBase):
    model_config = ConfigDict(from_attributes=True)