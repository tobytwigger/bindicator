import sys
from pathlib import Path
from datetime import datetime

root_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(root_dir))

from core.database.models import Schedule, Bin
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
