"""Internal scheduler tick API endpoints."""

from typing import Any, Dict
from fastapi import APIRouter, Depends

from app.api.deps import get_storage
from app.core.auth import verify_tick_secret
from app.detectors import detector_engine
from app.storage.base import BaseRepository

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(verify_tick_secret)],
)


@router.post("/tick")
async def scheduler_tick(
    storage: BaseRepository = Depends(get_storage),
) -> Dict[str, Any]:
    """Internal cron tick invoked by Cloud Scheduler or test harnesses.

    Protected by 'X-Tick-Secret' header.
    Executes a health and log sweep across all active registered services.
    """
    return await detector_engine.sweep_all_services(storage)
