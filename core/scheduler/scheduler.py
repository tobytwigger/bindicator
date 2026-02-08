import datetime
from typing import List, Dict, Optional
from core.database import models
from core.database.database import SessionLocal
from core.database.repositories import ScheduleRepository, BinRepository, BinDayReplacementRepository

class BinCollectionExplorer:
    def __init__(self, db: Optional[SessionLocal] = None):
        self._calculate_up_to_date = datetime.datetime.now().date() + datetime.timedelta(days=730)
        self._bin_date_cache: Dict[datetime.date, List[int]] = {} # List of bin IDs, keyed by the date they go out
        self._bin_obj_cache: Dict[int, models.Bin] = {}
        self._replacements_cache: Dict[datetime.date, datetime.date] = {}  # replace -> replace_with
        self._db = db
        self._load_bins()
        self._load_replacements()
        self._load_bin_collections()

    def clear_cache(self):
        self._bin_date_cache = {}
        self._bin_obj_cache = {}
        self._replacements_cache = {}

        self._load_bins()
        self._load_replacements()
        self._load_bin_collections()

    def _load_bins(self):
        self._bin_obj_cache = {}

        db = SessionLocal() if self._db is None else self._db

        bin_repo = BinRepository(db)
        for bin in bin_repo.get_all():
            self._bin_obj_cache[bin.id] = bin

        if self._db is None:
            db.close()

    def _load_bin_collections(self):
        db = SessionLocal() if self._db is None else self._db

        schedule_repo = ScheduleRepository(db)

        for schedule in schedule_repo.get_all_active():
            if schedule.bin_id not in self._bin_obj_cache:
                print("Bin not in object cache but is in schedule!")
                continue
            # Set the scheduled bin dates based on this.
            # Start at the start of the schedule
            current_date = schedule.start.date()
            # We want to iterate through from current_date, to either 1 year in the future or the end date
            end_date = self._calculate_up_to_date if schedule.end is None else min(schedule.end.date(), self._calculate_up_to_date)
            while current_date <= end_date:
                # Sometimes, current_date has a bin replacement. If this is the case, this is the date we care for
                temp_current_date = current_date if current_date not in self._replacements_cache else self._replacements_cache[current_date]
                if temp_current_date >= datetime.date.today():
                    if temp_current_date not in self._bin_date_cache:
                        self._bin_date_cache[temp_current_date] = []

                    self._bin_date_cache[temp_current_date].append(self._bin_obj_cache[schedule.bin_id].id)

                current_date += datetime.timedelta(weeks=schedule.repeat_weeks)

        # Sort the bin_date_cache by key
        self._bin_date_cache = dict(sorted(self._bin_date_cache.items()))

        if self._db is None:
            db.close()

    def _load_replacements(self):
        """Load bin day replacements from database into cache."""
        db = SessionLocal() if self._db is None else self._db

        replacement_repo = BinDayReplacementRepository(db)
        replacements = replacement_repo.get_all()  # Get all replacements

        for replacement in replacements:
            self._replacements_cache[replacement.replace.date()] = replacement.replace_with.date()

        if self._db is None:
            db.close()


    def get_bins_due_out_on(self, date: datetime.date) -> List[models.Bin]:
        if date in self._bin_date_cache:
            return [self._bin_obj_cache[bin_id] for bin_id in self._bin_date_cache[date]]

        return []

    def get_bin_by_id(self, bin_id: int) -> models.Bin | None:
        bin = self._bin_obj_cache.get(bin_id)
        if bin is not None:
            return bin

        return None

    def get_bin_by_position(self, position: int) -> models.Bin | None:
        bin = next((b for b in self._bin_obj_cache.values() if b.position == position), None)
        if bin is not None:
            return bin

        return None

    def get_collection_date_after(self, date: datetime.date, bin_id: int | None = None) -> Optional[datetime.date]:
        # Iterate through the keys until we find one larger than date
        for d, bin_ids in self._bin_date_cache.items():
            if bin_id is not None and bin_id not in bin_ids:
                continue
            if d > date:
                return d


        return None

    def get_collection_date_before(self, date: datetime.date, bin_id: int | None = None) -> Optional[datetime.date]:
        # Iterate through the keys until we find one larger than date
        for d in sorted(self._bin_date_cache.keys(), reverse=True):
            bin_ids = self._bin_date_cache[d]

            if bin_id is not None and bin_id not in bin_ids:
                continue

            if d < date:
                return d

        return None

    def get_calendar(self, start_date: datetime.date, end_date: datetime.date) -> List[Dict]:
        """
        Get calendar data for a date range.
        Returns a list of dates with their associated bins.

        Args:
            start_date: Start date of the range
            end_date: End date of the range

        Returns:
            List of dicts with 'date' (ISO string) and 'bins' (list of bin dicts)
        """
        result = []

        for date_key in sorted(self._bin_date_cache.keys()):
            # Only include dates within the requested range
            if date_key < start_date or date_key > end_date:
                continue

            # Get unique bins for this date
            unique_bins = {}
            for bin_id in self._bin_date_cache[date_key]:
                if bin_id in self._bin_obj_cache:
                    bin_obj = self._bin_obj_cache[bin_id]
                    unique_bins[bin_id] = {
                        'id': bin_obj.id,
                        'name': bin_obj.name,
                        'colour': bin_obj.colour
                    }

            if unique_bins:  # Only include dates that have bins
                result.append({
                    'date': date_key.isoformat(),
                    'bins': list(unique_bins.values())
                })

        return result


