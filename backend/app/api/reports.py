"""Reliability reporting and metrics API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import verify_dashboard_auth

router = APIRouter(
    prefix="/api/reports",
    tags=["reports"],
    dependencies=[Depends(verify_dashboard_auth)],
)


@router.get("/weekly")
def get_weekly_report() -> None:
    """Fetch latest weekly reliability report (uptime, MTTR, downtime cost).

    Stub behavior: In next phase, aggregates incident statistics and generates report.
    """
    # TODO: Implement automated weekly report compilation and metrics aggregation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Weekly reliability reporting is pending implementation in Phase 4.",
    )
