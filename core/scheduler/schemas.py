import datetime
from enum import Enum
from core.database import schemas
from pydantic import BaseModel


class BinCollectionStatus(Enum):
    MISSED='missed'
    TAKEN_OUT='taken_out'
    PUT_OUT_EARLY='put_out_early'
    COLLECTED='collected'
    DUE_OUT='due_out'
    NOT_YET_DUE='not_yet_due'


class BinCollection(BaseModel):
    bin_id: int
    bin_name: str
    bin_colour: str | None
    bin_position: int
    due_out_at: datetime.datetime
    collection_due_at: datetime.datetime
    taken_out_at: datetime.datetime | None
    put_out_id: int | None
    status: BinCollectionStatus

    model_config = {
        "from_attributes": True,
    }