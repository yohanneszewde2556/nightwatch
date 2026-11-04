"""Incidents management and war-room API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_storage
from app.core.auth import verify_dashboard_auth
from app.models.enums import IncidentStatus, Severity
from app.models.schemas import (
    ActionApprovalRequest,
    ActionRejectionRequest,
    Incident,
    IncidentEvent,
)
from app.storage.base import BaseRepository

router = APIRouter(
    prefix="/api/incidents",
    tags=["incidents"],
    dependencies=[Depends(verify_dashboard_auth)],
)


@router.get("", response_model=List[Incident])
def list_incidents(
    status_filter: Optional[IncidentStatus] = Query(None, alias="status"),
    severity: Optional[Severity] = Query(None),
    service_id: Optional[str] = Query(None),
    storage: BaseRepository = Depends(get_storage),
) -> List[Incident]:
    """List incidents with optional filtering by status or severity."""
    return storage.list_incidents(
        status=status_filter,
        severity=severity,
        service_id=service_id,
    )


@router.get("/{incident_id}", response_model=Incident)
def get_incident(
    incident_id: str,
    storage: BaseRepository = Depends(get_storage),
) -> Incident:
    """Get incident details, root cause, and confidence score."""
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
        )
    return incident


@router.get("/{incident_id}/events", response_model=List[IncidentEvent])
def get_incident_events(
    incident_id: str,
    storage: BaseRepository = Depends(get_storage),
) -> List[IncidentEvent]:
    """Retrieve timeline events and reasoning trace for an incident."""
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
        )
    return storage.list_incident_events(incident_id)


@router.post("/{incident_id}/approve")
def approve_incident_action(
    incident_id: str,
    request: ActionApprovalRequest,
    storage: BaseRepository = Depends(get_storage),
) -> None:
    """Approve a proposed agent remediation action.

    Stub behavior: In next phase, triggers execution of rollback/pr action.
    """
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
        )
    # TODO: Implement agent action execution and verification loop in next phase
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Action approval execution is pending implementation in Phase 2.",
    )


@router.post("/{incident_id}/reject")
def reject_incident_action(
    incident_id: str,
    request: ActionRejectionRequest,
    storage: BaseRepository = Depends(get_storage),
) -> None:
    """Reject a proposed agent action with explanation.

    Stub behavior: In next phase, logs feedback to agent and pauses remediation.
    """
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
        )
    # TODO: Implement action rejection and agent alternative hypothesis loop in next phase
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Action rejection handling is pending implementation in Phase 2.",
    )
