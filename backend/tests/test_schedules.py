import sys
from pathlib import Path
from datetime import datetime

from freezegun import freeze_time

root_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(root_dir))

from core.database.models import Schedule, Bin, BinDayReplacement
from backend.tests.test_db import db, client

# Helper to create a bin (since schedule requires bin_id)
def create_bin(client, db, name="TestBin", position=1, colour=None):
    bin = Bin(name=name, position=position, colour=colour)
    db.add(bin)
    db.commit()
    db.refresh(bin)
    return bin

def parse_datetime(value):
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

# Helper to create a schedule
def create_schedule(client, db, start, repeat_weeks, bin_id, end=None):
    start_dt = parse_datetime(start)
    end_dt = parse_datetime(end) if end else None
    schedule = Schedule(start=start_dt, repeat_weeks=repeat_weeks, bin_id=bin_id, end=end_dt)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule

# Helper to create a bin day replacement
def create_replacement(client, db, replace, replace_with):
    replace_dt = parse_datetime(replace)
    replace_with_dt = parse_datetime(replace_with)
    replacement = BinDayReplacement(replace=replace_dt, replace_with=replace_with_dt)
    db.add(replacement)
    db.commit()
    db.refresh(replacement)
    return replacement

@freeze_time("2026-01-01 12:00:00")
class TestSchedulesList:
    def test_list_schedules_returns_all(self, client, db):
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db)
        sched1 = create_schedule(client, db, "2024-01-01", 2, bin.id)
        sched2 = create_schedule(client, db, "2024-02-01", 3, bin.id)
        response = client.get("/schedules/?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"items", "total", "page", "per_page"}
        assert isinstance(data["items"], list)
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["per_page"] == 10
        ids = [item["id"] for item in data["items"]]
        assert sched1.id in ids and sched2.id in ids

    def test_list_schedules_empty(self, client, db):
        db.query(Schedule).delete()
        db.commit()
        response = client.get("/schedules/?page=1&per_page=10")
        assert response.status_code == 200
        assert response.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "per_page": 10
        }

    def test_schedules_pagination(self, client, db):
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db)
        for i in range(5):
            create_schedule(client, db, f"2024-01-0{i+1}", i+1, bin.id)
        response = client.get("/schedules/?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_schedules_pagination_correct_items(self, client, db):
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db)
        ids = []
        for i in range(6):
            sched = create_schedule(client, db, f"2024-01-0{i+1}", i+1, bin.id)
            ids.append(sched.id)
        # Page 1, per_page=4
        response1 = client.get("/schedules/?page=1&per_page=4")
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["page"] == 1
        assert data1["per_page"] == 4
        assert data1["total"] == 6
        assert len(data1["items"]) == 4
        # Page 2, per_page=4
        response2 = client.get("/schedules/?page=2&per_page=4")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["page"] == 2
        assert data2["per_page"] == 4
        assert data2["total"] == 6
        assert len(data2["items"]) == 2

    def test_schedules_pagination_page_too_late(self, client, db):
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db)
        for i in range(6):
            create_schedule(client, db, f"2024-01-0{i+1}", i+1, bin.id)
        response = client.get("/schedules/?page=3&per_page=4")
        assert response.status_code in (400, 422)

