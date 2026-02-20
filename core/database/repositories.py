from sqlalchemy.orm import Session
from typing import Optional, Any, List
from core.database import models, schemas
from sqlalchemy import func
from datetime import datetime
from sqlalchemy import or_
import os


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

    def get_by_position(self, bin_position: int) -> Optional[schemas.Bin]:
        db_bin = self.db.query(models.Bin).filter(models.Bin.position == bin_position).first()
        if not db_bin:
            return None
        return schemas.Bin.model_validate(db_bin)

    def count(self) -> int:
        return self.db.query(func.count(models.Bin.id)).scalar()


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

    def get_all(self) -> List[schemas.BinDayReplacement]:
        query = self.db.query(models.BinDayReplacement).order_by(models.BinDayReplacement.id)

        return [schemas.BinDayReplacement.model_validate(r) for r in query.all()]

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


class BinPutOutRepository:
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

    def paginate(self, page: int, per_page: int) -> tuple[list[schemas.BinPutOut], int]:
        query = self.db.query(models.BinPutOut).order_by(models.BinPutOut.date_put_out_at.desc(), models.BinPutOut.id.desc())
        total = query.count()
        if page > 1 and (page - 1) * per_page >= total:
            raise PaginationOutOfRange()
        put_outs = query.offset((page - 1) * per_page).limit(per_page).all()
        return [schemas.BinPutOut.model_validate(p) for p in put_outs], total

    def get_by_id(self, put_out_id: int) -> Optional[schemas.BinPutOut]:
        db_put_out = self.db.query(models.BinPutOut).filter(models.BinPutOut.id == put_out_id).first()
        if not db_put_out:
            return None
        return schemas.BinPutOut.model_validate(db_put_out)

    def get_all(self) -> List[schemas.BinPutOut]:
        """Get all bin put out records."""
        query = self.db.query(models.BinPutOut).order_by(models.BinPutOut.date_put_out_at.desc(), models.BinPutOut.id.desc())
        return [schemas.BinPutOut.model_validate(p) for p in query.all()]

    def get_by_date(self, date) -> list[schemas.BinPutOut]:
        """Get all bins put out on a specific date (matches any time on that date)."""
        target_date = self._parse_datetime(date)
        if target_date:
            target_date = target_date.date() if hasattr(target_date, 'date') else target_date

        # Since date_put_out_at is now DateTime, we need to filter by date range
        from sqlalchemy import and_
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        db_put_outs = self.db.query(models.BinPutOut).filter(
            and_(
                models.BinPutOut.date_put_out_at >= start_of_day,
                models.BinPutOut.date_put_out_at <= end_of_day
            )
        ).order_by(models.BinPutOut.id).all()

        return [schemas.BinPutOut.model_validate(p) for p in db_put_outs]

    def create(self, put_out_data: schemas.BinPutOutCreate) -> schemas.BinPutOut:
        # Check bin exists
        bin = self.db.query(models.Bin).filter(models.Bin.id == put_out_data.bin_id).first()
        if not bin:
            raise ValueError("Bin not found")

        db_put_out = models.BinPutOut(
            bin_id=put_out_data.bin_id,
            date_put_out_at=self._parse_datetime(put_out_data.date_put_out_at)
        )
        self.db.add(db_put_out)
        self.db.commit()
        self.db.refresh(db_put_out)
        return schemas.BinPutOut.model_validate(db_put_out)

    def delete(self, put_out_id: int) -> bool:
        db_put_out = self.db.query(models.BinPutOut).filter(models.BinPutOut.id == put_out_id).first()
        if not db_put_out:
            return False
        self.db.delete(db_put_out)
        self.db.commit()
        return True



