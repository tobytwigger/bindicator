import sys
from pathlib import Path
import pytest
import json
import tempfile
import os
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(root_dir))

from core.database.repositories import SettingsRepository
from backend.main import app


@pytest.fixture
def temp_settings_file(monkeypatch):
    """Create a temporary settings file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name

    # Monkey patch the settings file path
    monkeypatch.setattr(SettingsRepository, 'SETTINGS_FILE_PATH', temp_path)

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def client():
    """Create a test client without database dependency for settings tests."""
    with TestClient(app) as c:
        yield c


def set_setting_in_file(temp_path, key="timeout", value=120):
    """Helper to directly set a setting in the JSON file."""
    if os.path.exists(temp_path):
        try:
            with open(temp_path, 'r') as f:
                content = f.read()
                settings = json.loads(content) if content else {}
        except (json.JSONDecodeError, ValueError):
            settings = {}
    else:
        settings = {}

    settings[key] = value

    with open(temp_path, 'w') as f:
        json.dump(settings, f)


class TestSettingsList:
    def test_list_settings_returns_all_including_defaults(self, client, temp_settings_file):
        # Remove settings file if it exists
        if os.path.exists(temp_settings_file):
            os.unlink(temp_settings_file)

        response = client.get("/settings/")
        assert response.status_code == 200
        data = response.json()
        # Should include all defaults
        assert "timeout" in data
        assert data["timeout"] == 120
        assert "put_out_day_before" in data
        assert data["put_out_day_before"] == False
        assert "put_out_time" in data
        assert data["put_out_time"] == "17:00"
        assert "collection_time" in data
        assert data["collection_time"] == "09:00"


class TestSettingsCreateOrUpdate:
    def test_create_new_setting(self, client, temp_settings_file):
        response = client.post("/settings", json={"timeout": 500})
        assert response.status_code == 200
        data = response.json()
        assert data["timeout"] == 500
        assert data["put_out_day_before"] == False
        assert data["put_out_time"] == "17:00"
        assert data["collection_time"] == "09:00"

    def test_update_existing_setting(self, client, temp_settings_file):
        set_setting_in_file(temp_settings_file, key="timeout", value=120)
        response = client.post("/settings", json={"timeout": 321})
        assert response.status_code == 200
        data = response.json()
        assert data["timeout"] == 321
        assert data["put_out_day_before"] == False
        assert data["put_out_time"] == "17:00"
        assert data["collection_time"] == "09:00"

    def test_create_or_update_setting_invalid_input(self, client, temp_settings_file):
        response = client.post("/settings", json={"invalid": "data"})
        assert response.status_code == 422


class TestClearSettings:
    def test_clear_settings_resets_to_defaults(self, client, temp_settings_file):
        set_setting_in_file(temp_settings_file, key="timeout", value=999)
        response = client.delete("/settings/timeout")
        assert response.status_code == 204
        # Should now return default
        response = client.get("/settings")
        assert response.status_code == 200
        assert response.json() == {
            "timeout": 120,
            "put_out_day_before": False,
            "put_out_time": "17:00",
            "collection_time": "09:00"
        }

    def test_clear_settings_with_no_file(self, client, temp_settings_file):
        # Remove settings file if it exists
        if os.path.exists(temp_settings_file):
            os.unlink(temp_settings_file)

        # Should not error if setting doesn't exist
        response = client.delete("/settings/timeout")
        assert response.status_code == 204
        # Should still return default
        response = client.get("/settings")
        assert response.status_code == 200
        assert response.json() == {
            "timeout": 120,
            "put_out_day_before": False,
            "put_out_time": "17:00",
            "collection_time": "09:00"
        }
