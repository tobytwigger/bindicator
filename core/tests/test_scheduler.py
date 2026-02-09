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
from core.database.repositories import SettingsRepository

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

# ============================================================================
# Tests for get_calendar with status tracking
# ============================================================================

@freeze_time("2026-02-10 08:00:00")  # Before collection time (09:00)
class TestGetCalendarStatuses:
    """Test the status field in get_calendar results."""

    @pytest.fixture(scope="function")
    def setup_calendar_test(self, db):
        """Setup bins, schedules, and settings for calendar status tests."""
        # Create bins
        bin1 = models.Bin(name="General Waste", position=1, colour="#444444")
        bin2 = models.Bin(name="Recycling", position=2, colour="#2ecc40")
        db.add_all([bin1, bin2])
        db.commit()

        # Create schedules - both due on 2026-02-10
        schedule1 = models.Schedule(
            start=datetime.datetime(2026, 2, 10),
            repeat_weeks=1,
            bin_id=bin1.id
        )
        schedule2 = models.Schedule(
            start=datetime.datetime(2026, 2, 10),
            repeat_weeks=1,
            bin_id=bin2.id
        )
        db.add_all([schedule1, schedule2])
        db.commit()

        # Setup default settings (will be saved to file by SettingsRepository)
        from core.database.repositories import SettingsRepository
        settings_repo = SettingsRepository()
        settings_repo.create_or_update(schemas.SettingsEdit(
            timeout=120,
            put_out_day_before=True,  # Put out the day before
            put_out_time="17:00",     # Should be put out by 5pm day before
            collection_time="09:00"   # Collection at 9am
        ))

        yield db, {"bin1": bin1.id, "bin2": bin2.id}

    def test_status_not_yet_due(self, client, setup_calendar_test):
        """Test 'not_yet_due' status when current time is before put_out_time on day before."""
        with freeze_time("2026-02-09 10:00:00"):  # Day before collection, morning
            db, bin_ids = setup_calendar_test
            scheduler = BinCollectionExplorer(db)

            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            # Find the Feb 10 entry
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            assert feb_10 is not None
            assert len(feb_10['bins']) == 2

            # Both bins should be 'not_yet_due' (before 17:00 on day before)
            for bin in feb_10['bins']:
                assert bin['status'] == 'not_yet_due'
                assert 'put_out_date' not in bin

    def test_status_due_out(self, client, setup_calendar_test):
        """Test 'due_out' status when past put_out_time but before collection_time."""
        with freeze_time("2026-02-09 18:00:00"):  # Day before, after 17:00 put_out_time
            db, bin_ids = setup_calendar_test
            scheduler = BinCollectionExplorer(db)

            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            assert feb_10 is not None

            # Both bins should be 'due_out'
            for bin in feb_10['bins']:
                assert bin['status'] == 'due_out'
                assert 'put_out_date' not in bin

    def test_status_taken_out_before_collection(self, client, setup_calendar_test):
        """Test 'taken_out' status when bin was put out and collection hasn't happened."""
        with freeze_time("2026-02-10 08:00:00"):  # Collection day, before 09:00
            db, bin_ids = setup_calendar_test

            # Record that bin1 was put out
            put_out = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 9, 18, 30)
            )
            db.add(put_out)
            db.commit()

            scheduler = BinCollectionExplorer(db)

            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            assert feb_10 is not None

            # Find bin1 (was put out) and bin2 (was not put out)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            bin2 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin2"]), None)

            assert bin1 is not None
            assert bin1['status'] == 'taken_out'
            assert bin1['put_out_date'] == '2026-02-09'  # Date component only

            assert bin2 is not None
            assert bin2['status'] == 'due_out'  # Should be out by now but wasn't
            assert 'put_out_date' not in bin2

    def test_status_taken_out_after_collection(self, client, setup_calendar_test):
        """Test 'collected' status after collection time passes (was 'taken_out')."""
        with freeze_time("2026-02-10 10:00:00"):  # After 09:00 collection time
            db, bin_ids = setup_calendar_test

            # Record that bin1 was put out
            put_out = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 9, 18, 30)
            )
            db.add(put_out)
            db.commit()

            scheduler = BinCollectionExplorer(db)

            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            assert feb_10 is not None

            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)

            assert bin1 is not None
            # After collection time, status should be 'collected'
            assert bin1['status'] == 'collected'
            assert bin1['put_out_date'] == '2026-02-09'
            assert 'put_out_id' in bin1
            assert bin1['put_out_id'] is not None

    def test_status_missed(self, client, setup_calendar_test):
        """Test 'missed' status when collection time passed and bin wasn't put out."""
        with freeze_time("2026-02-10 10:00:00"):  # After 09:00 collection time
            db, bin_ids = setup_calendar_test

            # No put_out record - bin was missed
            scheduler = BinCollectionExplorer(db)

            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            assert feb_10 is not None

            # Both bins should be 'missed'
            for bin in feb_10['bins']:
                assert bin['status'] == 'missed'
                assert 'put_out_date' not in bin

    def test_status_with_put_out_day_before_false(self, client, setup_calendar_test):
        """Test status calculation when put_out_day_before is False (same day)."""
        db, bin_ids = setup_calendar_test

        # Update settings to put out same day
        from core.database.repositories import SettingsRepository
        settings_repo = SettingsRepository()
        settings_repo.create_or_update(schemas.SettingsEdit(
            put_out_day_before=False,
            put_out_time="07:00"  # Put out by 7am on collection day
        ))

        # Test at 6am on collection day - should be not_yet_due
        with freeze_time("2026-02-10 06:00:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            for bin in feb_10['bins']:
                assert bin['status'] == 'not_yet_due'

        # Test at 7:30am - should be due_out
        with freeze_time("2026-02-10 07:30:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            for bin in feb_10['bins']:
                assert bin['status'] == 'due_out'

    def test_multiple_collection_dates_with_different_statuses(self, client, setup_calendar_test):
        """Test that different collection dates can have different statuses."""
        with freeze_time("2026-02-10 08:00:00"):  # First collection day, before collection
            db, bin_ids = setup_calendar_test

            # Put out bin1 for Feb 10 collection (today - taken out)
            put_out_1 = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 9, 18, 0)
            )
            db.add(put_out_1)
            db.commit()

            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            # Feb 10 - bin1 was taken out, bin2 was not
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            assert feb_10 is not None
            bin1_feb10 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            bin2_feb10 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin2"]), None)
            assert bin1_feb10['status'] == 'taken_out'
            assert bin2_feb10['status'] == 'due_out'

            # Feb 17 - not yet due (future)
            feb_17 = next((item for item in calendar if item['date'] == '2026-02-17'), None)
            assert feb_17 is not None
            bin1_feb17 = next((b for b in feb_17['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1_feb17['status'] == 'not_yet_due'

    def test_status_with_bin_day_replacement(self, client, setup_calendar_test):
        """Test that status works correctly with bin day replacements."""
        db, bin_ids = setup_calendar_test

        # Move Feb 10 collection to Feb 11 (holiday)
        replacement = models.BinDayReplacement(
            replace=datetime.datetime(2026, 2, 10),
            replace_with=datetime.datetime(2026, 2, 11)
        )
        db.add(replacement)
        db.commit()

        # Test on Feb 11 before collection
        with freeze_time("2026-02-11 08:00:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            # Feb 10 should not be in calendar
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            assert feb_10 is None

            # Feb 11 should have the bins with due_out status
            feb_11 = next((item for item in calendar if item['date'] == '2026-02-11'), None)
            assert feb_11 is not None
            for bin in feb_11['bins']:
                assert bin['status'] == 'due_out'

    def test_boundary_exact_put_out_time(self, client, setup_calendar_test):
        """Test status at exact put_out_time boundary."""
        # Exactly at put_out_time (17:00 on day before)
        with freeze_time("2026-02-09 17:00:00"):
            db, bin_ids = setup_calendar_test
            scheduler = BinCollectionExplorer(db)

            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            for bin in feb_10['bins']:
                # At exactly 17:00, should be due_out (>= comparison)
                assert bin['status'] == 'due_out'

    def test_boundary_exact_collection_time(self, client, setup_calendar_test):
        """Test status at exact collection_time boundary."""
        # Exactly at collection_time (09:00 on collection day)
        with freeze_time("2026-02-10 09:00:00"):
            db, bin_ids = setup_calendar_test
            scheduler = BinCollectionExplorer(db)

            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            for bin in feb_10['bins']:
                # At exactly 09:00, should be missed (>= comparison)
                assert bin['status'] == 'missed'

    def test_put_out_datetime_preserved(self, client, setup_calendar_test):
        """Test that put_out_date is extracted correctly from datetime."""
        with freeze_time("2026-02-10 08:00:00"):
            db, bin_ids = setup_calendar_test

            # Put out at specific time
            put_out = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 9, 14, 23, 45)  # Specific time
            )
            db.add(put_out)
            db.commit()

            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)

            # Should show date part only, not time
            assert bin1['put_out_date'] == '2026-02-09'

    def test_early_put_out_matches_correct_collection(self, client, setup_calendar_test):
        """Test that bins put out early are matched to the correct collection date."""
        with freeze_time("2026-02-10 08:00:00"):
            db, bin_ids = setup_calendar_test

            # Put out bin1 early (2 days before) for Feb 10 collection
            put_out = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 8, 18, 0)  # 2 days early
            )
            db.add(put_out)
            db.commit()

            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            # Should match to the first collection on or after the put-out date (Feb 10)
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            assert feb_10 is not None
            bin1_feb10 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            # Put out on Feb 8 at 18:00, which is before the due time of Feb 9 at 17:00
            assert bin1_feb10['status'] == 'put_out_early'
            assert bin1_feb10['put_out_date'] == '2026-02-08'

            # Feb 17 should not show as taken out (different collection)
            feb_17 = next((item for item in calendar if item['date'] == '2026-02-17'), None)
            assert feb_17 is not None
            bin1_feb17 = next((b for b in feb_17['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1_feb17['status'] == 'not_yet_due'  # Not put out for this collection yet


# ============================================================================
# Tests for 'put_out_early' and 'collected' statuses
# ============================================================================

@freeze_time("2026-02-10 08:00:00")
class TestPutOutEarlyStatus:
    """Test the 'put_out_early' status when bins are put out before they're due."""

    @pytest.fixture(scope="function")
    def setup_early_test(self, db):
        """Setup bins, schedules, and settings for early put-out tests."""
        # Create bin
        bin1 = models.Bin(name="Blue Bin", position=1, colour="#0074D9")
        db.add(bin1)
        db.commit()

        # Create schedule - collection on Feb 10
        schedule1 = models.Schedule(
            start=datetime.datetime(2026, 2, 10),
            repeat_weeks=1,
            bin_id=bin1.id
        )
        db.add(schedule1)
        db.commit()

        # Setup settings: put out day before at 17:00
        from core.database.repositories import SettingsRepository
        settings_repo = SettingsRepository()
        settings_repo.create_or_update(schemas.SettingsEdit(
            timeout=120,
            put_out_day_before=True,
            put_out_time="17:00",
            collection_time="09:00"
        ))

        yield db, {"bin1": bin1.id}

    def test_put_out_early_before_due_time_before_collection(self, client, setup_early_test):
        """Test 'put_out_early' status when bin put out before due time, before collection."""
        with freeze_time("2026-02-10 08:00:00"):  # Collection day morning, before 09:00
            db, bin_ids = setup_early_test

            # Put out bin early (before 17:00 on Feb 9, which is when it's due)
            put_out = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 9, 12, 0)  # 12pm - before 17:00 due time
            )
            db.add(put_out)
            db.commit()

            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            assert feb_10 is not None
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)

            assert bin1 is not None
            assert bin1['status'] == 'put_out_early'
            assert bin1['put_out_date'] == '2026-02-09'
            assert 'put_out_id' in bin1

    def test_put_out_early_very_early_before_collection(self, client, setup_early_test):
        """Test 'put_out_early' when put out very early (2 days before due)."""
        with freeze_time("2026-02-10 08:00:00"):
            db, bin_ids = setup_early_test

            # Put out very early (Feb 8 - 2 days before collection)
            put_out = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 8, 10, 0)
            )
            db.add(put_out)
            db.commit()

            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)

            assert bin1['status'] == 'put_out_early'
            assert bin1['put_out_date'] == '2026-02-08'

    def test_put_out_early_becomes_collected_after_collection_time(self, client, setup_early_test):
        """Test that 'put_out_early' becomes 'collected' after collection time passes."""
        with freeze_time("2026-02-10 10:00:00"):  # After 09:00 collection time
            db, bin_ids = setup_early_test

            # Put out early
            put_out = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 9, 12, 0)
            )
            db.add(put_out)
            db.commit()

            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)

            # After collection time, should be 'collected' not 'put_out_early'
            assert bin1['status'] == 'collected'
            assert bin1['put_out_date'] == '2026-02-09'
            assert 'put_out_id' in bin1

    def test_put_out_on_time_vs_early(self, client, setup_early_test):
        """Test difference between 'taken_out' (on time) and 'put_out_early'."""
        with freeze_time("2026-02-10 08:00:00"):
            db, bin_ids = setup_early_test

            # Create another bin for comparison
            bin2 = models.Bin(name="Green Bin", position=2, colour="#2ecc40")
            db.add(bin2)
            db.commit()

            schedule2 = models.Schedule(
                start=datetime.datetime(2026, 2, 10),
                repeat_weeks=1,
                bin_id=bin2.id
            )
            db.add(schedule2)
            db.commit()

            # Bin1 put out early (before 17:00 on Feb 9)
            put_out_1 = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 9, 12, 0)  # Early
            )
            # Bin2 put out on time (after 17:00 on Feb 9)
            put_out_2 = models.BinPutOut(
                bin_id=bin2.id,
                date_put_out_at=datetime.datetime(2026, 2, 9, 18, 30)  # On time
            )
            db.add_all([put_out_1, put_out_2])
            db.commit()

            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            bin2 = next((b for b in feb_10['bins'] if b['id'] == bin2.id), None)

            assert bin1['status'] == 'put_out_early'
            assert bin2['status'] == 'taken_out'

    def test_put_out_early_with_same_day_collection(self, client, setup_early_test):
        """Test 'put_out_early' when put_out_day_before is False."""
        db, bin_ids = setup_early_test

        # Change settings: put out same day at 07:00
        from core.database.repositories import SettingsRepository
        settings_repo = SettingsRepository()
        settings_repo.create_or_update(schemas.SettingsEdit(
            put_out_day_before=False,
            put_out_time="07:00"
        ))

        with freeze_time("2026-02-10 08:00:00"):  # After 07:00, before 09:00
            # Put out at 06:00 (before 07:00 due time)
            put_out = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 10, 6, 0)
            )
            db.add(put_out)
            db.commit()

            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)

            assert bin1['status'] == 'put_out_early'


