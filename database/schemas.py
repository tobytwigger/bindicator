# Schemas validate API calls

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

class HomeBase(BaseModel):
    name: str
    council: Optional[str] = None
    council_data: Optional[Any] = None
    active: bool = False
    timeout: int = 180
    put_out_day_before: bool = False

class HomeCreate(HomeBase):
    pass

class Home(HomeBase):
    id: int
    class Config:
        from_attributes = True # In Pydantic v2 (replaces orm_mode=True)