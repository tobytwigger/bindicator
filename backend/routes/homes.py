from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from database import models, schemas

# Define the router
router = APIRouter(
    prefix="/home/{id}/bins",
    tags=["bins"],  # This groups them in the Swagger UI (/docs)
)


@router.get("/", response_model=dict)
def get_homes(db: Session = Depends(get_db)):
    homes = db.query(models.Home).all()
    return {"homes": homes}


@router.post("/", response_model=schemas.Home)
def create_home(home_data: schemas.HomeCreate, db: Session = Depends(get_db)):
    # Check for existing active home logic
    active_exists = db.query(models.Home).filter(models.Home.active == True).first()

    new_home = models.Home(
        name=home_data.name,
        council=home_data.council,
        council_data=home_data.council_data,
        active=not bool(active_exists),
        timeout=home_data.timeout,
        put_out_day_before=home_data.put_out_day_before
    )
    db.add(new_home)
    db.commit()
    db.refresh(new_home)
    return new_home


@router.get("/{id}", response_model=dict)
def get_home_detail(id: int, db: Session = Depends(get_db)):
    home = db.query(models.Home).filter(models.Home.id == id).first()
    if not home:
        raise HTTPException(status_code=404, detail="Home not found")

    has_schedule = db.query(models.Schedule).filter(models.Schedule.home_id == id).count() > 0
    has_bins = db.query(models.Bin).filter(models.Bin.home_id == id).count() > 0

    return {
        "home": home,
        "has_schedule": has_schedule,
        "has_bins": has_bins
    }


@router.post("/{id}/activate")
def activate_home(id: int, db: Session = Depends(get_db)):
    # Set target home to active
    db.query(models.Home).filter(models.Home.id == id).update({"active": True})
    # Set all others to inactive
    db.query(models.Home).filter(models.Home.id != id).update({"active": False})
    db.commit()
    return {"message": "Home activated"}


@router.delete("/{id}")
def delete_home(id: int, db: Session = Depends(get_db)):
    db.query(models.Bin).filter(models.Bin.home_id == id).delete()
    db.query(models.Home).filter(models.Home.id == id).delete()
    db.commit()
    return status.HTTP_204_NO_CONTENT