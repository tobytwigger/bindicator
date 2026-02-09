import sys
from pathlib import Path
from datetime import datetime

root_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(root_dir))

import pytest
from core.database.models import Bin, BinPutOut
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


def create_bin_put_out(client, db, bin_id, date_put_out_at):
    date_dt = parse_datetime(date_put_out_at)
    put_out = BinPutOut(bin_id=bin_id, date_put_out_at=date_dt)
    db.add(put_out)
    db.commit()
    db.refresh(put_out)
    return put_out


class TestBinPutOutsList:
    def test_list_bin_put_outs_returns_all(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin_1 = create_bin(client, db, "Green Bin", 1)
        bin_2 = create_bin(client, db, "Blue Bin", 2)
        put_out_1 = create_bin_put_out(client, db, bin_1.id, "2024-01-01")
        put_out_2 = create_bin_put_out(client, db, bin_2.id, "2024-01-02")
        response = client.get("/bin-put-outs/?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        # Check pagination structure
        assert set(data.keys()) == {"items", "total", "page", "per_page"}
        assert isinstance(data["items"], list)
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["per_page"] == 10
        # Check items content
        ids = [item["id"] for item in data["items"]]
        assert put_out_1.id in ids
        assert put_out_2.id in ids
        # Check full item structure
        for item in data["items"]:
            assert set(item.keys()) >= {"id", "bin_id", "date_put_out_at", "created_at", "updated_at"}

    def test_list_bin_put_outs_empty_db(self, client, db):
        db.query(BinPutOut).delete()
        db.commit()
        response = client.get("/bin-put-outs/")
        assert response.status_code == 200
        assert response.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "per_page": 10
        }

    def test_list_bin_put_outs_ordered_by_date_desc(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, "Green Bin", 1)
        put_out_1 = create_bin_put_out(client, db, bin.id, "2024-01-01")
        put_out_2 = create_bin_put_out(client, db, bin.id, "2024-01-05")
        put_out_3 = create_bin_put_out(client, db, bin.id, "2024-01-03")
        response = client.get("/bin-put-outs/?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        ids = [item["id"] for item in data["items"]]
        # Should be ordered by date descending (most recent first)
        assert ids == [put_out_2.id, put_out_3.id, put_out_1.id]


class TestBinPutOutsPagination:
    def test_bin_put_outs_pagination(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, "Bin1", 1)
        for i in range(5):
            create_bin_put_out(client, db, bin.id, f"2024-01-0{i+1}")
        response = client.get("/bin-put-outs/?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_bin_put_outs_pagination_correct_items(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, "Bin1", 1)
        ids = []
        for i in range(6):
            put_out = create_bin_put_out(client, db, bin.id, f"2024-01-0{i+1}")
            ids.append(put_out.id)
        # Page 1, per_page=4
        response1 = client.get("/bin-put-outs/?page=1&per_page=4")
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["page"] == 1
        assert data1["per_page"] == 4
        assert data1["total"] == 6
        assert len(data1["items"]) == 4
        # Page 2, per_page=4
        response2 = client.get("/bin-put-outs/?page=2&per_page=4")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["page"] == 2
        assert data2["per_page"] == 4
        assert data2["total"] == 6
        assert len(data2["items"]) == 2

    def test_bin_put_outs_pagination_page_too_late(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, "Bin1", 1)
        for i in range(6):
            create_bin_put_out(client, db, bin.id, f"2024-01-0{i+1}")
        # Page 3, per_page=4, only 6 put outs
        response = client.get("/bin-put-outs/?page=3&per_page=4")
        assert response.status_code in (400, 422)


class TestBinPutOutsGet:
    def test_get_bin_put_out_by_id_success(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, "BinA", 1)
        bin_id = bin.id  # Store id before session closes
        put_out = create_bin_put_out(client, db, bin_id, "2024-01-01")
        put_out_id = put_out.id  # Store id before session closes
        response = client.get(f"/bin-put-outs/{put_out_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == put_out_id
        assert data["bin_id"] == bin_id
        assert data["date_put_out_at"].startswith("2024-01-01")

    def test_get_bin_put_out_by_id_404(self, client, db):
        db.query(BinPutOut).delete()
        db.commit()
        response = client.get("/bin-put-outs/999")
        assert response.status_code == 404


class TestBinPutOutsByDate:
    def test_get_bin_put_outs_by_date_success(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin_1 = create_bin(client, db, "Green Bin", 1)
        bin_2 = create_bin(client, db, "Blue Bin", 2)
        put_out_1 = create_bin_put_out(client, db, bin_1.id, "2024-01-01")
        put_out_2 = create_bin_put_out(client, db, bin_2.id, "2024-01-01")
        put_out_3 = create_bin_put_out(client, db, bin_1.id, "2024-01-02")

        response = client.get("/bin-put-outs/by-date?date=2024-01-01")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        ids = [item["id"] for item in data]
        assert put_out_1.id in ids
        assert put_out_2.id in ids
        assert put_out_3.id not in ids

    def test_get_bin_put_outs_by_date_no_results(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, "Green Bin", 1)
        create_bin_put_out(client, db, bin.id, "2024-01-01")

        response = client.get("/bin-put-outs/by-date?date=2024-01-02")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_bin_put_outs_by_date_invalid_format(self, client, db):
        response = client.get("/bin-put-outs/by-date?date=invalid-date")
        assert response.status_code == 400

    def test_get_bin_put_outs_by_date_missing_param(self, client, db):
        response = client.get("/bin-put-outs/by-date")
        assert response.status_code == 422


class TestBinPutOutsCreate:
    def test_create_bin_put_out_success(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, "BinX", 1)
        bin_id = bin.id  # Store id before session closes
        response = client.post("/bin-put-outs/", json={
            "bin_id": bin_id,
            "date_put_out_at": "2024-01-01"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["bin_id"] == bin_id
        assert data["date_put_out_at"].startswith("2024-01-01")
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_bin_put_out_with_datetime(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, "BinX", 1)
        bin_id = bin.id  # Store id before session closes
        response = client.post("/bin-put-outs/", json={
            "bin_id": bin_id,
            "date_put_out_at": "2024-01-01T10:30:00"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["bin_id"] == bin_id
        assert data["date_put_out_at"].startswith("2024-01-01")

    def test_create_bin_put_out_invalid_bin_id(self, client, db):
        response = client.post("/bin-put-outs/", json={
            "bin_id": 99999,
            "date_put_out_at": "2024-01-01"
        })
        assert response.status_code == 404
        assert "Bin not found" in response.json()["detail"]

    def test_create_bin_put_out_missing_fields(self, client, db):
        response = client.post("/bin-put-outs/", json={
            "bin_id": 1
        })
        assert response.status_code == 422

    def test_create_bin_put_out_invalid_date(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, "BinX", 1)
        response = client.post("/bin-put-outs/", json={
            "bin_id": bin.id,
            "date_put_out_at": "invalid-date"
        })
        assert response.status_code == 422


class TestBinPutOutsDelete:
    def test_delete_bin_put_out_success(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, "Bin1", 1)
        put_out = create_bin_put_out(client, db, bin.id, "2024-01-01")
        response = client.delete(f"/bin-put-outs/{put_out.id}")
        assert response.status_code == 204
        # Verify deleted
        assert db.query(BinPutOut).filter(BinPutOut.id == put_out.id).first() is None

    def test_delete_bin_put_out_404(self, client, db):
        response = client.delete("/bin-put-outs/999")
        assert response.status_code == 404


class TestBinPutOutsCascadeDelete:
    def test_bin_put_outs_deleted_with_bin(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, "TestBin", 1)
        put_out_1 = create_bin_put_out(client, db, bin.id, "2024-01-01")
        put_out_2 = create_bin_put_out(client, db, bin.id, "2024-01-02")
        # Confirm put_outs exist
        assert db.query(BinPutOut).filter(BinPutOut.bin_id == bin.id).count() == 2
        # Delete the bin
        response = client.delete(f"/bins/{bin.id}")
        assert response.status_code == 204
        # Put outs should be deleted
        assert db.query(BinPutOut).filter(BinPutOut.bin_id == bin.id).count() == 0


class TestBinPutOutsForeignKey:
    def test_cannot_create_put_out_for_nonexistent_bin(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        response = client.post("/bin-put-outs/", json={
            "bin_id": 99999,
            "date_put_out_at": "2024-01-01"
        })
        assert response.status_code == 404
        assert "Bin not found" in response.json()["detail"]

    def test_multiple_put_outs_same_bin(self, client, db):
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, "Bin1", 1)
        put_out_1 = create_bin_put_out(client, db, bin.id, "2024-01-01")
        put_out_2 = create_bin_put_out(client, db, bin.id, "2024-01-02")
        put_out_3 = create_bin_put_out(client, db, bin.id, "2024-01-03")

        assert db.query(BinPutOut).filter(BinPutOut.bin_id == bin.id).count() == 3

    def test_same_bin_same_date_multiple_records(self, client, db):
        """Test that the system allows multiple records for the same bin on the same date."""
        db.query(BinPutOut).delete()
        db.query(Bin).delete()
        db.commit()
        bin = create_bin(client, db, "Bin1", 1)
        bin_id = bin.id  # Store id before session closes
        # Create two put out records for the same bin on the same date
        put_out_1 = create_bin_put_out(client, db, bin_id, "2024-01-01")
        put_out_2 = create_bin_put_out(client, db, bin_id, "2024-01-01")

        # Both should exist
        target_datetime = parse_datetime("2024-01-01")
        assert db.query(BinPutOut).filter(
            BinPutOut.bin_id == bin_id,
            BinPutOut.date_put_out_at == target_datetime
        ).count() == 2