class SettingsRepository:
    SETTINGS_FILE_PATH = None  # Can be set by tests or will be loaded from env

    def __init__(self):
        """Initialize settings repository with JSON file backend."""
        # Get the settings file path from class attribute (for tests) or environment variable
        if self.SETTINGS_FILE_PATH is None:
            self.SETTINGS_FILE_PATH = os.getenv(
                "SETTINGS_FILE_PATH",
                os.path.expanduser("~/.config/bindicator/settings.json")
            )
        self._ensure_settings_directory()

    def _ensure_settings_directory(self):
        """Ensure the settings directory exists, raise clear error if it cannot be created."""
        import os

        directory = os.path.dirname(self.SETTINGS_FILE_PATH)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except PermissionError:
                raise PermissionError(
                    f"Cannot create settings directory '{directory}'. "
                    f"Please ensure the directory exists and has proper permissions."
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to create settings directory '{directory}': {e}"
                )

    def _load_settings_from_file(self) -> dict:
        """Load settings from JSON file, return defaults if file doesn't exist."""
        import json
        import os

        if not os.path.exists(self.SETTINGS_FILE_PATH):
            # Return defaults if file doesn't exist
            return {field: model_field.default
                    for field, model_field in schemas.Settings.model_fields.items()}

        try:
            with open(self.SETTINGS_FILE_PATH, 'r') as f:
                content = f.read()
                # Handle empty files
                if not content:
                    return {field: model_field.default
                           for field, model_field in schemas.Settings.model_fields.items()}
                settings_data = json.loads(content)

            # Ensure all fields are set, using defaults if missing
            defaults = {field: model_field.default
                       for field, model_field in schemas.Settings.model_fields.items()}
            defaults.update(settings_data)
            return defaults
        except json.JSONDecodeError as e:
            raise ValueError(f"Settings file '{self.SETTINGS_FILE_PATH}' contains invalid JSON: {e}")
        except PermissionError:
            raise PermissionError(f"Cannot read settings file '{self.SETTINGS_FILE_PATH}'. Check file permissions.")
        except Exception as e:
            raise RuntimeError(f"Failed to load settings from '{self.SETTINGS_FILE_PATH}': {e}")

    def _save_settings_to_file(self, settings_dict: dict):
        """Save settings to JSON file with file locking to prevent concurrent write issues."""
        import json
        import fcntl
        import os

        try:
            # Open file for writing, create if doesn't exist
            with open(self.SETTINGS_FILE_PATH, 'w') as f:
                # Acquire exclusive lock
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(settings_dict, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    # Release lock
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except PermissionError:
            raise PermissionError(f"Cannot write to settings file '{self.SETTINGS_FILE_PATH}'. Check file permissions.")
        except Exception as e:
            raise RuntimeError(f"Failed to save settings to '{self.SETTINGS_FILE_PATH}': {e}")

    def get_by_key(self, key: str) -> Any:
        """Get a specific setting by key."""
        settings_dict = self._load_settings_from_file()

        if key in settings_dict:
            return settings_dict[key]

        raise KeyError(f"Setting '{key}' not found")

    def get_all(self) -> schemas.Settings:
        """Get all settings."""
        settings_dict = self._load_settings_from_file()
        return schemas.Settings.model_validate(settings_dict)

    def create_or_update(self, settings_data: schemas.SettingsEdit) -> schemas.Settings:
        """Create or update settings."""
        # Load current settings
        settings_dict = self._load_settings_from_file()

        # Update only the fields that were set
        for field in settings_data.model_fields_set:
            if field in schemas.Settings.model_fields:
                settings_dict[field] = getattr(settings_data, field)

        # Save to file
        self._save_settings_to_file(settings_dict)

        return schemas.Settings.model_validate(settings_dict)

    def delete_by_key(self, key: str):
        """Delete a setting by key (reset to default)."""
        settings_dict = self._load_settings_from_file()

        if key in schemas.Settings.model_fields:
            # Reset to default as defined in schema
            default_value = schemas.Settings.model_fields[key].default
            settings_dict[key] = default_value

            self._save_settings_to_file(settings_dict)
        else:
            raise KeyError(f"Setting '{key}' not found")