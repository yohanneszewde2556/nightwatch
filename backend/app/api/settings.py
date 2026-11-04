"""Settings and global kill switch API endpoints."""

from fastapi import APIRouter, Depends

from app.api.deps import get_storage
from app.core.auth import verify_dashboard_auth
from app.models.schemas import KillSwitchUpdate, SystemSettings
from app.storage.base import BaseRepository

router = APIRouter(
    prefix="/api/settings",
    tags=["settings"],
    dependencies=[Depends(verify_dashboard_auth)],
)


@router.get("", response_model=SystemSettings)
def get_settings(storage: BaseRepository = Depends(get_storage)) -> SystemSettings:
    """Get global system settings, notification targets, and kill switch status."""
    return storage.get_settings()


@router.post("/kill-switch", response_model=SystemSettings)
def set_kill_switch(
    payload: KillSwitchUpdate,
    storage: BaseRepository = Depends(get_storage),
) -> SystemSettings:
    """Instantly toggle global agent actions kill switch."""
    return storage.update_kill_switch(payload.killSwitch)
