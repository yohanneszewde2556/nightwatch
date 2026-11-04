"""Application configuration via pydantic-settings.

Reads from a `.env` file located in the sample-app directory.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Demo-shop configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ADMIN_TOKEN: str = "demo-admin-secret"
    APP_VERSION: str = "v1"
    CHAOS_MODE: str = "none"
    TRAFFIC_INTERVAL_SECONDS: float = 1.5
    TRAFFIC_ENABLED: bool = True
    LOG_BUFFER_SIZE: int = 1000
    PORT: int = 8001


settings = Settings()