@freeze_time("2026-01-01 12:00:00")
class TestSchedulesGet:
    def test_get_schedule_by_id_success(self, client, db):
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db)
        bin_id = bin.id  # Store id before session closes
        sched = create_schedule(client, db, "2024-01-01", 2, bin_id)
        response = client.get(f"/schedules/{sched.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sched.id
        assert data["start"].startswith("2024-01-01")
        assert data["repeat_weeks"] == 2
        assert data["bin_id"] == bin_id

    def test_get_schedule_by_id_404(self, client, db):
        db.query(Schedule).delete()
        db.commit()
        response = client.get("/schedules/99999")
        assert response.status_code == 404

@freeze_time("2026-01-01 12:00:00")
class TestSchedulesCreate:
    def test_create_schedule_success(self, client, db):
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db)
        bin_id = bin.id  # Store id before session closes
        payload = {"start": "2024-01-01", "repeat_weeks": 2, "bin_id": bin_id}
        response = client.post("/schedules/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["start"].startswith("2024-01-01")
        assert data["repeat_weeks"] == 2
        assert data["bin_id"] == bin_id
        assert data["end"] is None

    def test_create_schedule_with_end(self, client, db):
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db)
        payload = {"start": "2024-01-01", "repeat_weeks": 2, "bin_id": bin.id, "end": "2024-12-31"}
        response = client.post("/schedules/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["end"].startswith("2024-12-31")

    def test_create_schedule_invalid_missing_fields(self, client, db):
        response = client.post("/schedules/", json={"start": "2024-01-01"})
        assert response.status_code == 422

    def test_create_schedule_invalid_bin(self, client, db):
        payload = {"start": "2024-01-01", "repeat_weeks": 2, "bin_id": 99999}
        response = client.post("/schedules/", json=payload)
        assert response.status_code in (400, 404)

@freeze_time("2026-01-01 12:00:00")
class TestSchedulesUpdate:
    def test_update_schedule_success(self, client, db):
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db)
        bin_id = bin.id  # Store id before session closes
        sched = create_schedule(client, db, "2024-01-01", 2, bin_id)
        payload = {"start": "2024-02-01", "repeat_weeks": 3, "end": "2024-12-31", "bin_id": bin_id}
        response = client.patch(f"/schedules/{sched.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["start"].startswith("2024-02-01")
        assert data["repeat_weeks"] == 3
        assert data["end"].startswith("2024-12-31")
        assert data["bin_id"] == bin_id

    def test_update_schedule_not_found(self, client, db):
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db)
        bin_id = bin.id
        payload = {"start": "2024-02-01", "repeat_weeks": 3, "end": "2024-12-31", "bin_id": bin_id}
        response = client.patch("/schedules/99999", json=payload)
        assert response.status_code == 404

    def test_update_schedule_invalid(self, client, db):
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db)
        bin_id = bin.id
        sched = create_schedule(client, db, "2024-01-01", 2, bin_id)
        payload = {"start": 123, "repeat_weeks": "bad"}
        response = client.patch(f"/schedules/{sched.id}", json=payload)
        assert response.status_code == 422

@freeze_time("2026-01-01 12:00:00")
class TestSchedulesDelete:
    def test_delete_schedule_success(self, client, db):
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db)
        sched = create_schedule(client, db, "2024-01-01", 2, bin.id)
        response = client.delete(f"/schedules/{sched.id}")
        assert response.status_code == 204
        # Confirm schedule is gone
        response2 = client.get(f"/schedules/{sched.id}")
        assert response2.status_code == 404

    def test_delete_schedule_not_found(self, client, db):
        db.query(Schedule).delete()
        db.commit()
        response = client.delete("/schedules/99999")
        assert response.status_code == 404

    def test_bin_persists_after_schedule_deleted(self, client, db):
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db)
        bin_id = bin.id  # Store ID before session closes
        sched = create_schedule(client, db, "2024-01-01", 2, bin_id)
        response = client.delete(f"/schedules/{sched.id}")
        assert response.status_code == 204
        # Bin should still exist, fetch via API
        response2 = client.get(f"/bins/{bin_id}")
        assert response2.status_code == 200
        data = response2.json()
        assert data["id"] == bin_id


