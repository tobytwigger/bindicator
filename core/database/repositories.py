from sqlalchemy.orm import Session
from typing import Optional, Any
from core.database import models, schemas
from sqlalchemy import func
from datetime import datetime
from sqlalchemy import or_


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

class ScheduleRepository:
    def __init__(self, db: Session):
        self.db = db

    def _parse_datetime(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        return value

    def paginate(self, page: int, per_page: int) -> tuple[list[schemas.Schedule], int]:
        query = self.db.query(models.Schedule).order_by(models.Schedule.id)
        total = query.count()
        if page > 1 and (page - 1) * per_page >= total:
            raise PaginationOutOfRange()
        schedules = query.offset((page - 1) * per_page).limit(per_page).all()
        return [schemas.Schedule.model_validate(s) for s in schedules], total

    def get_by_id(self, schedule_id: int) -> Optional[schemas.Schedule]:
        db_schedule = self.db.query(models.Schedule).filter(models.Schedule.id == schedule_id).first()
        if not db_schedule:
            return None
        return schemas.Schedule.model_validate(db_schedule)

    def create(self, schedule_data: schemas.ScheduleCreate) -> schemas.Schedule:
        # Check bin exists
        bin = self.db.query(models.Bin).filter(models.Bin.id == schedule_data.bin_id).first()
        if not bin:
            raise ValueError("Bin not found")
        db_schedule = models.Schedule(
            start=self._parse_datetime(schedule_data.start),
            end=self._parse_datetime(schedule_data.end) if schedule_data.end else None,
            repeat_weeks=schedule_data.repeat_weeks,
            bin_id=schedule_data.bin_id
        )
        self.db.add(db_schedule)
        self.db.commit()
        self.db.refresh(db_schedule)
        return schemas.Schedule.model_validate(db_schedule)

    def edit(self, schedule_id: int, schedule_edit: schemas.ScheduleEdit) -> Optional[schemas.Schedule]:
        db_schedule = self.db.query(models.Schedule).filter(models.Schedule.id == schedule_id).first()
        if not db_schedule:
            return None
        if schedule_edit.start is not None:
            db_schedule.start = self._parse_datetime(schedule_edit.start)
        if schedule_edit.end is not None:
            db_schedule.end = self._parse_datetime(schedule_edit.end)
        if schedule_edit.repeat_weeks is not None:
            db_schedule.repeat_weeks = schedule_edit.repeat_weeks
        if schedule_edit.bin_id is not None:
            bin = self.db.query(models.Bin).filter(models.Bin.id == schedule_edit.bin_id).first()
            if not bin:
                raise ValueError("Bin not found")
            db_schedule.bin_id = schedule_edit.bin_id
        self.db.commit()
        self.db.refresh(db_schedule)
        return schemas.Schedule.model_validate(db_schedule)

    def delete(self, schedule_id: int) -> bool:
        db_schedule = self.db.query(models.Schedule).filter(models.Schedule.id == schedule_id).first()
        if not db_schedule:
            return False
        self.db.delete(db_schedule)
        self.db.commit()
        return True

    def get_all_active(self):
        # Get all schedules where end is in the future, or empty, and start is now or in the past
        db_schedules = self.db.query(models.Schedule).filter(
            or_(
                models.Schedule.end == None,
                models.Schedule.end >= func.now()
            )
        ).all()

        return [schemas.Schedule.model_validate(s) for s in db_schedules]

class BinDayReplacementRepository:
    def __init__(self, db: Session):
        self.db = db

    def _parse_datetime(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        return value

    def paginate(self, page: int, per_page: int) -> tuple[list[schemas.BinDayReplacement], int]:
        query = self.db.query(models.BinDayReplacement).order_by(models.BinDayReplacement.id)
        total = query.count()
        if page > 1 and (page - 1) * per_page >= total:
            raise PaginationOutOfRange()
        replacements = query.offset((page - 1) * per_page).limit(per_page).all()
        return [schemas.BinDayReplacement.model_validate(r) for r in replacements], total

    def get_by_id(self, replacement_id: int) -> Optional[schemas.BinDayReplacement]:
        db_replacement = self.db.query(models.BinDayReplacement).filter(models.BinDayReplacement.id == replacement_id).first()
        if not db_replacement:
            return None
        return schemas.BinDayReplacement.model_validate(db_replacement)

    def create(self, replacement_data: schemas.BinDayReplacementCreate) -> schemas.BinDayReplacement:
        db_replacement = models.BinDayReplacement(
            replace=replacement_data.replace,
            replace_with=replacement_data.replace_with
        )
        self.db.add(db_replacement)
        self.db.commit()
        self.db.refresh(db_replacement)
        return schemas.BinDayReplacement.model_validate(db_replacement)

    def edit(self, replacement_id: int, replacement_edit: dict) -> Optional[schemas.BinDayReplacement]:
        db_replacement = self.db.query(models.BinDayReplacement).filter(models.BinDayReplacement.id == replacement_id).first()
        if not db_replacement:
            return None
        if 'replace' in replacement_edit and replacement_edit['replace'] is not None:
            db_replacement.replace = self._parse_datetime(replacement_edit['replace'])
        if 'replace_with' in replacement_edit and replacement_edit['replace_with'] is not None:
            db_replacement.replace_with = self._parse_datetime(replacement_edit['replace_with'])
        self.db.commit()
        self.db.refresh(db_replacement)
        return schemas.BinDayReplacement.model_validate(db_replacement)

    def delete(self, replacement_id: int) -> bool:
        db_replacement = self.db.query(models.BinDayReplacement).filter(models.BinDayReplacement.id == replacement_id).first()
        if not db_replacement:
            return False
        self.db.delete(db_replacement)
        self.db.commit()
        return True

class SettingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_settings_row(self) -> models.Settings:
        settings = self.db.query(models.Settings).first()
        if not settings:
            settings = models.Settings()
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        # Ensure all fields are set, using defaults if missing
        for field, model_field in schemas.SettingsBase.model_fields.items():
            if getattr(settings, field, None) is None:
                setattr(settings, field, model_field.default)
        return settings

    def get_by_key(self, key: str) -> Any:
        db_settings = self.get_settings_row()

        if hasattr(db_settings, key):
            return getattr(db_settings, key)

        raise KeyError(f"Setting '{key}' not found")

    def get_all(self) -> schemas.SettingsBase:
        settings_row = self.get_settings_row()
        # Convert SQLAlchemy model to dict for Pydantic
        settings_dict = {field: getattr(settings_row, field) for field in schemas.SettingsBase.model_fields}
        return schemas.SettingsBase.model_validate(settings_dict)

    def create_or_update(self, settings_data: schemas.SettingsEdit) -> schemas.SettingsBase:
        db_settings = self.get_settings_row()

        for field in settings_data.model_fields_set:
            if hasattr(db_settings, field):
                setattr(db_settings, field, getattr(settings_data, field))

        self.db.commit()
        self.db.refresh(db_settings)

        # Convert SQLAlchemy model to dict for Pydantic
        settings_dict = {field: getattr(db_settings, field) for field in schemas.SettingsBase.model_fields}
        return schemas.SettingsBase.model_validate(settings_dict)

    def delete_by_key(self, key):
        db_settings = self.get_settings_row()

        if hasattr(db_settings, key):
            # Reset to default as defined in schema
            default_value = schemas.SettingsBase.model_fields[key].default
            setattr(db_settings, key, default_value)

            self.db.commit()
            self.db.refresh(db_settings)
        else:
            raise KeyError(f"Setting '{key}' not found")