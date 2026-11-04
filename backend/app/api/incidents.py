"""Incidents management and war-room API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_storage
from app.core.auth import verify_dashboard_auth
from app.models.enums import EventType, IncidentStatus, Severity
from app.models.schemas import (
    ActionApprovalRequest,
    ActionRejectionRequest,
    AuditLog,
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
async def approve_incident_action(
    incident_id: str,
    request: ActionApprovalRequest,
    storage: BaseRepository = Depends(get_storage),
) -> dict:
    """Approve a proposed agent remediation action and execute rollback."""
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
        )

    service = storage.get_service(incident.serviceId)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{incident.serviceId}' not found",
        )

    # 1. Execute the rollback remediation
    from app.tools.deploy import rollback_deploy
    rollback_res = await rollback_deploy(service)

    # 2. Transition incident status to MITIGATING
    storage.update_incident(incident_id, status=IncidentStatus.MITIGATING)

    # 3. Log timeline approval event
    approval_note = request.comment or "Approved by operator"
    storage.add_incident_event(
        IncidentEvent(
            incidentId=incident_id,
            type=EventType.APPROVAL,
            payload={
                "decision": "approved",
                "note": approval_note,
                "approver": request.approvedBy or "human_operator",
            },
        )
    )

    # 4. Log timeline action executed event
    storage.add_incident_event(
        IncidentEvent(
            incidentId=incident_id,
            type=EventType.ACTION,
            payload={
                "action": "rollback_deploy",
                "status": "executed",
                "result": rollback_res,
                "message": f"Rollback executed: {rollback_res.get('message', 'Shifted traffic to previous revision')}",
            },
        )
    )

    # 5. Add audit log
    from datetime import datetime, timezone
    import uuid
    storage.add_audit_log(
        AuditLog(
            id=f"audit-{uuid.uuid4().hex[:6]}",
            timestamp=datetime.now(timezone.utc),
            action="approve_rollback",
            target=service.id,
            actor="human_operator",
            approvedBy=request.approvedBy or "human",
            result="success",
        )
    )

    # 6. Notify Telegram of approval
    from app.notifiers.telegram import send_telegram_message
    await send_telegram_message(
        f"✅ *[ACTION APPROVED]*\n"
        f"Rollback executed for `{service.name}`.\n"
        f"Status: Mitigating. Verifying 3 consecutive healthy sweeps..."
    )

    return {
        "status": "approved",
        "action": "rollback_deploy",
        "result": rollback_res,
    }


@router.post("/{incident_id}/reject")
async def reject_incident_action(
    incident_id: str,
    request: ActionRejectionRequest,
    storage: BaseRepository = Depends(get_storage),
) -> dict:
    """Reject a proposed agent action with explanation."""
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
        )

    # 1. Revert to INVESTIGATING or remain open
    storage.update_incident(incident_id, status=IncidentStatus.INVESTIGATING)

    # 2. Log timeline rejection event
    storage.add_incident_event(
        IncidentEvent(
            incidentId=incident_id,
            type=EventType.APPROVAL,
            payload={
                "decision": "rejected",
                "reason": request.reason,
                "actor": "human_operator",
            },
        )
    )

    # 3. Add audit log
    from datetime import datetime, timezone
    import uuid
    storage.add_audit_log(
        AuditLog(
            id=f"audit-{uuid.uuid4().hex[:6]}",
            timestamp=datetime.now(timezone.utc),
            action="reject_remediation",
            target=incident.serviceId,
            actor="human_operator",
            approvedBy=None,
            result=f"rejected: {request.reason}",
        )
    )

    # 4. Notify Telegram
    from app.notifiers.telegram import send_telegram_message
    await send_telegram_message(
        f"❌ *[ACTION REJECTED]*\n"
        f"Incident `{incident_id}`: proposed action was rejected.\n"
        f"Reason: {request.reason}"
    )

    return {
        "status": "rejected",
        "reason": request.reason,
    }
