from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, constr
from app.schemas.types.localization_types import TimeZoneNames, CountryEnum


class TimeZoneBase(BaseModel):
    country: CountryEnum = Field(max_length=100, default=CountryEnum.RUSSIA)
    name: TimeZoneNames = Field(max_length=100, default=TimeZoneNames.MSK)
    offset: constr(max_length=6, pattern=r"^[+-]\d{2}:\d{2}$") = Field(default="+03:00")  # Corrected here


class TimeZoneCreate(TimeZoneBase):
    pass


class TimeZoneUpdate(BaseModel):
    name: TimeZoneNames
    offset: Optional[str]


class TimeZonePublic(TimeZoneBase):
    model_config = ConfigDict(from_attributes=True)

class TimeZonesCreateRequest(BaseModel):
    timezones: list[TimeZoneCreate]