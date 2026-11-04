"""Background sweep scheduler for continuous service monitoring."""

import asyncio
import logging
from typing import Optional

from app.core.config import settings
from app.detectors.sweep_service import detector_engine
from app.storage import get_repository

logger = logging.getLogger("nightwatch.detectors.scheduler")

_scheduler_task: Optional[asyncio.Task] = None


async def _sweep_loop() -> None:
    """Continuous background loop executing detection sweeps."""
    logger.info(
        "Detection scheduler started (interval: %.1fs)",
        settings.SWEEP_INTERVAL_SECONDS,
    )
    # Brief initial delay to allow FastAPI server to finish binding
    await asyncio.sleep(2.0)

    storage = get_repository()

    while True:
        try:
            results = await detector_engine.sweep_all_services(storage)
            logger.debug(
                "Completed sweep: %d services, %d incidents opened, %d resolved",
                results["services_checked"],
                results["incidents_created"],
                results["incidents_resolved"],
            )
        except asyncio.CancelledError:
            logger.info("Detection scheduler loop cancelled")
            break
        except Exception as exc:
            logger.error("Error during scheduled detection sweep: %s", exc)

        await asyncio.sleep(settings.SWEEP_INTERVAL_SECONDS)


def start_detection_scheduler() -> Optional[asyncio.Task]:
    """Start background detection scheduler if enabled."""
    global _scheduler_task
    if settings.SWEEP_ENABLED and settings.SWEEP_INTERVAL_SECONDS > 0:
        if _scheduler_task is None or _scheduler_task.done():
            _scheduler_task = asyncio.create_task(_sweep_loop())
    return _scheduler_task


async def stop_detection_scheduler() -> None:
    """Stop background detection scheduler."""
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None
