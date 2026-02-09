import datetime
from typing import List, Dict, Optional, Tuple, Literal
from core.database import models
from core.database.database import SessionLocal
from core.database.repositories import ScheduleRepository, BinRepository, BinDayReplacementRepository, BinPutOutRepository, SettingsRepository

class BinCollectionExplorer:
    def __init__(self, db: Optional[SessionLocal] = None):
        self._calculate_up_to_date = datetime.datetime.now().date() + datetime.timedelta(days=730)
        self._bin_date_cache: Dict[datetime.date, List[int]] = {} # List of bin IDs, keyed by the date they go out
        self._bin_obj_cache: Dict[int, models.Bin] = {}
        self._bin_put_out_cache: Dict[Tuple[int, datetime.date], Tuple[datetime.datetime, int]] = {} # Maps (bin_id, collection_date) to (put_out_datetime, put_out_id)
        self._replacements_cache: Dict[datetime.date, datetime.date] = {}  # replace -> replace_with
        self._db = db
        self._settings = None  # Cache settings
        self._load_settings()
        self._load_bins()
        self._load_replacements()
        self._load_bin_collections()  # Must be loaded before put outs
        self._load_bin_put_out_dates()

    def clear_cache(self):
        self._bin_date_cache = {}
        self._bin_obj_cache = {}
        self._bin_put_out_cache = {}
        self._replacements_cache = {}
        self._settings = None

        self._load_settings()
        self._load_bins()
        self._load_replacements()
        self._load_bin_collections()
        self._load_bin_put_out_dates()

    def _load_settings(self):
        """Load settings from repository."""
        settings_repo = SettingsRepository()
        self._settings = settings_repo.get_all()

    def _load_bins(self):
        self._bin_obj_cache = {}

        db = SessionLocal() if self._db is None else self._db

        bin_repo = BinRepository(db)
        for bin in bin_repo.get_all():
            self._bin_obj_cache[bin.id] = bin

        if self._db is None:
            db.close()

    def _load_bin_put_out_dates(self):
        """Load bin put out records from database into cache.

        Cache structure: {(bin_id, collection_date): put_out_datetime}
        This maps each bin's collection date to when it was actually put out.
        """
        self._bin_put_out_cache = {}

        db = SessionLocal() if self._db is None else self._db

        bin_put_out_repo = BinPutOutRepository(db)

        # Load all bin put outs
        put_outs = bin_put_out_repo.get_all()

        for put_out in put_outs:
            # Extract date from datetime
            put_out_date = put_out.date_put_out_at.date() if hasattr(put_out.date_put_out_at, 'date') else put_out.date_put_out_at

            # Find the collection date that this put-out corresponds to
            # Look for the next collection date after the put-out date
            collection_date = self._find_collection_date_for_put_out(
                put_out.bin_id,
                put_out_date
            )

            if collection_date:
                # Store the put out datetime (not just date) keyed by (bin_id, collection_date)
                cache_key = (put_out.bin_id, collection_date)
                self._bin_put_out_cache[cache_key] = (put_out.date_put_out_at, put_out.id)

        if self._db is None:
            db.close()

    def _find_collection_date_for_put_out(self, bin_id: int, put_out_date: datetime.date) -> Optional[datetime.date]:
        """Find the collection date that a put-out record corresponds to.

        Returns the collection date that comes on or after the put-out date.
        This handles cases where bins are put out early.
        """
        for collection_date, bin_ids in self._bin_date_cache.items():
            if bin_id in bin_ids and collection_date >= put_out_date:
                return collection_date
        return None

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
        # If the date is today, then look at the 'collection time' setting to know if return today or not

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

    def get_bin_status_for_date(
        self,
        bin_id: int,
        collection_date: datetime.date
    ) -> Tuple[Literal['missed', 'taken_out', 'put_out_early', 'collected', 'due_out', 'not_yet_due'], Optional[datetime.datetime], Optional[int]]:
        """
        Calculate the status of a bin for a given collection date.

        Args:
            bin_id: ID of the bin
            collection_date: Date the bin is scheduled for collection

        Returns:
            Tuple of (status, put_out_datetime, put_out_id) where:
            - status: 'missed', 'taken_out', 'put_out_early', 'collected', 'due_out', or 'not_yet_due'
            - put_out_datetime: Datetime the bin was put out (if applicable), None otherwise
            - put_out_id: ID of the put-out record (if applicable), None otherwise

        Status logic:
        - missed: was not taken out and the collection time has passed
        - taken_out: has been taken out after it was due, still before collection time
        - put_out_early: has been taken out before it was due, still before collection time
        - collected: was put out (on time or early) and collection time has passed
        - due_out: has not been taken out, but is past the put_out_day_before and put_out_time
        - not_yet_due: before the put_out_day_before and put_out_time
        """
        now = datetime.datetime.now()
        current_date = now.date()
        current_time = now.time()

        # Check if bin was put out for this collection date
        cache_key = (bin_id, collection_date)
        put_out_data = self._bin_put_out_cache.get(cache_key)
        put_out_datetime = put_out_data[0] if put_out_data else None
        put_out_id = put_out_data[1] if put_out_data else None
        print(put_out_data)
        # Parse settings times
        collection_time = datetime.time.fromisoformat(self._settings.collection_time)
        put_out_time = datetime.time.fromisoformat(self._settings.put_out_time)

        # Calculate when the bin is due to be put out
        if self._settings.put_out_day_before:
            put_out_due_date = collection_date - datetime.timedelta(days=1)
        else:
            put_out_due_date = collection_date

        # Combine date and time for comparisons
        collection_datetime = datetime.datetime.combine(collection_date, collection_time)
        put_out_due_datetime = datetime.datetime.combine(put_out_due_date, put_out_time)

        # Determine status
        if put_out_datetime:
            # Bin was put out
            if now >= collection_datetime:
                # Collection time has passed - bin has been collected
                return ('collected', put_out_datetime, put_out_id)
            else:
                # Still before collection time
                if put_out_datetime < put_out_due_datetime:
                    return ('put_out_early', put_out_datetime, put_out_id)
                else:
                    return ('taken_out', put_out_datetime, put_out_id)
        else:
            # Bin was not put out
            if now >= collection_datetime:
                # Collection time has passed and bin was not put out
                return ('missed', None, None)
            elif now >= put_out_due_datetime:
                # Past the time when bin should be put out, but before collection
                return ('due_out', None, None)
            else:
                # Not yet time to put out the bin
                return ('not_yet_due', None, None)

    def get_calendar(self, start_date: datetime.date, end_date: datetime.date) -> List[Dict]:
        """
        Get calendar data for a date range.
        Returns a list of dates with their associated bins, including status information.

        Args:
            start_date: Start date of the range
            end_date: End date of the range

        Returns:
            List of dicts with 'date' (ISO string) and 'bins' (list of bin dicts)
            Each bin dict includes: id, name, colour, status, put_out_date (if applicable), and put_out_id (if applicable)
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

                    # Calculate status for this bin
                    status, put_out_datetime, put_out_id = self.get_bin_status_for_date(bin_id, date_key)

                    bin_dict = {
                        'id': bin_obj.id,
                        'name': bin_obj.name,
                        'colour': bin_obj.colour,
                        'status': status
                    }

                    # Only include put_out_date and put_out_id if the bin was actually put out
                    if put_out_datetime:
                        bin_dict['put_out_date'] = put_out_datetime.date().isoformat()
                        bin_dict['put_out_id'] = put_out_id

                    unique_bins[bin_id] = bin_dict

            if unique_bins:  # Only include dates that have bins
                result.append({
                    'date': date_key.isoformat(),
                    'bins': list(unique_bins.values())
                })

        return result

    def get_bins_requiring_action(self) -> Dict:
        """
        Get bins that require action (display on hardware).

        Returns bins with actionable statuses for today or tomorrow, prioritizing today.
        If no actionable bins exist, returns information about the next collection.

        Returns:
            Dict with:
            - bins_to_display: List of dicts with 'bin' (Bin object), 'status', 'put_out_datetime'
            - display_date: The collection date being shown (today, tomorrow, or future)
            - next_collection_date: Date of next collection (for right arrow navigation)
            - previous_collection_date: Date of previous collection (for left arrow, minimum today)
        """
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)

        # Actionable statuses are those where the bin needs attention or action
        actionable_statuses = {'due_out', 'not_yet_due', 'taken_out', 'put_out_early'}

        # Check bins for today
        bins_today = self.get_bins_due_out_on(today)
        actionable_today = []

        for bin_obj in bins_today:
            status, put_out_datetime, put_out_id = self.get_bin_status_for_date(bin_obj.id, today)
            if status in actionable_statuses:
                actionable_today.append({
                    'bin': bin_obj,
                    'status': status,
                    'put_out_datetime': put_out_datetime,
                    'put_out_id': put_out_id
                })

        # If we have actionable bins today, return those
        if actionable_today:
            return {
                'bins_to_display': actionable_today,
                'display_date': today,
                'next_collection_date': self.get_collection_date_after(today),
                'previous_collection_date': max(today, self.get_collection_date_before(today) or today)
            }

        # Check bins for tomorrow
        bins_tomorrow = self.get_bins_due_out_on(tomorrow)
        actionable_tomorrow = []

        for bin_obj in bins_tomorrow:
            status, put_out_datetime, put_out_id = self.get_bin_status_for_date(bin_obj.id, tomorrow)
            if status in actionable_statuses:
                actionable_tomorrow.append({
                    'bin': bin_obj,
                    'status': status,
                    'put_out_datetime': put_out_datetime,
                    'put_out_id': put_out_id
                })

        # If we have actionable bins tomorrow, return those
        if actionable_tomorrow:
            return {
                'bins_to_display': actionable_tomorrow,
                'display_date': tomorrow,
                'next_collection_date': self.get_collection_date_after(tomorrow),
                'previous_collection_date': today  # Can't go before today
            }

        # No actionable bins - return next collection info
        next_collection = self.get_collection_date_after(today)
        return {
            'bins_to_display': [],
            'display_date': today,
            'next_collection_date': next_collection,
            'previous_collection_date': today  # Can't go before today
        }


