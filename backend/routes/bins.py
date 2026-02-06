from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.database.database import get_db
from core.database.schemas import Bin as BinSchema, BinCreate, BinEdit
from backend.utils.pagination import PaginationResponse
from core.database.repositories import BinRepository, PaginationOutOfRange

router = APIRouter(
    prefix="/bins",
    tags=["bins"],
)

def get_bin_repo(db: Session = Depends(get_db)) -> BinRepository:
    return BinRepository(db)

@router.get("/", response_model=PaginationResponse[BinSchema])
def get_bins(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    repo: BinRepository = Depends(get_bin_repo)
):
    """
    Get a paginated list of bins.
    """
    try:
        bins, total = repo.paginate(page, per_page)
    except PaginationOutOfRange:
        raise HTTPException(status_code=400, detail="Page out of range")
    return PaginationResponse[BinSchema](
        items=bins,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/{bin_id}", response_model=BinSchema)
def get_bin(bin_id: int, repo: BinRepository = Depends(get_bin_repo)):
    """
    Get a bin by its ID.
    """
    bin_obj = repo.get_by_id(bin_id)
    if not bin_obj:
        raise HTTPException(status_code=404, detail="Bin not found")
    return bin_obj

@router.post("/", response_model=BinSchema)
def create_bin(bin: BinCreate, repo: BinRepository = Depends(get_bin_repo)):
    """
    Create a new bin.
    """
    return repo.create(bin)

@router.post("/{bin_id}/move-earlier", response_model=BinSchema)
def move_bin_earlier(bin_id: int, repo: BinRepository = Depends(get_bin_repo)):
    """
    Move a bin earlier in the order.
    """
    bin_obj = repo.move_bin_earlier(bin_id)
    if not bin_obj:
        raise HTTPException(status_code=400, detail="Cannot move bin earlier")
    return bin_obj

@router.post("/{bin_id}/move-later", response_model=BinSchema)
def move_bin_later(bin_id: int, repo: BinRepository = Depends(get_bin_repo)):
    """
    Move a bin later in the order.
    """
    bin_obj = repo.move_bin_later(bin_id)
    if not bin_obj:
        raise HTTPException(status_code=400, detail="Cannot move bin later")
    return bin_obj

@router.post("/{bin_id}/set-position", response_model=BinSchema)
def set_bin_position(bin_id: int, position: int = Query(..., ge=1), repo: BinRepository = Depends(get_bin_repo)):
    """
    Set the position of a bin.
    """
    bin_obj = repo.set_bin_position(bin_id, position)
    if not bin_obj:
        raise HTTPException(status_code=400, detail="Cannot set bin position")
    return bin_obj

@router.patch("/{bin_id}", response_model=BinSchema)
def edit_bin(bin_id: int, bin_edit: BinEdit, repo: BinRepository = Depends(get_bin_repo)):
    """
    Edit a bin's name and colour.
    """
    bin_obj = repo.edit_bin(bin_id, bin_edit.name, bin_edit.colour)
    if not bin_obj:
        raise HTTPException(status_code=404, detail="Bin not found")
    return bin_obj

@router.delete("/{bin_id}", response_model=dict)
def delete_bin(bin_id: int, repo: BinRepository = Depends(get_bin_repo)):
    """
    Delete a bin by its ID.
    """
    success = repo.delete_bin(bin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bin not found")
    return {"status": "success"}
