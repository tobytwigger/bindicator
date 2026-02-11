from typing import List

from polars import DataFrame
from sqlalchemy.orm import Session
import polars as pl
import datetime

from core.database.database import SessionLocal
from core.database.repositories import ScheduleRepository, SettingsRepository, BinRepository, BinPutOutRepository, \
    BinDayReplacementRepository
from core.database.schemas import Schedule
from core.scheduler.schemas import BinCollection, BinCollectionStatus
from core.database import models, schemas

class BinCollectionDataCache:
    def __init__(self):
        self.settings: schemas.Settings | None = None
        self.bins: dict[int, schemas.Bin] = {}
        self.schedules: dict[int, Schedule] = {}
        self.bin_day_put_outs: dict[int, List[schemas.BinPutOut]] = {}
        self.bin_day_replacements: dict[datetime.date, schemas.BinDayReplacement] = {}

    def load_data(self):
        self.settings = SettingsRepository().get_all()  # Cache settings
        self.bins = self._load_bins()
        self.schedules = self._load_schedules()
        self.bin_day_put_outs = self._load_bin_day_put_outs()
        self.bin_day_replacements = self._load_bin_day_replacements()

        # self._load_replacements()
        # self._load_bin_collections()  # Must be loaded before put outs
        # self._load_bin_put_out_dates()

    def _load_bins(self) -> dict[int, schemas.Bin]:
        results = {}
        with SessionLocal() as db:
            bin_repo = BinRepository(db)
            # Create a cache of bin objects in a dict, keyed by bin id.

            for bin in bin_repo.get_all():
                results[bin.id] = schemas.Bin.model_validate(bin)

        return results

    def _load_schedules(self) -> dict[int, Schedule]:
        results = {}

        with SessionLocal() as db:

            schedule_repo = ScheduleRepository(db)

            for schedule in schedule_repo.get_all_active():
                results[schedule.id] = schemas.Schedule.model_validate(schedule)

        return results

    def _load_bin_day_put_outs(self) -> dict[int, List[schemas.BinPutOut]]:
        results: dict[int, List[schemas.BinPutOut]] = {}
        with SessionLocal() as db:

            put_out_repo = BinPutOutRepository(db)

            put_outs = put_out_repo.get_all()

            # Group put-outs by bin_id
            for put_out in put_outs:
                if put_out.bin_id not in results:
                    results[put_out.bin_id] = []
                results[put_out.bin_id].append(put_out)

            # Sort each bin's put-outs by date_put_out_at
            for bin_id in results:
                results[bin_id].sort(key=lambda x: x.date_put_out_at)

        return results

    def _load_bin_day_replacements(self) -> dict[datetime.date, schemas.BinDayReplacement]:
        results = {}

        with SessionLocal() as db:
            replacement_repo = BinDayReplacementRepository(db)

            for replacement in replacement_repo.get_all():
                results[replacement.replace.date()] = schemas.BinDayReplacement.model_validate(replacement)

        return results



