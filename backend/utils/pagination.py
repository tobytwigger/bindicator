from typing import Any, TypeVar, List, Generic

from pydantic import BaseModel
from sqlalchemy.orm import Query


def paginate(query: Query, page: int = 1, per_page: int = 10) -> dict[str, Any]:
    total = query.order_by(None).count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page
    }


T = TypeVar("T")

class PaginationResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int