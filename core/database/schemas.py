# Schemas validate API calls

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal
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


class BinPutOutBase(BaseModel):
    bin_id: int
    date_put_out_at: datetime

class BinPutOutCreate(BinPutOutBase):
    pass

class BinPutOut(BinPutOutBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class Settings(BaseModel):
    timeout: int = Field(default=120, ge=10, le=3600)
    put_out_day_before: bool = Field(default=False)
    put_out_time: str = Field(default="17:00")
    collection_time: str = Field(default="09:00")



class SettingsEdit(BaseModel):
    timeout: Optional[int] = Field(None, ge=10, le=3600)
    put_out_day_before: Optional[bool] = None
    put_out_time: Optional[str] = None
    collection_time: Optional[str] = Field(default="09:00")


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
    status: Literal['missed', 'taken_out', 'put_out_early', 'collected', 'due_out', 'not_yet_due']
    put_out_date: Optional[str] = None  # ISO date format YYYY-MM-DD, only present if taken_out, put_out_early, or collected
    put_out_id: Optional[int] = None  # ID of the put-out record, only present if taken_out, put_out_early, or collected

class CalendarDate(BaseModel):
    date: str  # ISO date format YYYY-MM-DD
    bins: list[CalendarBin]
