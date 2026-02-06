from sqlalchemy.orm import Session
from typing import Optional
from core.database import models, schemas
from sqlalchemy import func

class PaginationOutOfRange(Exception):
    pass

class BinRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[schemas.Bin]:
        bins = self.db.query(models.Bin).order_by(models.Bin.position).all()
        return [schemas.Bin.model_validate(b) for b in bins]

    def paginate(self, page: int, per_page: int) -> tuple[list[schemas.Bin], int]:
        query = self.db.query(models.Bin).order_by(models.Bin.position)
        total = query.count()
        if page > 1 and (page - 1) * per_page >= total:
            raise PaginationOutOfRange()
        bins = query.offset((page - 1) * per_page).limit(per_page).all()
        return [schemas.Bin.model_validate(b) for b in bins], total

    def get_by_id(self, bin_id: int) -> Optional[schemas.Bin]:
        db_bin = self.db.query(models.Bin).filter(models.Bin.id == bin_id).first()
        if not db_bin:
            return None
        return schemas.Bin.model_validate(db_bin)

    def create(self, bin_data: schemas.BinCreate) -> schemas.Bin:
        # Find the next available position
        max_position = self.db.query(func.max(models.Bin.position)).scalar()
        next_position = (max_position or 0) + 1
        db_bin = models.Bin(
            name=bin_data.name,
            colour=bin_data.colour,
            position=next_position
        )
        self.db.add(db_bin)
        self.db.commit()
        self.reorder_positions()
        self.db.refresh(db_bin)
        return schemas.Bin.model_validate(db_bin)

    def move_bin_earlier(self, bin_id: int) -> Optional[schemas.Bin]:
        db_bin = self.db.query(models.Bin).filter(models.Bin.id == bin_id).first()
        if not db_bin or db_bin.position == 1:
            return None
        prev_bin = self.db.query(models.Bin).filter(models.Bin.position == db_bin.position - 1).first()
        if prev_bin:
            prev_bin.position, db_bin.position = db_bin.position, prev_bin.position
            self.db.commit()
            self.reorder_positions()
            self.db.refresh(db_bin)
            self.db.refresh(prev_bin)
        return schemas.Bin.model_validate(db_bin)

    def move_bin_later(self, bin_id: int) -> Optional[schemas.Bin]:
        db_bin = self.db.query(models.Bin).filter(models.Bin.id == bin_id).first()
        max_position = self.db.query(func.max(models.Bin.position)).scalar()
        if not db_bin or db_bin.position == max_position:
            return None
        next_bin = self.db.query(models.Bin).filter(models.Bin.position == db_bin.position + 1).first()
        if next_bin:
            next_bin.position, db_bin.position = db_bin.position, next_bin.position
            self.db.commit()
            self.reorder_positions()
            self.db.refresh(db_bin)
            self.db.refresh(next_bin)
        return schemas.Bin.model_validate(db_bin)

    def set_bin_position(self, bin_id: int, new_position: int) -> Optional[schemas.Bin]:
        db_bin = self.db.query(models.Bin).filter(models.Bin.id == bin_id).first()
        if not db_bin:
            return None
        bins = self.db.query(models.Bin).order_by(models.Bin.position, models.Bin.updated_at).all()
        bins.remove(db_bin)
        bins.insert(new_position - 1, db_bin)
        for idx, bin_obj in enumerate(bins):
            bin_obj.position = idx + 1
        db_bin.updated_at = func.now()
        self.db.commit()
        self.db.refresh(db_bin)
        return schemas.Bin.model_validate(db_bin)

    def edit_bin(self, bin_id: int, name: Optional[str], colour: Optional[str]) -> Optional[schemas.Bin]:
        db_bin = self.db.query(models.Bin).filter(models.Bin.id == bin_id).first()
        if not db_bin:
            return None
        if name is not None:
            db_bin.name = name
        if colour is not None:
            db_bin.colour = colour
        db_bin.updated_at = func.now()
        self.db.commit()
        self.db.refresh(db_bin)
        return schemas.Bin.model_validate(db_bin)

    def delete_bin(self, bin_id: int) -> bool:
        db_bin = self.db.query(models.Bin).filter(models.Bin.id == bin_id).first()
        if not db_bin:
            return False
        self.db.delete(db_bin)
        self.db.commit()
        self.reorder_positions()
        return True

    def reorder_positions(self) -> None:
        bins = self.db.query(models.Bin).order_by(models.Bin.position).all()
        for idx, bin_obj in enumerate(bins):
            bin_obj.position = idx + 1
        self.db.commit()