class BinCollectionFactory:
    def __init__(self, data_source: BinCollectionDataCache = None):
        if data_source is None:
            data_source = BinCollectionDataCache()

        self._data = data_source

    def build_collections_dataframe(self) -> DataFrame:
        # Let's prepare the data first
        self._data.load_data()

        bin_collections: List[BinCollection] = []

        used_put_out_ids: set[int] = set()

        # Let's iterate through our schedules
        for schedule_id, schedule in self._data.schedules.items():
            bin = self._data.bins.get(schedule.bin_id, None)
            if bin is None:
                print(f"Bin {schedule.bin_id} not found for schedule: {str(schedule)}")
                continue

            end_date = schedule.end.date() if schedule.end is not None else datetime.date.today() + datetime.timedelta(days=365)

            current_date = schedule.start.date()

            while current_date <= end_date:
                # At this point, we can assume (unless told otherwise) a bin is being collected on `current_date`
                bin_collection_date = current_date

                # Let's see if we are told otherwise, by Bin Replacements
                if current_date in self._data.bin_day_replacements:
                    bin_collection_date = self._data.bin_day_replacements[current_date].replace_with.date()

                # The collection will happen on the day, at the time from settings
                collection_occurs_at_time = datetime.datetime.strptime(self._data.settings.collection_time, "%H:%M").time()
                collection_occurs_at = datetime.datetime.combine(bin_collection_date, collection_occurs_at_time)

                # It is due either on the day or the day before (if put_out_day_before is true), at the time from settings
                due_out_at_time = datetime.datetime.strptime(self._data.settings.put_out_time, "%H:%M").time()
                if self._data.settings.put_out_day_before:
                    due_out_at = datetime.datetime.combine(bin_collection_date - datetime.timedelta(days=1), due_out_at_time)
                else:
                    due_out_at = datetime.datetime.combine(bin_collection_date, due_out_at_time)

                # Find if this bin was taken out for this collection
                # We look for the earliest put-out that occurred after the previous collection
                # and before the current collection time
                bin_put_out = self._find_matching_put_out(
                    bin.id,
                    due_out_at,
                    collection_occurs_at,
                    used_put_out_ids # We pass this reference to hold the put outs still waiting
                )

                # Finally, with all this information, we can calculate a status!
                status = self._get_status(due_out_at, collection_occurs_at, bin_put_out)

                # We should probably start gathering this data together
                bin_collection = BinCollection.model_validate({
                    "bin_id": bin.id,
                    "bin_name": bin.name,
                    "bin_colour": bin.colour,
                    "bin_position": bin.position,
                    "due_out_at": due_out_at,
                    "collection_due_at": collection_occurs_at,
                    "taken_out_at": bin_put_out.date_put_out_at if bin_put_out else None,
                    "status": status,
                    "put_out_id": bin_put_out.id if bin_put_out else None
                })

                # We can append our new object to the list of collections
                bin_collections.append(bin_collection)

                # Finally, add another week to the current date and time to get ready for the next loop
                current_date += datetime.timedelta(weeks=schedule.repeat_weeks)

        # 2. Recreate the DataFrame
        return pl.from_dicts([
            {**bc.model_dump(), "status": bc.status.value}
            for bc in bin_collections
        ])

    def _find_matching_put_out(
        self,
        bin_id: int,
        due_out_at: datetime.datetime,
        collection_due_at: datetime.datetime,
        used_put_out_ids: set[int]
    ) -> schemas.BinPutOut | None:

        if bin_id not in self._data.bin_day_put_outs:
            return None

        # We need to consider a time window:
        # - Start: Some time before due_out_at (to allow for early put-outs)
        # - End: The collection time
        # Let's use 7 days before due_out_at as the earliest possible time
        window_start = due_out_at - datetime.timedelta(days=7)
        window_end = collection_due_at

        for put_out in self._data.bin_day_put_outs[bin_id]:
            if put_out.id in used_put_out_ids:
                continue  # This put-out has already been used for another collection

            if window_start <= put_out.date_put_out_at <= window_end:
                used_put_out_ids.add(put_out.id)  # Mark this put-out as used
                return put_out

        return None

    def _get_status(
        self,
        due_out_at: datetime.datetime,
        collection_due_at: datetime.datetime,
        taken_out_at: schemas.BinPutOut | None
    ) -> BinCollectionStatus:
        """
        Calculate the status of a bin collection based on timing.

        Args:
            due_out_at: When the bin is due to be put out
            collection_due_at: When the bin collection occurs
            taken_out_at: When the bin was actually put out (or None)

        Returns:
            The calculated BinCollectionStatus
        """
        now = datetime.datetime.now()

        # If collection has already happened
        if now >= collection_due_at:
            if taken_out_at:
                return BinCollectionStatus.COLLECTED
            else:
                return BinCollectionStatus.MISSED

        # Collection hasn't happened yet

        # If bin was put out
        if taken_out_at:
            # If bin was taken out earlier than it was due out
            if taken_out_at.date_put_out_at < due_out_at:
                return BinCollectionStatus.PUT_OUT_EARLY
            else: # It was just taken out on time
                return BinCollectionStatus.TAKEN_OUT

        # Bin hasn't been put out yet
        else:
            if now >= due_out_at:
                return BinCollectionStatus.DUE_OUT
            else:
                return BinCollectionStatus.NOT_YET_DUE



