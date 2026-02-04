from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from database import models, schemas

# Define the router
router = APIRouter(
    prefix="/bins",
    tags=["bins"],  # This groups them in the Swagger UI (/docs)
)


@router.get("/")
def get_bins(id: int, db: Session = Depends(get_db)):
    bins = db.query(models.Bin).filter(models.Bin.home_id == id).all()
    return {"bins": bins}


@router.get("/options")
def get_options(id: int):
    # Port of your ~/server/utils/python getBinOptions
    options = get_bin_options(id)
    return {"options": options}


@router.post("/{position}")
def upsert_bin(id: int, position: int, data: schemas.BinCreate, db: Session = Depends(get_db)):
    existing_bin = db.query(models.Bin).filter(
        and_(models.Bin.home_id == id, models.Bin.position == position)
    ).first()

    if existing_bin:
        existing_bin.name = data.humanName
        existing_bin.council_name = data.option
    else:
        new_bin = models.Bin(
            name=data.humanName,
            council_name=data.option,
            position=position,
            home_id=id
        )
        db.add(new_bin)
    db.commit()
    return {"status": "success"}


@router.post("/{position}/move")
def move_bin(id: int, position: int, direction: str = Body(..., embed=True), db: Session = Depends(get_db)):
    target_pos = position + 1 if direction == 'forwards' else position - 1

    from_bin = db.query(models.Bin).filter(and_(models.Bin.home_id == id, models.Bin.position == position)).first()
    to_bin = db.query(models.Bin).filter(and_(models.Bin.home_id == id, models.Bin.position == target_pos)).first()

    if not from_bin:
        raise HTTPException(status_code=400, detail="Invalid swap")

    # Temp position to avoid unique constraint clash
    from_bin.position = 999999
    db.flush()

    if to_bin:
        to_bin.position = position

    from_bin.position = target_pos
    db.commit()
    return {"status": "moved"}