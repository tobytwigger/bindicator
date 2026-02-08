import sys
from pathlib import Path
from freezegun import freeze_time

root_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(root_dir))

from core.scheduler.scheduler import BinCollectionExplorer

import pytest
import datetime
from backend.tests.test_db import db, client
from core.database import schemas, models

@pytest.fixture(scope="function")
@freeze_time("2026-01-01 12:00:00")
def setup_db(db):
    bin1 = models.Bin(name="Bin1", position=1)
    bin2 = models.Bin(name="Bin2", position=2)
    bin3 = models.Bin(name="Bin3", position=3)
    bin4 = models.Bin(name="Bin4", position=4)
    db.add_all([bin1, bin2, bin3, bin4])
    db.commit()

    # Bin 1 and 3 went out yesterday
    # Bin 2 and 4 go out next week

    schedule1 = models.Schedule(start=datetime.datetime.now().date(), repeat_weeks=2, bin_id=bin1.id)
    schedule2 = models.Schedule(start=datetime.datetime.now().date() + datetime.timedelta(weeks=1), repeat_weeks=2, bin_id=bin2.id)
    schedule3 = models.Schedule(start=datetime.datetime.now().date(), repeat_weeks=2, bin_id=bin3.id)
    schedule4 = models.Schedule(start=datetime.datetime.now().date() + datetime.timedelta(weeks=1), repeat_weeks=2, bin_id=bin4.id)

    db.add_all([schedule1, schedule2, schedule3, schedule4])
    db.commit()

    bin_ids = {
        "Bin1": bin1.id,
        "Bin2": bin2.id,
        "Bin3": bin3.id,
        "Bin4": bin4.id,
    }
    yield db, bin_ids

