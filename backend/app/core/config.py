"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE_PATH = REPO_ROOT / ".env"


class Settings(BaseSettings):
    """Nightwatch configuration settings loaded from environment or .env file."""

    # Gemini AI
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_FALLBACK_MODELS: str = ""
    GEMINI_TIMEOUT_SECONDS: float = 60.0

    @property
    def gemini_fallback_models_list(self) -> list[str]:
        """Parsed list of comma-separated fallback models in priority order."""
        if not self.GEMINI_FALLBACK_MODELS:
            return []
        return [
            m.strip()
            for m in self.GEMINI_FALLBACK_MODELS.split(",")
            if m.strip()
        ]

    # GitHub
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_REPO: Optional[str] = None

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # Security & Auth
    DASHBOARD_PASSWORD: str = "nightwatch-dev-secret"
    TICK_SECRET: str = "nightwatch-scheduler-tick-secret"

    # Storage
    STORAGE_BACKEND: Literal["sqlite", "firestore"] = "sqlite"
    SQLITE_DB_PATH: str = str(REPO_ROOT / "nightwatch.db")

    # API / Server
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=(str(ENV_FILE_PATH), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
