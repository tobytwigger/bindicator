import datetime
from typing import List, Dict, Optional, Tuple, Literal

from polars import DataFrame
from sqlalchemy.orm import Session

from core.scheduler.schemas import BinCollection, BinCollectionStatus
from core.database import models
from core.database.repositories import ScheduleRepository, BinRepository, BinDayReplacementRepository, BinPutOutRepository, SettingsRepository
from core.scheduler.factory import BinCollectionFactory


class BinCollectionExplorer:
    def __init__(self, factory_or_database: BinCollectionFactory | Session):
        if isinstance(factory_or_database, BinCollectionFactory):
            factory = factory_or_database
        elif isinstance(factory_or_database, Session):
            factory = BinCollectionFactory(factory_or_database)
        else:
            raise ValueError("Invalid data source type. Must be BinCollectionDataCache or Session.")

        self._factory = factory
        self.data: DataFrame | None = None
        self.load_data()

    def load_data(self):
        self.data = None
        self.data = self._factory.build_collections_dataframe()




    # def get_bins_due_out_on(self, date: datetime.date) -> List[models.Bin]:
    #     if date in self._bin_date_cache:
    #         return [self._bin_obj_cache[bin_id] for bin_id in self._bin_date_cache[date]]
    #
    #     return []
    #
    # def get_bin_by_id(self, bin_id: int) -> models.Bin | None:
    #     bin = self._bin_obj_cache.get(bin_id)
    #     if bin is not None:
    #         return bin
    #
    #     return None
    #
    # def get_bin_by_position(self, position: int) -> models.Bin | None:
    #     bin = next((b for b in self._bin_obj_cache.values() if b.position == position), None)
    #     if bin is not None:
    #         return bin
    #
    #     return None
    #
    # def get_collection_date_after(self, date: datetime.date, bin_id: int | None = None) -> Optional[datetime.date]:
    #     # If the date is today, then look at the 'collection time' setting to know if return today or not
    #
    #     # Iterate through the keys until we find one larger than date
    #     for d, bin_ids in self._bin_date_cache.items():
    #         if bin_id is not None and bin_id not in bin_ids:
    #             continue
    #         if d > date:
    #             return d
    #
    #
    #     return None
    #
    # def get_collection_date_before(self, date: datetime.date, bin_id: int | None = None) -> Optional[datetime.date]:
    #     # Iterate through the keys until we find one larger than date
    #     for d in sorted(self._bin_date_cache.keys(), reverse=True):
    #         bin_ids = self._bin_date_cache[d]
    #
    #         if bin_id is not None and bin_id not in bin_ids:
    #             continue
    #
    #         if d < date:
    #             return d
    #
    #     return None

    def get_items_as_dict(self, start_date: datetime.date, end_date: datetime.date) -> List[BinCollection]:
        # Filter for the collection date being between the start and end date
        start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
        end_datetime = datetime.datetime.combine(end_date, datetime.time.max)

        filtered_df = self.data.filter(
            (self.data['collection_due_at'] >= start_datetime) &
            (self.data['collection_due_at'] <= end_datetime)
        )

        return [BinCollection.model_validate(row) for row in filtered_df.iter_rows(named=True)]

        # Use self.data dataframe to build the result

        # return result

    # def get_bins_requiring_action(self) -> Dict:
    #     """
    #     Get bins that require action (display on hardware).
    #
    #     Returns bins with actionable statuses for today or tomorrow, prioritizing today.
    #     If no actionable bins exist, returns information about the next collection.
    #
    #     Returns:
    #         Dict with:
    #         - bins_to_display: List of dicts with 'bin' (Bin object), 'status', 'put_out_datetime'
    #         - display_date: The collection date being shown (today, tomorrow, or future)
    #         - next_collection_date: Date of next collection (for right arrow navigation)
    #         - previous_collection_date: Date of previous collection (for left arrow, minimum today)
    #     """
    #     today = datetime.date.today()
    #     tomorrow = today + datetime.timedelta(days=1)
    #
    #     # Actionable statuses are those where the bin needs attention or action
    #     actionable_statuses = {'due_out', 'not_yet_due', 'taken_out', 'put_out_early'}
    #
    #     # Check bins for today
    #     bins_today = self.get_bins_due_out_on(today)
    #     actionable_today = []
    #
    #     for bin_obj in bins_today:
    #         status, put_out_datetime, put_out_id = self.get_bin_status_for_date(bin_obj.id, today)
    #         if status in actionable_statuses:
    #             actionable_today.append({
    #                 'bin': bin_obj,
    #                 'status': status,
    #                 'put_out_datetime': put_out_datetime,
    #                 'put_out_id': put_out_id
    #             })
    #
    #     # If we have actionable bins today, return those
    #     if actionable_today:
    #         return {
    #             'bins_to_display': actionable_today,
    #             'display_date': today,
    #             'next_collection_date': self.get_collection_date_after(today),
    #             'previous_collection_date': max(today, self.get_collection_date_before(today) or today)
    #         }
    #
    #     # Check bins for tomorrow
    #     bins_tomorrow = self.get_bins_due_out_on(tomorrow)
    #     actionable_tomorrow = []
    #
    #     for bin_obj in bins_tomorrow:
    #         status, put_out_datetime, put_out_id = self.get_bin_status_for_date(bin_obj.id, tomorrow)
    #         if status in actionable_statuses:
    #             actionable_tomorrow.append({
    #                 'bin': bin_obj,
    #                 'status': status,
    #                 'put_out_datetime': put_out_datetime,
    #                 'put_out_id': put_out_id
    #             })
    #
    #     # If we have actionable bins tomorrow, return those
    #     if actionable_tomorrow:
    #         return {
    #             'bins_to_display': actionable_tomorrow,
    #             'display_date': tomorrow,
    #             'next_collection_date': self.get_collection_date_after(tomorrow),
    #             'previous_collection_date': today  # Can't go before today
    #         }
    #
    #     # No actionable bins - return next collection info
    #     next_collection = self.get_collection_date_after(today)
    #     return {
    #         'bins_to_display': [],
    #         'display_date': today,
    #         'next_collection_date': next_collection,
    #         'previous_collection_date': today  # Can't go before today
    #     }


