import sys
from pathlib import Path
from datetime import datetime

root_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(root_dir))

from core.database.models import BinDayReplacement
from backend.tests.test_db import db, client

# Helper to create a BinDayReplacement

def create_bin_day_replacement(client, db, replace, replace_with):
    # Convert string to datetime if necessary
    if isinstance(replace, str):
        replace = datetime.strptime(replace, "%Y-%m-%d")
    if isinstance(replace_with, str):
        replace_with = datetime.strptime(replace_with, "%Y-%m-%d")
    replacement = BinDayReplacement(replace=replace, replace_with=replace_with)
    db.add(replacement)
    db.commit()
    db.refresh(replacement)
    return replacement

class TestBinDayReplacementList:
    def test_returns_all(self, client, db):
        db.query(BinDayReplacement).delete()
        db.commit()
        rep1 = create_bin_day_replacement(client, db, "2024-01-01", "2024-01-02")
        rep2 = create_bin_day_replacement(client, db, "2024-02-01", "2024-02-02")
        response = client.get("/bin_day_replacements/?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"items", "total", "page", "per_page"}
        assert isinstance(data["items"], list)
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["per_page"] == 10
        ids = [item["id"] for item in data["items"]]
        assert rep1.id in ids and rep2.id in ids

    def test_empty(self, client, db):
        db.query(BinDayReplacement).delete()
        db.commit()
        response = client.get("/bin_day_replacements/?page=1&per_page=10")
        assert response.status_code == 200
        assert response.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "per_page": 10
        }

    def test_pagination(self, client, db):
        db.query(BinDayReplacement).delete()
        db.commit()
        for i in range(5):
            create_bin_day_replacement(client, db, f"2024-01-0{i+1}", f"2024-01-1{i+1}")
        response = client.get("/bin_day_replacements/?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_page_out_of_range(self, client, db):
        db.query(BinDayReplacement).delete()
        db.commit()
        response = client.get("/bin_day_replacements/?page=100&per_page=10")
        assert response.status_code == 400
        assert response.json()["detail"] == "Page out of range"

    def test_invalid_page(self, client, db):
        response = client.get("/bin_day_replacements/?page=0&per_page=10")
        assert response.status_code == 422

    def test_invalid_per_page(self, client, db):
        response = client.get("/bin_day_replacements/?page=1&per_page=0")
        assert response.status_code == 422

class TestBinDayReplacementCreate:
    def test_create(self, client, db):
        db.query(BinDayReplacement).delete()
        db.commit()
        payload = {"replace": "2024-01-01T00:00:00", "replace_with": "2024-01-02T00:00:00"}
        response = client.post("/bin_day_replacements/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["replace"] == payload["replace"]
        assert data["replace_with"] == payload["replace_with"]
        assert "id" in data

    def test_missing_both_parameters(self, client, db):
        response = client.post("/bin_day_replacements/", json={})
        assert response.status_code == 422

    def test_missing_replace(self, client, db):
        payload = {"replace_with": "2024-01-02T00:00:00"}
        response = client.post("/bin_day_replacements/", json=payload)
        assert response.status_code == 422

    def test_missing_replace_with(self, client, db):
        payload = {"replace": "2024-01-01T00:00:00"}
        response = client.post("/bin_day_replacements/", json=payload)
        assert response.status_code == 422

    def test_invalid_datetime_format(self, client, db):
        payload = {"replace": "not-a-date", "replace_with": "2024-01-02T00:00:00"}
        response = client.post("/bin_day_replacements/", json=payload)
        assert response.status_code == 422
        payload = {"replace": "2024-01-01T00:00:00", "replace_with": "not-a-date"}
        response = client.post("/bin_day_replacements/", json=payload)
        assert response.status_code == 422

class TestBinDayReplacementGet:
    def test_get(self, client, db):
        db.query(BinDayReplacement).delete()
        db.commit()
        rep = create_bin_day_replacement(client, db, "2024-01-01", "2024-01-02")
        response = client.get(f"/bin_day_replacements/{rep.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == rep.id
        assert data["replace"][:10] == "2024-01-01"
        assert data["replace_with"][:10] == "2024-01-02"

    def test_not_found(self, client, db):
        response = client.get("/bin_day_replacements/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "BinDayReplacement not found"

class TestBinDayReplacementEdit:
    def test_edit(self, client, db):
        db.query(BinDayReplacement).delete()
        db.commit()
        rep = create_bin_day_replacement(client, db, "2024-01-01", "2024-01-02")
        patch = {"replace_with": "2024-01-03T00:00:00"}
        response = client.patch(f"/bin_day_replacements/{rep.id}", json=patch)
        assert response.status_code == 200
        data = response.json()
        assert data["replace_with"] == patch["replace_with"]
        assert data["replace"][:10] == "2024-01-01"

    def test_partial_update_replace(self, client, db):
        db.query(BinDayReplacement).delete()
        db.commit()
        rep = create_bin_day_replacement(client, db, "2024-01-01", "2024-01-02")
        patch = {"replace": "2024-01-05T00:00:00"}
        response = client.patch(f"/bin_day_replacements/{rep.id}", json=patch)
        assert response.status_code == 200
        data = response.json()
        assert data["replace"] == patch["replace"]
        assert data["replace_with"][:10] == "2024-01-02"

    def test_no_parameters(self, client, db):
        db.query(BinDayReplacement).delete()
        db.commit()
        rep = create_bin_day_replacement(client, db, "2024-01-01", "2024-01-02")
        response = client.patch(f"/bin_day_replacements/{rep.id}", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["replace"][:10] == "2024-01-01"
        assert data["replace_with"][:10] == "2024-01-02"

    def test_not_found(self, client, db):
        patch = {"replace_with": "2024-01-03T00:00:00"}
        response = client.patch("/bin_day_replacements/99999", json=patch)
        assert response.status_code == 404
        assert response.json()["detail"] == "BinDayReplacement not found"

class TestBinDayReplacementDelete:
    def test_delete(self, client, db):
        db.query(BinDayReplacement).delete()
        db.commit()
        rep = create_bin_day_replacement(client, db, "2024-01-01", "2024-01-02")
        response = client.delete(f"/bin_day_replacements/{rep.id}")
        assert response.status_code == 204
        # Confirm deletion
        response = client.get(f"/bin_day_replacements/{rep.id}")
        assert response.status_code == 404

    def test_not_found(self, client, db):
        response = client.delete("/bin_day_replacements/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "BinDayReplacement not found"
