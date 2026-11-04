"""External webhooks API endpoints."""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)


@router.post("/telegram")
def telegram_webhook(payload: Dict[str, Any]) -> None:
    """Handle callback button queries and message updates from Telegram bot.

    Stub behavior: In next phase, parses callback_data for inline approve/reject buttons.
    """
    # TODO: Implement Telegram inline callback query parser and approval router in Phase 3
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Telegram webhook processing is pending implementation in Phase 3.",
    )
