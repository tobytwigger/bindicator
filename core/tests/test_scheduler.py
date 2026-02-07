import sys
from pathlib import Path
from freezegun import freeze_time

root_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(root_dir))

from core.scheduler.scheduler import Scheduler

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
class TestGetSingleBinSchedule:
    def test_get_next_single_bin_date(self, client, setup_db):
        db, bin_ids = setup_db

        scheduler = Scheduler(db)

        bin_1_next_due = scheduler.get_date_bin_next_due_out(bin_ids["Bin1"])
        bin_2_next_due = scheduler.get_date_bin_next_due_out(bin_ids["Bin2"])
        bin_3_next_due = scheduler.get_date_bin_next_due_out(bin_ids["Bin3"])
        bin_4_next_due = scheduler.get_date_bin_next_due_out(bin_ids["Bin4"])

        assert bin_1_next_due == datetime.date(2026, 1, 15)
        assert bin_2_next_due == datetime.date(2026, 1, 8)
        assert bin_3_next_due == datetime.date(2026, 1, 15)
        assert bin_4_next_due == datetime.date(2026, 1, 8)

    def test_get_single_bin_date_after_future_date(self, client, setup_db):
        db, bin_ids = setup_db

        scheduler = Scheduler(db)

        bin_1_next_due = scheduler.get_date_bin_next_due_out(bin_ids["Bin1"], after=datetime.date(2026, 2, 16))
        bin_2_next_due = scheduler.get_date_bin_next_due_out(bin_ids["Bin2"], after=datetime.date(2026, 2, 16))
        bin_3_next_due = scheduler.get_date_bin_next_due_out(bin_ids["Bin3"], after=datetime.date(2026, 2, 16))
        bin_4_next_due = scheduler.get_date_bin_next_due_out(bin_ids["Bin4"], after=datetime.date(2026, 2, 16))

        assert bin_1_next_due == datetime.date(2026, 2, 26)
        assert bin_2_next_due == datetime.date(2026, 2, 19)
        assert bin_3_next_due == datetime.date(2026, 2, 26)
        assert bin_4_next_due == datetime.date(2026, 2, 19)

    def test_get_single_bin_returns_none_if_no_schedule(self, client, db):
        bin1 = models.Bin(name="Bin1", position=1)
        db.add(bin1)
        db.commit()

        scheduler = Scheduler(db)

        bin_1_next_due = scheduler.get_date_bin_next_due_out(bin1.id)

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

        scheduler = Scheduler(db)

        bin_1_next_due = scheduler.get_date_bin_next_due_out(bin1.id, after=datetime.date(2026, 11, 1))

        assert bin_1_next_due is None


    def test_get_all_single_bin_dates(self, client, db):
        bin1 = models.Bin(name="Bin1", position=1)
        db.add(bin1)
        db.commit()

        schedule1 = models.Schedule(start=datetime.date(
            year=2026, month=1, day=1
        ), end=datetime.date(
            year=2026, month=2, day=17
        ), repeat_weeks=2, bin_id=bin1.id)

        db.add(schedule1)
        db.commit()

        scheduler = Scheduler(db)

        bin_1_due_dates = scheduler.get_all_dates_bin_due_out(bin1.id)

        assert len(bin_1_due_dates) == 4
        assert bin_1_due_dates[0] == datetime.date(2026, 1, 1)
        assert bin_1_due_dates[1] == datetime.date(2026, 1, 15)
        assert bin_1_due_dates[2] == datetime.date(2026, 1, 29)
        assert bin_1_due_dates[3] == datetime.date(2026, 2, 12)

    def test_get_all_single_bin_dates_after(self, client, db):
        bin1 = models.Bin(name="Bin1", position=1)
        db.add(bin1)
        db.commit()

        schedule1 = models.Schedule(start=datetime.date(
            year=2026, month=1, day=1
        ), end=datetime.date(
            year=2026, month=2, day=17
        ), repeat_weeks=2, bin_id=bin1.id)

        db.add(schedule1)
        db.commit()

        scheduler = Scheduler(db)

        bin_1_due_dates = scheduler.get_all_dates_bin_due_out(bin1.id, after=datetime.date(2026, 1, 16))

        assert len(bin_1_due_dates) == 2
        assert bin_1_due_dates[0] == datetime.date(2026, 1, 29)
        assert bin_1_due_dates[1] == datetime.date(2026, 2, 12)


@freeze_time("2026-01-01 12:00:00")
class TestGetMultipleBinSchedule:
    def test_get_next_multiple_bin_date(self, client, setup_db):
        db, bin_ids = setup_db

        pass

    def test_get_multiple_bin_date_after_future_date(self, client, db):
        pass

    def test_get_all_multiple_bin_dates_until(self, client, db):
        pass