@freeze_time("2026-02-10 10:00:00")
class TestCollectedStatus:
    """Test the 'collected' status when bins have been collected."""

    @pytest.fixture(scope="function")
    def setup_collected_test(self, db):
        """Setup for collected status tests."""
        bin1 = models.Bin(name="Red Bin", position=1, colour="#FF4136")
        db.add(bin1)
        db.commit()

        schedule1 = models.Schedule(
            start=datetime.datetime(2026, 2, 10),
            repeat_weeks=1,
            bin_id=bin1.id
        )
        db.add(schedule1)
        db.commit()

        from core.database.repositories import SettingsRepository
        settings_repo = SettingsRepository()
        settings_repo.create_or_update(schemas.SettingsEdit(
            timeout=120,
            put_out_day_before=True,
            put_out_time="17:00",
            collection_time="09:00"
        ))

        yield db, {"bin1": bin1.id}

    def test_collected_status_after_collection_time(self, client, setup_collected_test):
        """Test 'collected' status after collection time has passed."""
        with freeze_time("2026-02-10 10:00:00"):  # After 09:00 collection
            db, bin_ids = setup_collected_test

            # Put out on time
            put_out = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 9, 18, 0)
            )
            db.add(put_out)
            db.commit()

            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)

            assert bin1['status'] == 'collected'
            assert bin1['put_out_date'] == '2026-02-09'
            assert bin1['put_out_id'] is not None

    def test_collected_status_many_hours_after_collection(self, client, setup_collected_test):
        """Test 'collected' status remains even hours after collection."""
        with freeze_time("2026-02-10 20:00:00"):  # 11 hours after collection
            db, bin_ids = setup_collected_test

            put_out = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 9, 18, 0)
            )
            db.add(put_out)
            db.commit()

            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)

            assert bin1['status'] == 'collected'

    def test_collected_from_early_put_out(self, client, setup_collected_test):
        """Test that early put-outs also become 'collected' after collection time."""
        with freeze_time("2026-02-10 10:00:00"):
            db, bin_ids = setup_collected_test

            # Put out early
            put_out = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 9, 12, 0)  # Before 17:00
            )
            db.add(put_out)
            db.commit()

            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)

            # Early put-out should become 'collected' after collection time
            assert bin1['status'] == 'collected'
            assert bin1['put_out_date'] == '2026-02-09'

    def test_put_out_id_persists_in_collected_status(self, client, setup_collected_test):
        """Test that put_out_id is preserved in collected status."""
        with freeze_time("2026-02-10 10:00:00"):
            db, bin_ids = setup_collected_test

            put_out = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 9, 18, 0)
            )
            db.add(put_out)
            db.commit()
            put_out_id = put_out.id

            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)

            assert bin1['status'] == 'collected'
            assert bin1['put_out_id'] == put_out_id

    def test_next_collection_not_affected_by_previous_collected(self, client, setup_collected_test):
        """Test that next collection is independent from previous collected status."""
        with freeze_time("2026-02-10 10:00:00"):
            db, bin_ids = setup_collected_test

            # Put out for Feb 10 collection
            put_out = models.BinPutOut(
                bin_id=bin_ids["bin1"],
                date_put_out_at=datetime.datetime(2026, 2, 9, 18, 0)
            )
            db.add(put_out)
            db.commit()

            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(
                datetime.date(2026, 2, 1),
                datetime.date(2026, 2, 28)
            )

            # Feb 10 - collected
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1_feb10 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1_feb10['status'] == 'collected'

            # Feb 17 - not yet due (independent from previous collection)
            feb_17 = next((item for item in calendar if item['date'] == '2026-02-17'), None)
            bin1_feb17 = next((b for b in feb_17['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1_feb17['status'] == 'not_yet_due'
            assert 'put_out_id' not in bin1_feb17  # No put-out record for this collection


@freeze_time("2026-02-10 08:00:00")
class TestStatusTransitions:
    """Test status transitions throughout the collection cycle."""

    @pytest.fixture(scope="function")
    def setup_transition_test(self, db):
        """Setup for status transition tests."""
        bin1 = models.Bin(name="Yellow Bin", position=1, colour="#FFDC00")
        db.add(bin1)
        db.commit()

        schedule1 = models.Schedule(
            start=datetime.datetime(2026, 2, 10),
            repeat_weeks=1,
            bin_id=bin1.id
        )
        db.add(schedule1)
        db.commit()

        from core.database.repositories import SettingsRepository
        settings_repo = SettingsRepository()
        settings_repo.create_or_update(schemas.SettingsEdit(
            timeout=120,
            put_out_day_before=True,
            put_out_time="17:00",
            collection_time="09:00"
        ))

        yield db, {"bin1": bin1.id}

    def test_full_lifecycle_put_out_on_time(self, client, setup_transition_test):
        """Test full status lifecycle: not_yet_due -> due_out -> taken_out -> collected."""
        db, bin_ids = setup_transition_test

        # 1. Feb 9 at 10:00 - not_yet_due
        with freeze_time("2026-02-09 10:00:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(datetime.date(2026, 2, 1), datetime.date(2026, 2, 28))
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1['status'] == 'not_yet_due'

        # 2. Feb 9 at 18:00 - due_out (after 17:00)
        with freeze_time("2026-02-09 18:00:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(datetime.date(2026, 2, 1), datetime.date(2026, 2, 28))
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1['status'] == 'due_out'

        # 3. Put out at 18:30 on Feb 9
        put_out = models.BinPutOut(
            bin_id=bin_ids["bin1"],
            date_put_out_at=datetime.datetime(2026, 2, 9, 18, 30)
        )
        db.add(put_out)
        db.commit()

        # 4. Feb 10 at 08:00 - taken_out (after put out, before collection)
        with freeze_time("2026-02-10 08:00:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(datetime.date(2026, 2, 1), datetime.date(2026, 2, 28))
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1['status'] == 'taken_out'

        # 5. Feb 10 at 10:00 - collected (after collection time)
        with freeze_time("2026-02-10 10:00:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(datetime.date(2026, 2, 1), datetime.date(2026, 2, 28))
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1['status'] == 'collected'

    def test_full_lifecycle_put_out_early(self, client, setup_transition_test):
        """Test full status lifecycle with early put-out: not_yet_due -> put_out_early -> collected."""
        db, bin_ids = setup_transition_test

        # 1. Feb 9 at 10:00 - not_yet_due
        with freeze_time("2026-02-09 10:00:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(datetime.date(2026, 2, 1), datetime.date(2026, 2, 28))
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1['status'] == 'not_yet_due'

        # 2. Put out early at 12:00 on Feb 9 (before 17:00)
        put_out = models.BinPutOut(
            bin_id=bin_ids["bin1"],
            date_put_out_at=datetime.datetime(2026, 2, 9, 12, 0)
        )
        db.add(put_out)
        db.commit()

        # 3. Feb 9 at 18:00 - put_out_early (was put out before due time)
        with freeze_time("2026-02-09 18:00:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(datetime.date(2026, 2, 1), datetime.date(2026, 2, 28))
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1['status'] == 'put_out_early'

        # 4. Feb 10 at 08:00 - still put_out_early (before collection)
        with freeze_time("2026-02-10 08:00:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(datetime.date(2026, 2, 1), datetime.date(2026, 2, 28))
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1['status'] == 'put_out_early'

        # 5. Feb 10 at 10:00 - collected (after collection time)
        with freeze_time("2026-02-10 10:00:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(datetime.date(2026, 2, 1), datetime.date(2026, 2, 28))
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1['status'] == 'collected'

    def test_lifecycle_not_put_out(self, client, setup_transition_test):
        """Test status lifecycle when bin is not put out: not_yet_due -> due_out -> missed."""
        db, bin_ids = setup_transition_test

        # 1. Feb 9 at 10:00 - not_yet_due
        with freeze_time("2026-02-09 10:00:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(datetime.date(2026, 2, 1), datetime.date(2026, 2, 28))
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1['status'] == 'not_yet_due'

        # 2. Feb 9 at 18:00 - due_out
        with freeze_time("2026-02-09 18:00:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(datetime.date(2026, 2, 1), datetime.date(2026, 2, 28))
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1['status'] == 'due_out'

        # 3. Feb 10 at 08:00 - still due_out
        with freeze_time("2026-02-10 08:00:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(datetime.date(2026, 2, 1), datetime.date(2026, 2, 28))
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1['status'] == 'due_out'

        # 4. Feb 10 at 10:00 - missed (never put out, collection passed)
        with freeze_time("2026-02-10 10:00:00"):
            scheduler = BinCollectionExplorer(db)
            calendar = scheduler.get_calendar(datetime.date(2026, 2, 1), datetime.date(2026, 2, 28))
            feb_10 = next((item for item in calendar if item['date'] == '2026-02-10'), None)
            bin1 = next((b for b in feb_10['bins'] if b['id'] == bin_ids["bin1"]), None)
            assert bin1['status'] == 'missed'


@freeze_time("2026-02-09 12:00:00")
class TestGetBinsDueOutOnWithSettings:
    """Test get_bins_due_out_on respects put_out_day_before and put_out_time settings."""

    @pytest.fixture(scope="function")
    def setup_bins_due_db(self, db):
        """Set up database for bins due tests."""
        # Create settings with put_out_day_before=True and put_out_time=17:00
        settings = SettingsRepository().create_or_update(schemas.SettingsEdit(
            timeout=120,
            put_out_day_before=True,
            put_out_time="17:00",
            collection_time="09:00"
        ))

        # Create bins
        bin1 = models.Bin(name="Recycling", colour="blue", position=1)
        bin2 = models.Bin(name="Waste", colour="black", position=2)
        bin3 = models.Bin(name="Garden", colour="green", position=3)
        db.add_all([bin1, bin2, bin3])
        db.commit()

        # bin1: tomorrow (Feb 10)
        schedule1 = models.Schedule(
            start=datetime.date(2026, 2, 10),
            repeat_weeks=2,
            bin_id=bin1.id
        )
        # bin2: in 2 weeks (Feb 23)
        schedule2 = models.Schedule(
            start=datetime.date(2026, 2, 23),
            repeat_weeks=2,
            bin_id=bin2.id
        )
        # bin3: tomorrow (Feb 10)
        schedule3 = models.Schedule(
            start=datetime.date(2026, 2, 10),
            repeat_weeks=2,
            bin_id=bin3.id
        )
        db.add_all([schedule1, schedule2, schedule3])
        db.commit()

        bin_ids = {
            "bin1": bin1.id,
            "bin2": bin2.id,
            "bin3": bin3.id,
        }
        return db, bin_ids

    def test_bins_not_due_before_put_out_time(self, client, setup_bins_due_db):
        """Should show tomorrow's bins with 'not_yet_due' status before put_out_time."""
        db, bin_ids = setup_bins_due_db

        # At 12:00 (before 17:00 put_out_time)
        with freeze_time("2026-02-09 12:00:00"):
            scheduler = BinCollectionExplorer(db)
            result = scheduler.get_bins_requiring_action()

            # Should show tomorrow's bins (Feb 10) with 'not_yet_due' status
            assert len(result['bins_to_display']) == 2
            assert result['display_date'] == datetime.date(2026, 2, 10)
            for bin_data in result['bins_to_display']:
                assert bin_data['status'] == 'not_yet_due'

    def test_bins_due_after_put_out_time_with_day_before(self, client, setup_bins_due_db):
        """Should show tomorrow's bins with 'due_out' status after put_out_time when put_out_day_before is True."""
        db, bin_ids = setup_bins_due_db

        # At 18:00 (after 17:00 put_out_time)
        with freeze_time("2026-02-09 18:00:00"):
            scheduler = BinCollectionExplorer(db)
            result = scheduler.get_bins_requiring_action()

            # Should show bin1 and bin3 (scheduled for tomorrow) with 'due_out' status
            assert len(result['bins_to_display']) == 2
            assert result['display_date'] == datetime.date(2026, 2, 10)
            bin_ids_due = [b['bin'].id for b in result['bins_to_display']]
            assert bin_ids["bin1"] in bin_ids_due
            assert bin_ids["bin3"] in bin_ids_due
            assert bin_ids["bin2"] not in bin_ids_due  # bin2 is in 2 weeks
            for bin_data in result['bins_to_display']:
                assert bin_data['status'] == 'due_out'

    def test_bins_due_on_collection_day_with_day_before_disabled(self, client, db):
        """Should show today's bins with 'due_out' status when put_out_day_before is False."""
        # Create settings with put_out_day_before=False
        settings = SettingsRepository().create_or_update(schemas.SettingsEdit(
            timeout=120,
            put_out_day_before=False,
            put_out_time="06:00",  # Put out at 06:00
            collection_time="09:00"  # Collected at 09:00
        ))

        bin1 = models.Bin(name="Recycling", colour="blue", position=1)
        bin2 = models.Bin(name="Waste", colour="black", position=2)
        db.add_all([bin1, bin2])
        db.commit()

        # bin1: today (Feb 9)
        schedule1 = models.Schedule(
            start=datetime.date(2026, 2, 9),
            repeat_weeks=2,
            bin_id=bin1.id
        )
        # bin2: tomorrow (Feb 10)
        schedule2 = models.Schedule(
            start=datetime.date(2026, 2, 10),
            repeat_weeks=2,
            bin_id=bin2.id
        )
        db.add_all([schedule1, schedule2])
        db.commit()

        # At 07:00 on Feb 9 (after 06:00 put_out_time, before 09:00 collection)
        with freeze_time("2026-02-09 07:00:00"):
            scheduler = BinCollectionExplorer(db)
            result = scheduler.get_bins_requiring_action()

            # Should only show bin1 (scheduled today), not bin2 (tomorrow)
            assert len(result['bins_to_display']) == 1
            assert result['display_date'] == datetime.date(2026, 2, 9)
            assert result['bins_to_display'][0]['bin'].id == bin1.id
            assert result['bins_to_display'][0]['status'] == 'due_out'

    def test_bins_due_with_explicit_date(self, client, setup_bins_due_db):
        """Should return bins for explicit date using get_bins_due_out_on."""
        db, bin_ids = setup_bins_due_db

        # Check Feb 10 explicitly (bins are scheduled for Feb 10)
        with freeze_time("2026-02-08 10:00:00"):  # Different day
            scheduler = BinCollectionExplorer(db)
            bins_due = scheduler.get_bins_due_out_on(datetime.date(2026, 2, 10))

            # Should return bin1 and bin3 (scheduled for Feb 10)
            assert len(bins_due) == 2
            bin_ids_due = [b.id for b in bins_due]
            assert bin_ids["bin1"] in bin_ids_due
            assert bin_ids["bin3"] in bin_ids_due

    def test_no_bins_scheduled(self, client, db):
        """Should return empty bins_to_display when no bins are scheduled."""
        settings = SettingsRepository().create_or_update(schemas.SettingsEdit(
            timeout=120,
            put_out_day_before=True,
            put_out_time="17:00",
            collection_time="09:00"
        ))

        bin1 = models.Bin(name="Recycling", colour="blue", position=1)
        db.add(bin1)
        db.commit()

        with freeze_time("2026-02-09 18:00:00"):
            scheduler = BinCollectionExplorer(db)
            result = scheduler.get_bins_requiring_action()

            assert len(result['bins_to_display']) == 0
            assert result['next_collection_date'] is None


