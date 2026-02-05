import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(root_dir))

import pytest
from database.models import Bin
from backend.tests.test_db import db, client


def test_list_bins_returns_all_bins(client, db):
    """
    Test that GET /api/bin/ returns a list of all bins in the DB.
    """
    # Ensure a clean state
    db.query(Bin).delete()
    db.commit()

    # 1. ARRANGE: Manually add two bins to our test database
    bin_1 = Bin(name="Green Bin", position=1, colour="#ffffff")
    bin_2 = Bin(name="Blue Bin", position=2, colour="#000000")

    db.add(bin_1)
    db.add(bin_2)
    db.commit()

    # 2. ACT: Call the FastAPI endpoint
    response = client.get("/api/bins/")

    # 3. ASSERT: Check status code and data integrity
    assert response.status_code == 200

    data = response.json()
    assert "bins" in data
    assert len(data["bins"]) == 2

    # Verify specific data points
    names = [h["name"] for h in data["bins"]]
    assert "Green Bin" in names
    assert "Blue Bin" in names

    # Verify the entire format of the JSON response
    expected = {
        "bins": [
            {
                "id": bin_1.id,
                "name": "Green Bin",
                "position": 1,
                "colour": "#ffffff"
            },
            {
                "id": bin_2.id,
                "name": "Blue Bin",
                "position": 2,
                "colour": "#000000"
            }
        ]
    }
    assert response.json() == expected


def test_list_bins_empty_db(client, db):
    """
    Test that the endpoint returns an empty list if no bins exist.
    """
    db.query(Bin).delete()
    db.commit()
    response = client.get("/api/bins/")
    assert response.status_code == 200
    assert response.json() == {"bins": []}
