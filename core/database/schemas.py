# Schemas validate API calls

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from pydantic import Field

# class HomeBase(BaseModel):
#     name: str
#     council: Optional[str] = None
#     council_data: Optional[Any] = None
#     active: bool = False
#     timeout: int = 180
#     put_out_day_before: bool = False
#

#
# class Home(HomeBase):
#     id: int
#     class Config:
#         from_attributes = True # In Pydantic v2 (replaces orm_mode=True)


class BinBase(BaseModel):
    name: str
    colour: Optional[str] = None

class BinCreate(BinBase):
    pass

class BinEdit(BaseModel):
    name: Optional[str] = None
    colour: Optional[str] = None
    model_config = {
        "from_attributes": True,
    }

class Bin(BinBase):
    id: int
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ScheduleBase(BaseModel):
    start: datetime
    end: Optional[datetime] = None
    bin_id: int
    repeat_weeks: int

class ScheduleCreate(ScheduleBase):
    pass


class ScheduleEdit(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    bin_id: Optional[int] = None
    repeat_weeks: Optional[int] = None
    model_config = {
        "from_attributes": True,
    }


class Schedule(ScheduleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }

class BinDayReplacementBase(BaseModel):
    replace: datetime
    replace_with: datetime

class BinDayReplacementCreate(BinDayReplacementBase):
    pass

class BinDayReplacement(BinDayReplacementBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class SettingsBase(BaseModel):
    timeout: int = Field(default=120, ge=1, le=3600)
class SettingsEdit(BaseModel):
    timeout: Optional[int] = Field(None, ge=1, le=3600)


    model_config = {
        "from_attributes": True,
        "extra": "forbid",
    }

    # @field_validator("app_name")
    # @classmethod
    # def name_must_be_capitalized(cls, v: str):
    #     if v and not v[0].isupper():
    #         raise ValueError("App name must start with a capital letter")
    #     return v

# Calendar endpoint schemas
class CalendarBin(BaseModel):
    id: int
    name: str
    colour: Optional[str] = None

class CalendarDate(BaseModel):
    date: str  # ISO date format YYYY-MM-DD
    bins: list[CalendarBin]
