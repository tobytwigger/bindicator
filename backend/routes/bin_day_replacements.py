from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from core.database.database import get_db
from core.database import schemas
from core.database.repositories import BinDayReplacementRepository, PaginationOutOfRange
from backend.utils.pagination import PaginationResponse
from backend.utils.mqtt_publisher import publish_database_update

router = APIRouter(
    prefix="/bin_day_replacements",
    tags=["Bin Day Replacements"],
)

def get_bin_day_replacement_repo(db: Session = Depends(get_db)) -> BinDayReplacementRepository:
    return BinDayReplacementRepository(db)

@router.get("/", response_model=PaginationResponse[schemas.BinDayReplacement])
def list_bin_day_replacements(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    repo: BinDayReplacementRepository = Depends(get_bin_day_replacement_repo),
):
    try:
        items, total = repo.paginate(page, per_page)
    except PaginationOutOfRange:
        raise HTTPException(status_code=400, detail="Page out of range")
    return PaginationResponse[
        schemas.BinDayReplacement
    ](
        items=items,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/{replacement_id}", response_model=schemas.BinDayReplacement)
def get_bin_day_replacement(replacement_id: int, repo: BinDayReplacementRepository = Depends(get_bin_day_replacement_repo)):
    replacement = repo.get_by_id(replacement_id)
    if not replacement:
        raise HTTPException(status_code=404, detail="BinDayReplacement not found")
    return replacement

@router.post("/", response_model=schemas.BinDayReplacement)
def create_bin_day_replacement(replacement: schemas.BinDayReplacementCreate, repo: BinDayReplacementRepository = Depends(get_bin_day_replacement_repo)):
    created = repo.create(replacement)
    publish_database_update()
    return created

@router.patch("/{replacement_id}", response_model=schemas.BinDayReplacement)
def edit_bin_day_replacement(replacement_id: int, replacement_edit: dict, repo: BinDayReplacementRepository = Depends(get_bin_day_replacement_repo)):
    updated = repo.edit(replacement_id, replacement_edit)
    if not updated:
        raise HTTPException(status_code=404, detail="BinDayReplacement not found")
    publish_database_update()
    return updated

@router.delete("/{replacement_id}", status_code=204)
def delete_bin_day_replacement(replacement_id: int, repo: BinDayReplacementRepository = Depends(get_bin_day_replacement_repo)):
    deleted = repo.delete(replacement_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="BinDayReplacement not found")
    publish_database_update()
    return Response(status_code=204)
