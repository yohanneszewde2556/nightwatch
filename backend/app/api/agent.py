"""Agent chat and interactive inquiry API endpoints."""

from typing import Any, Dict
from fastapi import APIRouter, Depends

from app.agent.runbook_memory import search_similar_runbooks
from app.api.deps import get_storage
from app.core.auth import verify_dashboard_auth
from app.core.gemini_client import get_gemini_client
from app.models.schemas import AgentChatRequest
from app.storage.base import BaseRepository

router = APIRouter(
    prefix="/api/agent",
    tags=["agent"],
    dependencies=[Depends(verify_dashboard_auth)],
)


@router.post("/chat")
async def chat_with_agent(
    request: AgentChatRequest,
    storage: BaseRepository = Depends(get_storage),
) -> Dict[str, Any]:
    """Ask the Nightwatch agent questions about incident history and live services."""
    context_sections = []

    # 1. Fetch relevant runbooks
    query_text = request.message
    runbooks = await search_similar_runbooks(query_text, storage=storage, limit=2)
    if runbooks:
        context_sections.append(
            "Relevant Past Runbooks:\n" + "\n".join(
                f"- Symptoms: {rb['symptoms']} | Cause: {rb['root_cause']} | Fix: {rb['fix_applied']}"
                for rb in runbooks
            )
        )

    # 2. Fetch active incidents
    active_incidents = storage.list_incidents(service_id=request.serviceId)[:5]
    if active_incidents:
        context_sections.append(
            "Recent Incidents:\n" + "\n".join(
                f"- [{inc.severity}] {inc.id}: {inc.summary} (Status: {inc.status}, Cause: {inc.rootCause or 'Investigating'})"
                for inc in active_incidents
            )
        )

    prompt = (
        f"You are Nightwatch, an AI SRE engineer. Answer the user question based on production telemetry:\n\n"
        + "\n\n".join(context_sections) + f"\n\nUser Question: {query_text}\nAnswer:"
    )

    try:
        gemini = get_gemini_client()
        reply, model = await gemini.generate_content(
            prompt=prompt,
            system_instruction="Be concise, factual, and helpful like an on-call site reliability engineer.",
            temperature=0.2,
        )
        return {
            "reply": reply.strip(),
            "model": model,
            "sources": [rb["id"] for rb in runbooks],
        }
    except Exception:
        # Fallback response using local context
        if active_incidents:
            latest = active_incidents[0]
            fallback_text = (
                f"Currently tracking incident {latest.id} ({latest.severity}): {latest.summary}. "
                f"Status is {latest.status}. "
                f"{'Root cause identified as: ' + latest.rootCause if latest.rootCause else 'Investigation is ongoing.'}"
            )
        else:
            fallback_text = "All registered services are currently healthy. No active incidents detected."
        return {
            "reply": fallback_text,
            "model": "rule-based-synthesizer",
            "sources": [],
        }
