# Schemas validate API calls

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

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
