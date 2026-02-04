from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from database import models, schemas

# Define the router
router = APIRouter(
    prefix="/home/{id}/schedules",
    tags=["schedules"],  # This groups them in the Swagger UI (/docs)
)


@router.get("/schedule")
def get_home_schedule(id: int, db: Session = Depends(get_db)):
    # This replaces that large .reduce() logic in Nuxt
    # SQLAlchemy's joinedload is much cleaner for this
    schedules = db.query(models.Schedule).filter(models.Schedule.home_id == id).all()

    results = []
    for s in schedules:
        # Build your nested structure here or use a specific Pydantic schema
        results.append({
            "schedule": s,
            "bins": s.bins,  # via relationship
            "next_date": None  # Calculate logic here
        })
    return {"schedules": results}


@router.post("/bin-day-replacement")
def create_replacement(id: int, data: dict, db: Session = Depends(get_db)):
    replacement = models.BinDayReplacement(
        replace=data['replace'],
        replace_with=data['with'],
        home_id=id
    )
    db.add(replacement)
    db.commit()
    refresh_all_schedules(id)  # Your ported utility
    return {"status": "created"}


@router.post("/schedule/{schedule_id}/recalculate")
def recalculate(id: int, schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(models.Schedule).filter(models.Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404)
    calculate_schedule(schedule)
    return {"status": "recalculated"}