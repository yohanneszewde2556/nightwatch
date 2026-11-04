"""Authentication dependencies for dashboard and internal routes."""

import secrets
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def verify_dashboard_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    """Validate Bearer token against configured DASHBOARD_PASSWORD."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization: Bearer <token> header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Secure constant-time comparison
    is_valid = secrets.compare_digest(
        credentials.credentials.encode("utf-8"),
        settings.DASHBOARD_PASSWORD.encode("utf-8"),
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid dashboard password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


def verify_tick_secret(
    x_tick_secret: Optional[str] = Header(None, alias="X-Tick-Secret"),
) -> str:
    """Validate X-Tick-Secret header for Cloud Scheduler internal triggers."""
    if not x_tick_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Tick-Secret header",
        )

    is_valid = secrets.compare_digest(
        x_tick_secret.encode("utf-8"),
        settings.TICK_SECRET.encode("utf-8"),
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-Tick-Secret value",
        )

    return x_tick_secret
