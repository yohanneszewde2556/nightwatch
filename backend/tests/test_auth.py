"""Tests for dashboard and tick authentication."""

from app.core.config import settings


def test_dashboard_routes_require_auth(client):
    """Confirm dashboard endpoints reject requests lacking Authorization header."""
    res = client.get("/api/services")
    assert res.status_code == 401
    assert "Missing Authorization" in res.json()["detail"]


def test_dashboard_rejects_invalid_bearer_token(client):
    """Confirm dashboard rejects incorrect bearer password."""
    res = client.get(
        "/api/services",
        headers={"Authorization": "Bearer wrong-password-here"},
    )
    assert res.status_code == 401
    assert "Invalid dashboard password" in res.json()["detail"]


def test_dashboard_accepts_valid_bearer_token(client, auth_headers):
    """Confirm dashboard allows access with configured DASHBOARD_PASSWORD."""
    res = client.get("/api/services", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_tick_requires_secret_header(client):
    """Confirm /internal/tick rejects requests without X-Tick-Secret."""
    res = client.post("/internal/tick")
    assert res.status_code == 401
    assert "Missing X-Tick-Secret" in res.json()["detail"]


def test_tick_rejects_wrong_secret(client):
    """Confirm /internal/tick rejects invalid X-Tick-Secret."""
    res = client.post(
        "/internal/tick",
        headers={"X-Tick-Secret": "invalid-secret-value"},
    )
    assert res.status_code == 401
    assert "Invalid X-Tick-Secret" in res.json()["detail"]


def test_tick_accepts_valid_secret(client):
    """Confirm /internal/tick passes authentication with valid secret (returns 501 stub)."""
    res = client.post(
        "/internal/tick",
        headers={"X-Tick-Secret": settings.TICK_SECRET},
    )
    # Authenticated, hits the 501 stub
    assert res.status_code == 501
    assert "pending implementation" in res.json()["detail"]
