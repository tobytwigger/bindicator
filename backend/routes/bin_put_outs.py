from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from core.database.database import get_db
from core.database.schemas import BinPutOut as BinPutOutSchema, BinPutOutCreate
from backend.utils.pagination import PaginationResponse
from core.database.repositories import BinPutOutRepository, PaginationOutOfRange
from backend.utils.mqtt_publisher import publish_database_update
from typing import List

router = APIRouter(
    prefix="/bin-put-outs",
    tags=["Bin Put Outs"],
)

def get_bin_put_out_repo(db: Session = Depends(get_db)) -> BinPutOutRepository:
    return BinPutOutRepository(db)

@router.get("/", response_model=PaginationResponse[BinPutOutSchema])
def get_bin_put_outs(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    repo: BinPutOutRepository = Depends(get_bin_put_out_repo)
):
    """
    Get a paginated list of bin put out records.
    """
    try:
        put_outs, total = repo.paginate(page, per_page)
    except PaginationOutOfRange:
        raise HTTPException(status_code=400, detail="Page out of range")
    return PaginationResponse[BinPutOutSchema](
        items=put_outs,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/by-date", response_model=List[BinPutOutSchema])
def get_bin_put_outs_by_date(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    repo: BinPutOutRepository = Depends(get_bin_put_out_repo)
):
    """
    Get all bins put out on a specific date.
    """
    try:
        put_outs = repo.get_by_date(date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    return put_outs

@router.get("/{put_out_id}", response_model=BinPutOutSchema)
def get_bin_put_out(put_out_id: int, repo: BinPutOutRepository = Depends(get_bin_put_out_repo)):
    """
    Get a bin put out record by its ID.
    """
    put_out = repo.get_by_id(put_out_id)
    if not put_out:
        raise HTTPException(status_code=404, detail="Bin put out record not found")
    return put_out

@router.post("/", response_model=BinPutOutSchema)
def create_bin_put_out(put_out: BinPutOutCreate, repo: BinPutOutRepository = Depends(get_bin_put_out_repo)):
    """
    Create a new bin put out record.
    """
    try:
        result = repo.create(put_out)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    publish_database_update()
    return result

@router.delete("/{put_out_id}", status_code=204)
def delete_bin_put_out(put_out_id: int, repo: BinPutOutRepository = Depends(get_bin_put_out_repo)):
    """
    Delete a bin put out record by its ID.
    """
    success = repo.delete(put_out_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bin put out record not found")
    publish_database_update()
    return Response(status_code=204)
