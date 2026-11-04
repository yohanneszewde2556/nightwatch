"""External webhooks API endpoints for Telegram button callbacks."""

import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
import httpx

from app.api.deps import get_storage
from app.core.config import settings
from app.models.enums import EventType, IncidentStatus
from app.models.schemas import AuditLog, IncidentEvent
from app.storage.base import BaseRepository
from app.tools.deploy import rollback_deploy

logger = logging.getLogger("nightwatch.api.webhooks")

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)


@router.post("/telegram")
async def telegram_webhook(
    payload: Dict[str, Any],
    storage: BaseRepository = Depends(get_storage),
) -> Dict[str, Any]:
    """Handle callback button queries and message updates from Telegram bot.

    Processes inline button approvals and rejections from mobile.
    """
    callback_query = payload.get("callback_query")
    if not callback_query:
        # Ignore regular text messages or unhandled update types
        return {"ok": True, "status": "ignored"}

    cb_id = callback_query.get("id")
    data = callback_query.get("data", "")
    from_user = callback_query.get("from", {}).get("first_name", "Telegram User")

    if not data or ":" not in data:
        return {"ok": True, "status": "invalid_data"}

    action_type, incident_id = data.split(":", 1)
    incident = storage.get_incident(incident_id)

    if not incident:
        logger.warning("Telegram webhook received callback for unknown incident %s", incident_id)
        return {"ok": False, "error": "Incident not found"}

    service = storage.get_service(incident.serviceId)
    if not service:
        logger.warning("Service %s not found for incident %s", incident.serviceId, incident_id)
        return {"ok": False, "error": "Service not found"}

    # Telegram Bot API answer callback query helper
    async def answer_callback(text: str) -> None:
        if settings.TELEGRAM_BOT_TOKEN and cb_id:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(
                        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
                        json={"callback_query_id": cb_id, "text": text},
                    )
            except Exception as e:
                logger.debug("Failed to answer Telegram callback query: %s", e)

    if action_type == "approve":
        # 1. Execute the rollback remediation
        rollback_res = await rollback_deploy(service)

        # 2. Transition incident to MITIGATING
        storage.update_incident(incident_id, status=IncidentStatus.MITIGATING)

        # 3. Add timeline events
        storage.add_incident_event(
            IncidentEvent(
                incidentId=incident_id,
                type=EventType.APPROVAL,
                payload={
                    "decision": "approved",
                    "approver": f"telegram:{from_user}",
                    "note": f"Approved by {from_user} via Telegram mobile button",
                },
            )
        )
        storage.add_incident_event(
            IncidentEvent(
                incidentId=incident_id,
                type=EventType.ACTION,
                payload={
                    "action": "rollback_deploy",
                    "status": "executed",
                    "result": rollback_res,
                },
            )
        )

        await answer_callback("✅ Rollback approved and executed!")
        return {"ok": True, "action": "approved", "incident_id": incident_id}

    elif action_type == "reject":
        # Transition back to INVESTIGATING
        storage.update_incident(incident_id, status=IncidentStatus.INVESTIGATING)

        storage.add_incident_event(
            IncidentEvent(
                incidentId=incident_id,
                type=EventType.APPROVAL,
                payload={
                    "decision": "rejected",
                    "approver": f"telegram:{from_user}",
                    "note": f"Rejected by {from_user} via Telegram",
                },
            )
        )

        await answer_callback("❌ Action rejected.")
        return {"ok": True, "action": "rejected", "incident_id": incident_id}

    return {"ok": True, "status": "unhandled_action"}
