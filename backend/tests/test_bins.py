import sys
from pathlib import Path
from datetime import datetime

root_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(root_dir))

import pytest
from core.database.models import Bin, Schedule
from backend.tests.test_db import db, client


# Helper to create bins
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


def create_bin(client, db, name, position, colour=None):
    bin = Bin(name=name, position=position, colour=colour)
    db.add(bin)
    db.commit()
    db.refresh(bin)
    return bin


def create_schedule(client, db, start, repeat_weeks, bin_id, end=None):
    start_dt = parse_datetime(start)
    end_dt = parse_datetime(end) if end else None
    schedule = Schedule(start=start_dt, repeat_weeks=repeat_weeks, bin_id=bin_id, end=end_dt)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


class TestBinsList:
    def test_list_bins_returns_all_bins(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin_1 = Bin(name="Green Bin", position=1, colour="#ffffff")
        bin_2 = Bin(name="Blue Bin", position=2, colour="#000000")
        db.add(bin_1)
        db.add(bin_2)
        db.commit()
        response = client.get("/bins/?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        # Check pagination structure
        assert set(data.keys()) == {"items", "total", "page", "per_page"}
        assert isinstance(data["items"], list)
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["per_page"] == 10
        # Check items content
        names = [h["name"] for h in data["items"]]
        assert "Green Bin" in names
        assert "Blue Bin" in names
        # Check full item structure
        for item in data["items"]:
            assert set(item.keys()) >= {"id", "name", "position", "colour"}

    def test_list_bins_empty_db(self, client, db):
        db.query(Bin).delete()
        db.commit()
        response = client.get("/api/bins/")
        assert response.status_code == 200
        assert response.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "per_page": 10
        }

class TestBinsPagination:
    def test_bins_pagination(self, client, db):
        db.query(Bin).delete()
        db.commit()
        for i in range(5):
            create_bin(client, db, f"Bin{i+1}", i+1)
        response = client.get("/bins/?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_bins_pagination_correct_bins(self, client, db):
        db.query(Bin).delete()
        db.commit()
        for i in range(6):
            create_bin(client, db, f"Bin{i+1}", i+1)
        # Page 1, per_page=4
        response1 = client.get("/bins/?page=1&per_page=4")
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["page"] == 1
        assert data1["per_page"] == 4
        assert data1["total"] == 6
        assert len(data1["items"]) == 4
        names1 = [item["name"] for item in data1["items"]]
        assert names1 == ["Bin1", "Bin2", "Bin3", "Bin4"]
        # Page 2, per_page=4
        response2 = client.get("/bins/?page=2&per_page=4")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["page"] == 2
        assert data2["per_page"] == 4
        assert data2["total"] == 6
        assert len(data2["items"]) == 2
        names2 = [item["name"] for item in data2["items"]]
        assert names2 == ["Bin5", "Bin6"]

    def test_bins_pagination_page_too_late(self, client, db):
        db.query(Bin).delete()
        db.commit()
        for i in range(6):
            create_bin(client, db, f"Bin{i+1}", i+1)
        # Page 3, per_page=4, only 6 bins
        response = client.get("/bins/?page=3&per_page=4")
        assert response.status_code in (400, 422)

class TestBinsGet:
    def test_get_bin_by_id_success(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, "BinA", 1)
        response = client.get(f"/bins/{bin.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "BinA"

    def test_get_bin_by_id_404(self, client, db):
        db.query(Bin).delete()
        db.commit()
        response = client.get("/bins/999")
        assert response.status_code == 404

class TestBinsCreate:
    def test_create_bin_success(self, client, db):
        db.query(Bin).delete()
        db.commit()
        response = client.post("/bins/", json={"name": "BinX", "colour": "#123456"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "BinX"
        assert data["position"] == 1
        assert data["colour"] == "#123456"

        response = client.post("/bins/", json={"name": "BinX-2", "colour": "#789101"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "BinX-2"
        assert data["position"] == 2
        assert data["colour"] == "#789101"

    def test_create_bin_without_colour(self, client, db):
        response = client.post("/bins/", json={"name": "BinY"})
        assert response.status_code == 200

    def test_create_bin_invalid(self, client, db):
        response = client.post("/bins/", json={"colour": "#000fff"})
        assert response.status_code == 422

class TestBinsMoveEarlier:
    def test_move_bin_earlier_success(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin1 = create_bin(client, db, "Bin1", 1)
        bin2 = create_bin(client, db, "Bin2", 2)
        response = client.post(f"/bins/{bin2.id}/move-earlier")
        assert response.status_code == 200
        assert response.json()["position"] == 1
        # Check the database
        db_bin2 = db.query(Bin).filter(Bin.id == bin2.id).first()
        assert db_bin2.position == 1
        db_bin1 = db.query(Bin).filter(Bin.id == bin1.id).first()
        assert db_bin1.position == 2

    def test_move_bin_earlier_edge(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin1 = create_bin(client, db, "Bin1", 1)
        response = client.post(f"/bins/{bin1.id}/move-earlier")
        assert response.status_code == 400

    def test_move_bin_earlier_404(self, client, db):
        response = client.post("/bins/999/move-earlier")
        assert response.status_code == 400

class TestBinsMoveLater:
    def test_move_bin_later_success(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin1 = create_bin(client, db, "Bin1", 1)
        bin2 = create_bin(client, db, "Bin2", 2)
        response = client.post(f"/bins/{bin1.id}/move-later")
        assert response.status_code == 200
        assert response.json()["position"] == 2

        db_bin2 = db.query(Bin).filter(Bin.id == bin2.id).first()
        assert db_bin2.position == 1
        db_bin1 = db.query(Bin).filter(Bin.id == bin1.id).first()
        assert db_bin1.position == 2

    def test_move_bin_later_edge(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin1 = create_bin(client, db, "Bin1", 1)
        response = client.post(f"/bins/{bin1.id}/move-later")
        assert response.status_code == 400

class TestBinsSetPosition:
    def test_set_bin_position_success(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin1 = create_bin(client, db, "Bin1", 1)
        bin2 = create_bin(client, db, "Bin2", 2)
        response = client.post(f"/bins/{bin1.id}/set-position?position=2")
        assert response.status_code == 200
        assert response.json()["position"] == 2

    def test_set_bin_position_invalid(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin1 = create_bin(client, db, "Bin1", 1)
        response = client.post(f"/bins/{bin1.id}/set-position?position=0")
        assert response.status_code == 422 or response.status_code == 400

    def test_set_bin_position_404(self, client, db):
        response = client.post("/bins/999/set-position?position=1")
        assert response.status_code == 400

class TestBinsEdit:
    def test_edit_bin_success(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin1 = create_bin(client, db, "Bin1", 1, "#ff0000")
        response = client.patch(f"/bins/{bin1.id}", json={"name": "BinRenamed", "colour": "#00ff00"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "BinRenamed"
        assert data["colour"] == "#00ff00"

    def test_edit_bin_404(self, client, db):
        response = client.patch("/bins/999", json={"name": "X"})
        assert response.status_code == 404

    def test_edit_bin_empty_payload(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin1 = create_bin(client, db, "Bin1", 1, "#ff0000")
        response = client.patch(f"/bins/{bin1.id}", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Bin1"
        assert data["colour"] == "#ff0000"

    def test_edit_bin_invalid_types(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin1 = create_bin(client, db, "Bin1", 1, "#ff0000")
        response = client.patch(f"/bins/{bin1.id}", json={"name": 123, "colour": 456})
        assert response.status_code == 422

    def test_edit_bin_null_values(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin1 = create_bin(client, db, "Bin1", 1, "#ff0000")
        response = client.patch(f"/bins/{bin1.id}", json={"name": None, "colour": None})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Bin1"
        assert data["colour"] == "#ff0000"

    def test_edit_bin_partial_update_name(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin1 = create_bin(client, db, "Bin1", 1, "#ff0000")
        response = client.patch(f"/bins/{bin1.id}", json={"name": "NewName"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NewName"
        assert data["colour"] == "#ff0000"

    def test_edit_bin_partial_update_colour(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin1 = create_bin(client, db, "Bin1", 1, "#ff0000")
        response = client.patch(f"/bins/{bin1.id}", json={"colour": "#00ff00"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Bin1"
        assert data["colour"] == "#00ff00"

class TestBinsDelete:
    def test_delete_bin_success(self, client, db):
        db.query(Bin).delete()
        db.commit()
        bin1 = create_bin(client, db, "Bin1", 1)
        response = client.delete(f"/bins/{bin1.id}")
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_delete_bin_404(self, client, db):
        response = client.delete("/bins/999")
        assert response.status_code == 404

    def test_schedules_deleted_with_bin(self, client, db):
        db.query(Schedule).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, name="TestBin", position=1)
        sched1 = create_schedule(client, db, "2024-01-01", 2, bin.id)
        sched2 = create_schedule(client, db, "2024-02-01", 3, bin.id)
        # Confirm schedules exist
        assert db.query(Schedule).filter(Schedule.bin_id == bin.id).count() == 2
        # Delete the bin
        response = client.delete(f"/bins/{bin.id}")
        assert response.status_code == 200
        # Schedules should be deleted
        assert db.query(Schedule).filter(Schedule.bin_id == bin.id).count() == 0
