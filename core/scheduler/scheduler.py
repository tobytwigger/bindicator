import datetime
from typing import List

from core.database.repositories import ScheduleRepository, BinRepository


class Scheduler:
    """
    Handle scheduling of bins in the future

    This class gets all the input info, e.g. from the database, and can create a future schedule.
    - Get next time single bin is out
    - Get next bin dates with bins
    - Get next bin dates with bins after X date
    - Get next time single bin is out after X date
    """

    def __init__(self, db, calculate_up_to_date: datetime.date | None = None):
        if calculate_up_to_date is None:
            calculate_up_to_date = datetime.datetime.now().date() + datetime.timedelta(days=365)

        self._calculate_up_to_date = calculate_up_to_date
        self._db = db
        self._bin_date_cache: dict[str, List[datetime.date]] = {}
        self._initialise_values()

    def _initialise_values(self, start_from=None):
        # Get the schedules, where end date is null or
        bin_repo = BinRepository(self._db)

        for bin in bin_repo.get_all():
            self._bin_date_cache[str(bin.id)] = []

        schedule_repo = ScheduleRepository(self._db)

        for schedule in schedule_repo.get_all_active():
            # Set the scheduled bin dates based on this.
            # Start at the start of the schedule
            current_date = max(schedule.start.date(), start_from) if start_from is not None else schedule.start.date()
            # We want to iterate through from current_date, to either 1 year in the future or the end date
            end_date = self._calculate_up_to_date if schedule.end is None else min(schedule.end.date(), self._calculate_up_to_date)
            while current_date <= end_date:
                self._bin_date_cache[str(schedule.bin_id)].append(current_date)
                current_date += datetime.timedelta(weeks=schedule.repeat_weeks)

    def get_date_bin_next_due_out(self, bin_id: int, after: datetime.date | None =None):
        """
        Get the dates that a single bin is due out, after the 'after' date or now if given
        :param bin_id: The ID of the bin
        :param after: The date after which to find the next due date. If None, defaults to now.
        :return:
        """
        if after is None:
            after = datetime.datetime.now().date()

        for date in self._bin_date_cache[str(bin_id)]:
            if date > after:
                return date

        return None

    def get_all_dates_bin_due_out(self, bin_id: int, after: datetime.date | None =None) -> list[datetime.date]:
        """
        Get all the dates that a single bin is due out, after the 'after' date or now if given

        :param bin_id:
        :param after:
        :return:
        """
        if after is None:
            after = datetime.datetime.now().date()

        if after > self._calculate_up_to_date:
            start_from = self._calculate_up_to_date
            self._calculate_up_to_date = after
            self._initialise_values(start_from)

        return [b for b in self._bin_date_cache[str(bin_id)] if b >= after]

    def get_collection_dates(self, after : datetime.date | None = None, until : datetime.date | None = None):
        """
        Get the dates of future collections, after the 'after' date or now if given, and before the 'until' date (if given)
        """