@freeze_time("2026-01-01 12:00:00")
class TestCalendar:
    def test_returns_all_scheduled_bins_between_the_given_dates(self, client, db):
        """Test that all scheduled bins are returned within the date range"""
        db.query(BinDayReplacement).delete()
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()

        # Create a bin with weekly schedule starting Feb 3, 2026 (Tuesday)
        bin1 = create_bin(client, db, name="General Waste", colour="#444444")
        create_schedule(client, db, "2026-02-03", 1, bin1.id)

        # Request Feb 2026 (should have 4 Tuesdays: 3, 10, 17, 24)
        response = client.get("/schedules/calendar?start=2026-02-01&end=2026-02-28")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert data[0]["date"] == "2026-02-03"
        assert data[1]["date"] == "2026-02-10"
        assert data[2]["date"] == "2026-02-17"
        assert data[3]["date"] == "2026-02-24"

        for item in data:
            assert len(item["bins"]) == 1
            assert item["bins"][0]["name"] == "General Waste"
            assert item["bins"][0]["colour"] == "#444444"

    def test_returns_empty_if_no_schedules(self, client, db):
        """Test that empty array is returned when no schedules exist"""
        db.query(BinDayReplacement).delete()
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()

        response = client.get("/schedules/calendar?start=2026-02-01&end=2026-02-28")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_returns_empty_if_no_bins_scheduled_between_the_given_dates(self, client, db):
        """Test that empty array is returned when schedules exist but not in date range"""
        db.query(BinDayReplacement).delete()
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()

        # Create a schedule for March 2026
        bin1 = create_bin(client, db, name="General Waste")
        create_schedule(client, db, "2026-03-01", 1, bin1.id)

        # Request February 2026
        response = client.get("/schedules/calendar?start=2026-02-01&end=2026-02-28")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_handles_a_single_bin(self, client, db):
        """Test that a single bin is correctly returned"""
        db.query(BinDayReplacement).delete()
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()

        bin1 = create_bin(client, db, name="Recycling", colour="#2ecc40")
        create_schedule(client, db, "2026-02-10", 2, bin1.id)  # Bi-weekly

        # Request Feb 2026 (should have 2 dates: 10, 24)
        response = client.get("/schedules/calendar?start=2026-02-01&end=2026-02-28")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["date"] == "2026-02-10"
        assert data[1]["date"] == "2026-02-24"

        for item in data:
            assert len(item["bins"]) == 1
            assert item["bins"][0]["id"] == bin1.id
            assert item["bins"][0]["name"] == "Recycling"
            assert item["bins"][0]["colour"] == "#2ecc40"

    def test_handles_multiple_bins(self, client, db):
        """Test that multiple bins on the same date are correctly grouped"""
        db.query(BinDayReplacement).delete()
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()

        # Create two bins with same schedule date
        bin1 = create_bin(client, db, name="Recycling", position=1, colour="#2ecc40")
        bin2 = create_bin(client, db, name="Garden Waste", position=2, colour="#ffdc00")

        # Both start on same date, Feb 10, 2026
        create_schedule(client, db, "2026-02-10", 2, bin1.id)
        create_schedule(client, db, "2026-02-10", 2, bin2.id)

        response = client.get("/schedules/calendar?start=2026-02-01&end=2026-02-28")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Feb 10 and Feb 24

        # Check first date has both bins
        assert data[0]["date"] == "2026-02-10"
        assert len(data[0]["bins"]) == 2
        bin_names = [b["name"] for b in data[0]["bins"]]
        assert "Recycling" in bin_names
        assert "Garden Waste" in bin_names

        # Check second date has both bins
        assert data[1]["date"] == "2026-02-24"
        assert len(data[1]["bins"]) == 2

    def test_handles_different_repeat_intervals(self, client, db):
        """Test bins with different repeat intervals (weekly vs bi-weekly)"""
        db.query(BinDayReplacement).delete()
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()

        bin1 = create_bin(client, db, name="General Waste", position=1)
        bin2 = create_bin(client, db, name="Recycling", position=2)

        # General waste weekly from Feb 3
        create_schedule(client, db, "2026-02-03", 1, bin1.id)
        # Recycling bi-weekly from Feb 10
        create_schedule(client, db, "2026-02-10", 2, bin2.id)

        response = client.get("/schedules/calendar?start=2026-02-01&end=2026-02-28")

        assert response.status_code == 200
        data = response.json()

        # Feb 3, 10, 17, 24 - general waste
        # Feb 10, 24 - recycling
        # Should have 5 dates total (3, 10, 17, 24 with general, 10 and 24 with both)
        dates_dict = {item["date"]: item["bins"] for item in data}

        assert "2026-02-03" in dates_dict
        assert len(dates_dict["2026-02-03"]) == 1
        assert dates_dict["2026-02-03"][0]["name"] == "General Waste"

        assert "2026-02-10" in dates_dict
        assert len(dates_dict["2026-02-10"]) == 2  # Both bins

        assert "2026-02-17" in dates_dict
        assert len(dates_dict["2026-02-17"]) == 1
        assert dates_dict["2026-02-17"][0]["name"] == "General Waste"

        assert "2026-02-24" in dates_dict
        assert len(dates_dict["2026-02-24"]) == 2  # Both bins

    def test_schedule_with_end_date(self, client, db):
        """Test that schedules stop after their end date"""
        db.query(BinDayReplacement).delete()
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()

        bin1 = create_bin(client, db, name="General Waste")
        # Schedule ends on Feb 15
        create_schedule(client, db, "2026-02-03", 1, bin1.id, end="2026-02-15")

        response = client.get("/schedules/calendar?start=2026-02-01&end=2026-02-28")

        assert response.status_code == 200
        data = response.json()

        # Should only have Feb 3 and Feb 10 (not 17, 24 as schedule ends on 15th)
        assert len(data) == 2
        assert data[0]["date"] == "2026-02-03"
        assert data[1]["date"] == "2026-02-10"

    def test_bin_day_replacement_moves_collection(self, client, db):
        """Test that bin day replacements move collections correctly"""
        db.query(BinDayReplacement).delete()
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()

        bin1 = create_bin(client, db, name="General Waste")
        create_schedule(client, db, "2026-02-03", 1, bin1.id)  # Weekly on Tuesdays

        # Move Feb 10 collection to Feb 11 (holiday)
        create_replacement(client, db, "2026-02-10", "2026-02-11")

        response = client.get("/schedules/calendar?start=2026-02-01&end=2026-02-28")

        assert response.status_code == 200
        data = response.json()

        dates = [item["date"] for item in data]

        # Should have Feb 3, 11 (not 10), 17, 24
        assert "2026-02-03" in dates
        assert "2026-02-10" not in dates  # Moved away
        assert "2026-02-11" in dates  # Moved to
        assert "2026-02-17" in dates
        assert "2026-02-24" in dates

    def test_multiple_replacements(self, client, db):
        """Test multiple bin day replacements"""
        db.query(BinDayReplacement).delete()
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()

        bin1 = create_bin(client, db, name="General Waste")
        create_schedule(client, db, "2026-02-03", 1, bin1.id)

        # Move two collections
        create_replacement(client, db, "2026-02-10", "2026-02-11")
        create_replacement(client, db, "2026-02-17", "2026-02-18")

        response = client.get("/schedules/calendar?start=2026-02-01&end=2026-02-28")

        assert response.status_code == 200
        data = response.json()

        dates = [item["date"] for item in data]

        assert "2026-02-03" in dates
        assert "2026-02-10" not in dates
        assert "2026-02-11" in dates
        assert "2026-02-17" not in dates
        assert "2026-02-18" in dates
        assert "2026-02-24" in dates

    def test_replacement_outside_range(self, client, db):
        """Test that replacement moving date outside range is handled correctly"""
        db.query(BinDayReplacement).delete()
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()

        bin1 = create_bin(client, db, name="General Waste")
        create_schedule(client, db, "2026-02-24", 1, bin1.id)  # Weekly from Feb 24

        # Move Feb 24 to March 3 (outside February range)
        create_replacement(client, db, "2026-02-24", "2026-03-03")

        response = client.get("/schedules/calendar?start=2026-02-01&end=2026-02-28")

        assert response.status_code == 200
        data = response.json()

        # Feb 24 should not appear in February results
        dates = [item["date"] for item in data]
        assert "2026-02-24" not in dates

    def test_deduplicates_same_bin_on_same_date(self, client, db):
        """Test that multiple schedules for same bin on same date only show once"""
        db.query(BinDayReplacement).delete()
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()

        bin1 = create_bin(client, db, name="General Waste")
        # Create two schedules that result in same date (edge case)
        create_schedule(client, db, "2026-02-10", 2, bin1.id)
        create_schedule(client, db, "2026-02-10", 4, bin1.id)  # Also on Feb 10

        response = client.get("/schedules/calendar?start=2026-02-01&end=2026-02-28")

        assert response.status_code == 200
        data = response.json()

        # Find Feb 10
        feb_10 = next((item for item in data if item["date"] == "2026-02-10"), None)
        assert feb_10 is not None

        # Should only have 1 bin entry (deduplicated)
        assert len(feb_10["bins"]) == 1
        assert feb_10["bins"][0]["id"] == bin1.id

    def test_invalid_date_format(self, client, db):
        """Test that invalid date format returns 400 error"""
        response = client.get("/schedules/calendar?start=2026-02-01&end=invalid-date")

        assert response.status_code == 400
        assert "Invalid date format" in response.json()["detail"]

    def test_start_after_end(self, client, db):
        """Test that start date after end date returns 400 error"""
        response = client.get("/schedules/calendar?start=2026-02-28&end=2026-02-01")

        assert response.status_code == 400
        assert "Start date must be before or equal to end date" in response.json()["detail"]

    def test_missing_parameters(self, client, db):
        """Test that missing required parameters returns 422 error"""
        response = client.get("/schedules/calendar?start=2026-02-01")

        assert response.status_code == 422  # Missing 'end' parameter

    def test_partial_schedule_overlap(self, client, db):
        """Test schedule that starts within the requested range"""
        db.query(BinDayReplacement).delete()
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()

        bin1 = create_bin(client, db, name="General Waste")
        # Schedule starts on Feb 15
        create_schedule(client, db, "2026-02-15", 1, bin1.id)

        response = client.get("/schedules/calendar?start=2026-02-01&end=2026-02-28")

        assert response.status_code == 200
        data = response.json()

        dates = [item["date"] for item in data]

        # Should only have dates from Feb 15 onwards (15, 22)
        assert "2026-02-15" in dates
        assert "2026-02-22" in dates
        assert len(data) == 2
