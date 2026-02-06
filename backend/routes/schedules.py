from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.database.database import get_db
from core.database import schemas
from core.database.repositories import ScheduleRepository, PaginationOutOfRange

# Define the router
router = APIRouter(
    prefix="/schedules",
    tags=["schedules"],  # This groups them in the Swagger UI (/docs)
)


@router.get("/", response_model=dict)
def list_schedules(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    repo = ScheduleRepository(db)
    try:
        items, total = repo.paginate(page, per_page)
    except PaginationOutOfRange:
        raise HTTPException(status_code=400, detail="Page out of range")
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.get("/{schedule_id}", response_model=schemas.Schedule)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    repo = ScheduleRepository(db)
    schedule = repo.get_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.post("/", response_model=schemas.Schedule)
def create_schedule(schedule: schemas.ScheduleCreate, db: Session = Depends(get_db)):
    repo = ScheduleRepository(db)
    try:
        created = repo.create(schedule)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return created


@router.patch("/{schedule_id}", response_model=schemas.Schedule)
def edit_schedule(schedule_id: int, schedule_edit: schemas.ScheduleEdit, db: Session = Depends(get_db)):
    repo = ScheduleRepository(db)
    updated = repo.edit(schedule_id, schedule_edit)
    if not updated:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return updated