@freeze_time("2026-01-01 12:00:00")
class TestGetSingleBinNextDueOut:
    def test_get_next_single_bin_date(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        # Should get the next collection date after 2026-01-01 for each bin
        bin_1_next_due = scheduler.get_collection_date_after(datetime.date(2026, 1, 1), bin_ids["Bin1"])
        bin_2_next_due = scheduler.get_collection_date_after(datetime.date(2026, 1, 1), bin_ids["Bin2"])
        bin_3_next_due = scheduler.get_collection_date_after(datetime.date(2026, 1, 1), bin_ids["Bin3"])
        bin_4_next_due = scheduler.get_collection_date_after(datetime.date(2026, 1, 1), bin_ids["Bin4"])
        assert bin_1_next_due == datetime.date(2026, 1, 15)
        assert bin_2_next_due == datetime.date(2026, 1, 8)
        assert bin_3_next_due == datetime.date(2026, 1, 15)
        assert bin_4_next_due == datetime.date(2026, 1, 8)

    def test_get_single_bin_date_after_future_date(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        # Should get the next collection date after a future date
        bin_1_next_due = scheduler.get_collection_date_after(datetime.date(2026, 2, 16), bin_ids["Bin1"])
        bin_2_next_due = scheduler.get_collection_date_after(datetime.date(2026, 2, 16), bin_ids["Bin2"])
        bin_3_next_due = scheduler.get_collection_date_after(datetime.date(2026, 2, 16), bin_ids["Bin3"])
        bin_4_next_due = scheduler.get_collection_date_after(datetime.date(2026, 2, 16), bin_ids["Bin4"])
        assert bin_1_next_due == datetime.date(2026, 2, 26)
        assert bin_2_next_due == datetime.date(2026, 2, 19)
        assert bin_3_next_due == datetime.date(2026, 2, 26)
        assert bin_4_next_due == datetime.date(2026, 2, 19)

    def test_get_single_bin_returns_none_if_no_schedule(self, client, db):
        bin1 = models.Bin(name="Bin1", position=1)
        db.add(bin1)
        db.commit()
        scheduler = BinCollectionExplorer(db)
        bin_1_next_due = scheduler.get_collection_date_after(datetime.date(2026, 1, 1), bin1.id)
        assert bin_1_next_due is None

    def test_get_single_bin_returns_none_if_no_schedule_after_date(self, client, db):
        bin1 = models.Bin(name="Bin1", position=1)
        db.add(bin1)
        db.commit()
        schedule1 = models.Schedule(start=datetime.datetime.now().date(), end=datetime.date(
            year=2026, month=10, day=15
        ), repeat_weeks=2, bin_id=bin1.id)
        db.add(schedule1)
        db.commit()
        scheduler = BinCollectionExplorer(db)
        bin_1_next_due = scheduler.get_collection_date_after(datetime.date(2026, 11, 1), bin1.id)
        assert bin_1_next_due is None

@freeze_time("2026-01-01 12:00:00")
class TestGetAnyBinNextDueOut:
    def test_get_next_bin_date(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        # Should get the next collection date after 2026-01-01 for any bin
        bins_next_due = scheduler.get_collection_date_after(datetime.date(2026, 1, 1))
        assert bins_next_due == datetime.date(2026, 1, 8)

    def test_get_bin_date_after_future_date(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        bins_next_due = scheduler.get_collection_date_after(datetime.date(2026, 2, 16))
        assert bins_next_due == datetime.date(2026, 2, 19)

    def test_get_bin_date_after_future_date_outside_cache(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        bins_next_due = scheduler.get_collection_date_after(datetime.date(2028, 2, 16))
        assert bins_next_due is None

    def test_get_bin_returns_none_if_no_schedule(self, client, db):
        bin1 = models.Bin(name="Bin1", position=1)
        db.add(bin1)
        db.commit()
        scheduler = BinCollectionExplorer(db)
        bins_next_due = scheduler.get_collection_date_after(datetime.date(2026, 1, 1))
        assert bins_next_due is None

    def test_get_bin_returns_none_if_no_schedule_after_date(self, client, db):
        bin1 = models.Bin(name="Bin1", position=1)
        bin2 = models.Bin(name="Bin2", position=2)
        db.add_all([bin1, bin2])
        db.commit()
        schedule1 = models.Schedule(start=datetime.datetime.now().date(), end=datetime.datetime.now().date() + datetime.timedelta(days=365), repeat_weeks=2, bin_id=bin1.id)
        schedule2 = models.Schedule(start=datetime.datetime.now().date() + datetime.timedelta(weeks=1), end=datetime.datetime.now().date() + datetime.timedelta(days=365), repeat_weeks=2,
                                    bin_id=bin2.id)
        db.add_all([schedule1, schedule2])
        db.commit()
        scheduler = BinCollectionExplorer(db)
        bins_next_due = scheduler.get_collection_date_after(datetime.date(2027, 11, 1))
        assert bins_next_due is None

@freeze_time("2026-01-01 12:00:00")
class TestGetSingleBinLastDueOut:
    def test_get_last_collection_date(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        # The first collection is on 2026-01-01, so before that should be None
        assert scheduler.get_collection_date_before(datetime.date(2026, 1, 1), bin_ids["Bin1"]) is None
        # After the first collection, but before the second
        assert scheduler.get_collection_date_before(datetime.date(2026, 1, 15), bin_ids["Bin1"]) == datetime.date(2026, 1, 1)
        # After the second collection
        assert scheduler.get_collection_date_before(datetime.date(2026, 1, 29), bin_ids["Bin1"]) == datetime.date(2026, 1, 15)

    def test_get_last_collection_date_before_past_date(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        # Before any collections
        assert scheduler.get_collection_date_before(datetime.date(2025, 1, 1), bin_ids["Bin1"]) is None

    def test_get_last_collection_date_returns_none_if_no_schedule(self, client, db):
        bin1 = models.Bin(name="Bin1", position=1)
        db.add(bin1)
        db.commit()
        scheduler = BinCollectionExplorer(db)
        assert scheduler.get_collection_date_before(datetime.date(2026, 1, 1), bin1.id) is None

    def test_get_last_collection_date_returns_none_if_no_schedule_before_date(self, client, db):
        bin1 = models.Bin(name="Bin1", position=1)
        db.add(bin1)
        db.commit()
        schedule1 = models.Schedule(start=datetime.datetime.now().date(), end=datetime.date(
            year=2026, month=10, day=15
        ), repeat_weeks=2, bin_id=bin1.id)
        db.add(schedule1)
        db.commit()
        scheduler = BinCollectionExplorer(db)
        # Before the first scheduled collection
        assert scheduler.get_collection_date_before(datetime.date(2025, 1, 1), bin1.id) is None

@freeze_time("2026-01-01 12:00:00")
class TestGetAnyBinLastDueOut:
    def test_get_last_collection_date(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        # The earliest collection for any bin is 2026-01-01, so before that should be None
        assert scheduler.get_collection_date_before(datetime.date(2026, 1, 1)) is None
        # After the first collection, but before the next
        assert scheduler.get_collection_date_before(datetime.date(2026, 1, 8)) == datetime.date(2026, 1, 1)
        # After the next collection
        assert scheduler.get_collection_date_before(datetime.date(2026, 1, 15)) == datetime.date(2026, 1, 8)

    def test_get_last_collection_date_before_past_date(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        # Before any collections
        assert scheduler.get_collection_date_before(datetime.date(2025, 1, 1)) is None

    def test_get_last_collection_date_returns_none_if_no_schedule(self, client, db):
        bin1 = models.Bin(name="Bin1", position=1)
        db.add(bin1)
        db.commit()
        scheduler = BinCollectionExplorer(db)
        assert scheduler.get_collection_date_before(datetime.date(2026, 1, 1)) is None

    def test_get_last_collection_date_returns_none_if_no_schedule_before_date(self, client, db):
        bin1 = models.Bin(name="Bin1", position=1)
        bin2 = models.Bin(name="Bin2", position=2)
        db.add_all([bin1, bin2])
        db.commit()
        schedule1 = models.Schedule(start=datetime.datetime.now().date(), end=datetime.datetime.now().date() + datetime.timedelta(days=365), repeat_weeks=2, bin_id=bin1.id)
        schedule2 = models.Schedule(start=datetime.datetime.now().date() + datetime.timedelta(weeks=1), end=datetime.datetime.now().date() + datetime.timedelta(days=365), repeat_weeks=2,
                                    bin_id=bin2.id)
        db.add_all([schedule1, schedule2])
        db.commit()
        scheduler = BinCollectionExplorer(db)
        # Before the first scheduled collection for any bin
        assert scheduler.get_collection_date_before(datetime.date(2025, 1, 1)) is None

@freeze_time("2026-01-01 12:00:00")
class TestGetBinsDueOutOn:
    def test_it_returns_the_bins_due_out_on_the_date(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        # On 2026-01-01, Bin1 and Bin3 are due out
        bins_due = scheduler.get_bins_due_out_on(datetime.date(2026, 1, 1))
        bin_ids_due = sorted([b.id for b in bins_due])
        assert bin_ids_due == sorted([bin_ids["Bin1"], bin_ids["Bin3"]])
    def test_it_returns_an_empty_list_if_no_bins_due_out_on_the_date(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        # On a date with no collections
        bins_due = scheduler.get_bins_due_out_on(datetime.date(2025, 1, 1))
        assert bins_due == []

@freeze_time("2026-01-01 12:00:00")
class TestGetBinById:
    def test_it_returns_the_bin_with_the_given_id(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        bin1 = scheduler.get_bin_by_id(bin_ids["Bin1"])
        assert bin1.id == bin_ids["Bin1"]

    def test_it_returns_none_if_no_bin_with_the_given_id(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        bin1 = scheduler.get_bin_by_id(999999)
        assert bin1 is None

@freeze_time("2026-01-01 12:00:00")
class TestGetBinByPosition:
    def test_it_returns_the_bin_with_the_given_position(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        bin1 = scheduler.get_bin_by_position(1)
        assert bin1.id == bin_ids["Bin1"]

    def test_it_returns_none_if_no_bin_with_the_given_position(self, client, setup_db):
        db, bin_ids = setup_db
        scheduler = BinCollectionExplorer(db)
        bin1 = scheduler.get_bin_by_position(999999)
        assert bin1 is None