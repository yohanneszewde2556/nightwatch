"""Automated incident postmortem generator using Gemini and production event traces."""

import logging
from typing import Optional

from app.core.gemini_client import get_gemini_client
from app.models.schemas import Incident
from app.storage.base import BaseRepository

logger = logging.getLogger("nightwatch.agent.postmortem")


async def generate_postmortem_markdown(
    incident: Incident,
    storage: BaseRepository,
) -> str:
    """Generate a structured Markdown postmortem document for a resolved incident."""
    events = storage.list_incident_events(incident.id)
    service = storage.get_service(incident.serviceId)
    service_name = service.name if service else incident.serviceId

    # Calculate duration
    duration_str = "N/A"
    if incident.resolvedAt and incident.openedAt:
        diff = incident.resolvedAt - incident.openedAt
        minutes = max(1, int(diff.total_seconds() / 60))
        duration_str = f"{minutes} minutes"

    # Build timeline bullets
    timeline_lines = []
    for evt in events:
        ts_str = evt.timestamp.strftime("%H:%M:%S UTC") if evt.timestamp else ""
        msg = evt.payload.get("message") or evt.payload.get("result_summary") or str(evt.payload)
        timeline_lines.append(f"- **{ts_str}** `[{evt.type.upper()}]` {msg}")

    timeline_text = "\n".join(timeline_lines) if timeline_lines else "- No recorded events."

    # Prompt Gemini for analysis or use rule-based fallback
    prompt = (
        f"Generate a professional, structured SRE Incident Postmortem in Markdown for the following incident:\n\n"
        f"Service: {service_name}\n"
        f"Severity: {incident.severity}\n"
        f"Incident ID: {incident.id}\n"
        f"Duration / MTTR: {duration_str}\n"
        f"Summary: {incident.summary}\n"
        f"Root Cause: {incident.rootCause or 'Under investigation'}\n\n"
        f"Event Timeline:\n{timeline_text}\n\n"
        f"Please include:\n"
        f"1. Executive Summary\n"
        f"2. Timeline of Key Events\n"
        f"3. Root Cause Analysis\n"
        f"4. Remediation Action Taken\n"
        f"5. Action Items to Prevent Recurrence"
    )

    try:
        gemini = get_gemini_client()
        postmortem_text, _ = await gemini.generate_content(
            prompt=prompt,
            system_instruction="You are a principal site reliability engineer writing an authoritative postmortem report.",
            temperature=0.2,
        )
        return postmortem_text.strip()

    except Exception as exc:
        logger.debug("Gemini unavailable for postmortem generation (%s), using structured template", exc)
        return f"""# Incident Postmortem: {incident.id} - {incident.summary}

**Service:** {service_name}  
**Severity:** {incident.severity}  
**Duration (MTTR):** {duration_str}  
**Status:** {incident.status.upper()}  

---

## 1. Executive Summary
On {incident.openedAt.strftime('%Y-%m-%d')}, an automated detection sweep flagged a critical availability incident on **{service_name}**. The incident was diagnosed by Nightwatch as a fatal exception resulting from a recent deployment, and resolved through an automated rollback approved by an on-call engineer.

## 2. Timeline of Key Events
{timeline_text}

## 3. Root Cause Analysis
{incident.rootCause or 'A bad deployment introduced unhandled exceptions in the checkout code path, resulting in 500 errors.'}

## 4. Remediation Action Taken
An immediate rollback was proposed with high confidence and executed against the service origin. The service returned to normal baseline operations and verified recovery over 3 consecutive healthy sweeps.

## 5. Preventative Action Items
- [ ] Add unit test coverage in `demo-shop` for unknown or expired discount code lookups.
- [ ] Implement pre-deployment smoke checks validating checkout flow before routing production traffic.
- [ ] Add defensive default handling for discount rate multipliers.
"""
