"""Demo chaos engineering endpoints for live scenario validation."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import verify_dashboard_auth
from app.models.schemas import ChaosRequest

router = APIRouter(
    prefix="/api/demo",
    tags=["demo"],
    dependencies=[Depends(verify_dashboard_auth)],
)


@router.post("/chaos")
def inject_chaos(request: ChaosRequest) -> None:
    """Inject a controlled failure (crash, slow, bad_deploy) into monitored sample app.

    Stub behavior: In next phase, calls the sample app failure endpoints.
    """
    # TODO: Implement demo failure injection against sample app in Phase 5
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Demo chaos injection is pending implementation in Phase 5.",
    )
