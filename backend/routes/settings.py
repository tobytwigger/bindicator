from fastapi import APIRouter, Depends, Response
from core.database.schemas import Settings as SettingsSchema, SettingsEdit
from core.database.repositories import SettingsRepository
from backend.utils.mqtt_publisher import publish_settings_update

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)

def get_settings_repo() -> SettingsRepository:
    return SettingsRepository()

@router.get("/", response_model=SettingsSchema)
def get_settings(repo: SettingsRepository = Depends(get_settings_repo)):
    """
    Get the current settings.
    """
    return repo.get_all()

@router.post("/", response_model=SettingsSchema)
def create_or_update_settings(settings: SettingsEdit, repo: SettingsRepository = Depends(get_settings_repo)):
    """
    Create new settings. This will overwrite existing settings.
    """
    repo.create_or_update(settings)

    # Publish MQTT notification that settings have been updated
    publish_settings_update()

    return repo.get_all()

@router.delete("/{key}", status_code=204)
def delete_setting(key: str, repo: SettingsRepository = Depends(get_settings_repo)):
    """
    Delete a specific setting by name.
    """
    repo.delete_by_key(key)

    # Publish MQTT notification that settings have been updated
    publish_settings_update()

    return Response(status_code=204)
