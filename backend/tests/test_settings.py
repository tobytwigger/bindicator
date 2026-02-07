import sys
from pathlib import Path
from datetime import datetime

root_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(root_dir))

from core.database.schemas import SettingsBase


from core.database import models, schemas
from backend.tests.test_db import db, client

# Helper to set a setting
def set_setting(client, db, key="my_settings_key", value=None):
    db_row = db.query(models.Settings).first()
    if db_row:
        setattr(db_row, key, value)
    else:
        db_row = models.Settings(**{key: value})
        db.add(db_row)
    db.commit()
    db.refresh(db_row)
    return db_row


class TestSettingsList:
    def test_list_settings_returns_all_including_defaults(self, client, db):
        # Remove all settings
        db.query(models.Settings).delete()
        db.commit()
        response = client.get("/settings/")
        assert response.status_code == 200
        data = response.json()
        # Should include all defaults
        assert "timeout" in data
        assert data["timeout"] == 120

class TestSettingsCreateOrUpdate:
    def test_create_new_setting(self, client, db):
        response = client.post("/settings", json={"timeout": 500})
        print(response.text)
        assert response.status_code == 200
        assert response.json() == {"timeout": 500}

    def test_update_existing_setting(self, client, db):
        set_setting(client, db, key="timeout", value=120)
        response = client.post("/settings", json={"timeout": 321})
        assert response.status_code == 200
        assert response.json() == {"timeout": 321}

    def test_create_or_update_setting_invalid_input(self, client, db):
        response = client.post("/settings", json={"invalid": "data"})
        assert response.status_code == 422

class TestClearSettings:
    def test_clear_settings_resets_to_defaults(self, client, db):
        set_setting(client, db, key="timeout", value=999)
        response = client.delete("/settings/timeout")
        assert response.status_code == 204
        # Should now return default
        response = client.get("/settings")
        assert response.status_code == 200
        assert response.json() == {
            "timeout": 120
        }

    def test_clear_settings_with_no_database_settings(self, client, db):
        # Should not error if setting doesn't exist
        response = client.delete("/settings/timeout")
        assert response.status_code == 204
        # Should still return default
        response = client.get("/settings")
        assert response.status_code == 200
        assert response.json() == {
            "timeout": 120
        }
