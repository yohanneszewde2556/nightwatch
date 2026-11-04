"""Core module exports config and auth utilities."""

from app.core.auth import verify_dashboard_auth, verify_tick_secret
from app.core.config import settings
from app.core.gemini_client import (
    GeminiClient,
    GeminiConfigError,
    GeminiEmbeddingResponse,
    GeminiError,
    GeminiRequestError,
    GeminiResponse,
    get_gemini_client,
)

__all__ = [
    "settings",
    "verify_dashboard_auth",
    "verify_tick_secret",
    "GeminiClient",
    "get_gemini_client",
    "GeminiResponse",
    "GeminiEmbeddingResponse",
    "GeminiError",
    "GeminiConfigError",
    "GeminiRequestError",
]
