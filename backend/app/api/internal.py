"""Internal scheduler tick API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import verify_tick_secret

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(verify_tick_secret)],
)


@router.post("/tick")
def scheduler_tick() -> None:
    """Internal cron tick invoked by Cloud Scheduler every 5 minutes.

    Protected by 'X-Tick-Secret' header.
    Stub behavior: In next phase, triggers health sweeps, deploy watch, and digest jobs.
    """
    # TODO: Implement 5-minute health sweeps and cron dispatcher in Phase 2
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Scheduler tick handler is pending implementation in Phase 2.",
    )
