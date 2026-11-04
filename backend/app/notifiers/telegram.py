"""Telegram notification service for Nightwatch alerts and approvals."""

import logging
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings
from app.models.schemas import Check, Incident, Service

logger = logging.getLogger("nightwatch.notifiers.telegram")


async def send_telegram_message(
    text: str,
    reply_markup: Optional[Dict[str, Any]] = None,
) -> bool:
    """Send a formatted Markdown message to configured Telegram chat.

    Args:
        text: Message body formatted in Telegram Markdown/HTML.
        reply_markup: Optional inline keyboard markup for approvals.

    Returns:
        True if sent successfully, False otherwise.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        logger.debug("Telegram notifications skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID unset")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info("Telegram notification sent successfully to chat ending in ...%s", chat_id[-4:])
                return True
            logger.warning(
                "Telegram API error HTTP %d: %s",
                resp.status_code,
                resp.text[:200],
            )
            return False
    except Exception as exc:
        logger.warning("Failed to send Telegram notification: %s", exc)
        return False


async def notify_incident_detected(
    incident: Incident,
    service: Service,
    check: Optional[Check] = None,
) -> bool:
    """Send immediate alert when an incident is opened or escalated."""
    severity_icon = {
        "P1": "🚨",
        "P2": "⚠️",
        "P3": "ℹ️",
    }.get(str(incident.severity), "🚨")

    latency_str = f"{check.latencyMs:.1f}ms" if check and check.latencyMs is not None else "N/A"
    status_str = f"HTTP {check.httpStatus}" if check and check.httpStatus else "Unreachable"

    text = (
        f"{severity_icon} *[NIGHTWATCH ALERT - {incident.severity}]*\n\n"
        f"*Service:* `{service.name}`\n"
        f"*Status:* `{status_str}` (Latency: {latency_str})\n"
        f"*Summary:* {incident.summary}\n"
        f"*Incident ID:* `{incident.id}`\n\n"
        f"🔗 [Open Dashboard War-Room](http://localhost:5173/incidents/{incident.id})"
    )

    return await send_telegram_message(text)


async def notify_incident_resolved(
    incident: Incident,
    service: Service,
) -> bool:
    """Send notification when an incident is verified recovered and closed."""
    text = (
        f"✅ *[NIGHTWATCH RESOLVED - {incident.severity}]*\n\n"
        f"*Service:* `{service.name}`\n"
        f"*Incident:* `{incident.id}`\n"
        f"*Resolution:* Service recovered. 3 consecutive healthy sweeps verified.\n\n"
        f"🔗 [View Incident Timeline](http://localhost:5173/incidents/{incident.id})"
    )
    return await send_telegram_message(text)
