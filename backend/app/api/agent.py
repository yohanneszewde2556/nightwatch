"""Agent chat and interactive inquiry API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import verify_dashboard_auth
from app.models.schemas import AgentChatRequest

router = APIRouter(
    prefix="/api/agent",
    tags=["agent"],
    dependencies=[Depends(verify_dashboard_auth)],
)


@router.post("/chat")
def chat_with_agent(request: AgentChatRequest) -> None:
    """Ask the Nightwatch agent questions about incident history.

    Stub behavior: In next phase, connects to Gemini RAG over runbooks and incidents.
    """
    # TODO: Implement Gemini RAG conversational interface over incident memory in Phase 3
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Agent chat interface is pending implementation in Phase 3.",
    )
