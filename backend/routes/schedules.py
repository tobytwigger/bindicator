from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from core.database.database import get_db
from core.database import schemas
from core.database.repositories import ScheduleRepository, PaginationOutOfRange
from backend.utils.pagination import PaginationResponse
from typing import List
from datetime import datetime
from core.scheduler.scheduler import BinCollectionExplorer
from backend.utils.mqtt_publisher import publish_database_update

# Define the router
router = APIRouter(
    prefix="/schedules",
    tags=["Schedules"],  # This groups them in the Swagger UI (/docs)
)

def get_schedule_repo(db: Session = Depends(get_db)) -> ScheduleRepository:
    return ScheduleRepository(db)

@router.get("/", response_model=PaginationResponse[schemas.Schedule])
def list_schedules(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    repo: ScheduleRepository = Depends(get_schedule_repo),
):
    """
    Get all schedules paginated.
    """
    try:
        items, total = repo.paginate(page, per_page)
    except PaginationOutOfRange:
        raise HTTPException(status_code=400, detail="Page out of range")
    return PaginationResponse[
        schemas.Schedule
    ](
        items=items,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get('/calendar', response_model=List[schemas.CalendarDate])
def load_calendar(
        start: str = Query(..., description="Start date (YYYY-MM-DD)"),
        end: str = Query(..., description="End date (YYYY-MM-DD)"),
        db: Session = Depends(get_db)
):
    """
    Get computed bin collection dates within a date range.
    Considers schedules and bin day replacements.
    """
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before or equal to end date")

    # Use BinCollectionExplorer to get calendar data
    explorer = BinCollectionExplorer(db=db)
    calendar_data = explorer.get_calendar(start_date, end_date)

    return calendar_data


@router.get("/{schedule_id}", response_model=schemas.Schedule)
def get_schedule(schedule_id: int, repo: ScheduleRepository = Depends(get_schedule_repo)):
    """
    Get a schedule by its ID.
    """
    schedule = repo.get_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.post("/", response_model=schemas.Schedule)
def create_schedule(schedule: schemas.ScheduleCreate, repo: ScheduleRepository = Depends(get_schedule_repo)):
    """
    Create a new schedule.
    """
    try:
        created = repo.create(schedule)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    publish_database_update()
    return created


@router.patch("/{schedule_id}", response_model=schemas.Schedule)
def edit_schedule(schedule_id: int, schedule_edit: schemas.ScheduleEdit, repo: ScheduleRepository = Depends(get_schedule_repo)):
    """
    Edit an existing schedule.
    """
    updated = repo.edit(schedule_id, schedule_edit)
    if not updated:
        raise HTTPException(status_code=404, detail="Schedule not found")
    publish_database_update()
    return updated


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, repo: ScheduleRepository = Depends(get_schedule_repo)):
    """
    Delete a schedule by its ID.
    """
    deleted = repo.delete(schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found")
    publish_database_update()
    return Response(status_code=204)

