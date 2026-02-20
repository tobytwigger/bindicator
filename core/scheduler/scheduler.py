import datetime
from typing import List, Dict, Optional, Tuple, Literal, Iterator

from polars import DataFrame
import polars as pl

from core.scheduler.schemas import BinCollection, BinCollectionStatus
from core.scheduler.factory import BinCollectionFactory


class BinCollectionExplorer:
    def __init__(self, factory: BinCollectionFactory = None):
        if factory is None:
            factory = BinCollectionFactory()

        self._factory = factory
        self.data: DataFrame | None = None
        self.load_data()

    def __len__(self):
        if self.data is None:
            return 0
        return len(self.data)

    def load_data(self):
        self.data = None
        self.data = self._factory.build_collections_dataframe()

    def get_items_as_dict(self, start_date: datetime.date, end_date: datetime.date) -> List[BinCollection]:
        # Filter for the collection date being between the start and end date
        start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
        end_datetime = datetime.datetime.combine(end_date, datetime.time.max)

        filtered_df = self.data.filter(
            (self.data['collection_due_at'] >= start_datetime) &
            (self.data['collection_due_at'] <= end_datetime)
        )

        return [BinCollection.model_validate(row) for row in filtered_df.iter_rows(named=True)]

    def get_next_collections_for_all_bins(self) -> List[BinCollection]:
        """
        Get the next collection information for all bins.

        The filtering here is
            - collection_due_at is in the future (after right now)
            - Group by bin_id
            - Sort by collection_due_at ascending
            - Take the first entry for each bin_id (the next collection)
            - Sort by bin position (which is in the data)

        :return:
        """
        now = datetime.datetime.now()

        filtered_df = self.data.filter(
            self.data['collection_due_at'] > now
        ).sort('collection_due_at').group_by('bin_id').first().sort('bin_position')

        return [BinCollection.model_validate(row) for row in filtered_df.iter_rows(named=True)]

    def has_collection_after(self, after: datetime.datetime) -> bool:
        """
        Test if there is any collection occurring after the given datetime
        :param after:
        :return:
        """

        filtered_df = self.data.filter(
            self.data['collection_due_at'] > after
        )

        return len(filtered_df) > 0

    def get_next_collection_for_bin(self, bin_id: int) -> BinCollection | None:
        now = datetime.datetime.now()

        filtered_df = self.data.filter(
            (self.data['collection_due_at'] > now) &
            (self.data['bin_id'] == bin_id)
        ).sort('collection_due_at')

        if len(filtered_df) == 0:
            return None

        return BinCollection.model_validate(filtered_df.row(0, named=True))

    def get_not_yet_due_collection_days_by_index(self, index: int) -> Tuple[int, datetime.date, List[BinCollection]]:
        """
        Return collections where status is 'not_yet_due', grouped by collection date.

        Returns an iterator that yields tuples of (collection_date, list of BinCollection objects)
        sorted by collection_due_at.
        """
        # Filter for not_yet_due status and sort
        filtered_df = self.data.filter(
            pl.col("status").is_in([
                BinCollectionStatus.NOT_YET_DUE.value,
                BinCollectionStatus.PUT_OUT_EARLY.value
            ])
        ).sort("collection_due_at")

        # Group by date (without time) and iterate
        # We need to add a date column first
        df_with_date = filtered_df.with_columns(
            pl.col("collection_due_at").dt.date().alias("collection_date")
        )

        # get the `index`th unique date
        unique_dates = df_with_date["collection_date"].unique().sort()
        total_count = len(unique_dates)
        if index >= len(unique_dates):
            return None
        target_date = unique_dates[index]

        bin_collections_for_date = df_with_date.filter(pl.col("collection_date") == target_date)

        return total_count, target_date, [BinCollection.model_validate(row) for row in
                             bin_collections_for_date.iter_rows(named=True)]

    def get_not_yet_due_collection_day_for_bin_by_index(self, index: int, bin_id: int) -> Tuple[int, BinCollection]:
        """
        Return collections where status is 'not_yet_due', grouped by collection date.

        Returns an iterator that yields tuples of (collection_date, list of BinCollection objects)
        sorted by collection_due_at.
        """
        # Filter for not_yet_due status and sort
        filtered_df = (self.data.filter(
            pl.col("status").is_in([
                BinCollectionStatus.NOT_YET_DUE.value,
                BinCollectionStatus.PUT_OUT_EARLY.value
            ])
        ).filter(pl.col("bin_id") == bin_id)).sort("collection_due_at")

        if index >= len(filtered_df):
            index = len(filtered_df) - 1

        total_count = len(filtered_df)

        return total_count, BinCollection.model_validate(filtered_df.row(index, named=True))
