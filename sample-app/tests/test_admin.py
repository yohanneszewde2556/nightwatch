"""Tests for demo-shop admin endpoints and auth."""
from fastapi.testclient import TestClient

from app.state import state


def test_admin_auth_missing_header_returns_401(client: TestClient) -> None:
    """Admin routes require X-Admin-Token header; return 401 when missing."""
    assert client.get("/admin/state").status_code == 401
    assert client.post("/admin/deploy", json={"version": "v2"}).status_code == 401
    assert client.post("/admin/rollback").status_code == 401
    assert client.post("/admin/chaos", json={"mode": "slow"}).status_code == 401


def test_admin_auth_invalid_header_returns_401(client: TestClient) -> None:
    """Invalid token returns 401."""
    bad_headers = {"X-Admin-Token": "wrong-token"}
    response = client.get("/admin/state", headers=bad_headers)
    assert response.status_code == 401
    assert "Invalid or missing X-Admin-Token" in response.json()["detail"]


def test_admin_get_state(client: TestClient, admin_headers: dict[str, str]) -> None:
    """GET /admin/state returns current version, chaos mode, and commit label."""
    response = client.get("/admin/state", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "v1"
    assert data["chaos_mode"] == "none"
    assert "Initial demo-shop API" in data["commit_label"]


def test_admin_deploy(client: TestClient, admin_headers: dict[str, str]) -> None:
    """POST /admin/deploy updates current version and commit label."""
    response = client.post("/admin/deploy", json={"version": "v2"}, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "v2"
    assert "Add discount codes to checkout" in data["commit_label"]

    # Verify state reflects new version
    assert state.version == "v2"


def test_admin_deploy_invalid_version(client: TestClient, admin_headers: dict[str, str]) -> None:
    """Deploying invalid version returns 422 Unprocessable Entity."""
    response = client.post("/admin/deploy", json={"version": "v99"}, headers=admin_headers)
    assert response.status_code == 422


def test_admin_rollback(client: TestClient, admin_headers: dict[str, str]) -> None:
    """POST /admin/rollback resets version to v1."""
    # First deploy v2
    client.post("/admin/deploy", json={"version": "v2"}, headers=admin_headers)
    assert state.version == "v2"

    # Now rollback
    response = client.post("/admin/rollback", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "v1"
    assert "Initial demo-shop API" in data["commit_label"]
    assert state.version == "v1"


def test_admin_chaos_modes(client: TestClient, admin_headers: dict[str, str]) -> None:
    """POST /admin/chaos switches chaos mode."""
    # 1. Down mode makes /health return 503
    res_chaos = client.post("/admin/chaos", json={"mode": "down"}, headers=admin_headers)
    assert res_chaos.status_code == 200
    assert res_chaos.json()["chaos_mode"] == "down"

    res_health = client.get("/health")
    assert res_health.status_code == 503
    assert res_health.json()["status"] == "unhealthy"

    # 2. Reset mode restores /health to 200
    res_reset = client.post("/admin/chaos", json={"mode": "none"}, headers=admin_headers)
    assert res_reset.status_code == 200
    assert res_reset.json()["chaos_mode"] == "none"

    res_health_ok = client.get("/health")
    assert res_health_ok.status_code == 200
    assert res_health_ok.json()["status"] == "healthy"

    # 3. Slow mode sets state
    res_slow = client.post("/admin/chaos", json={"mode": "slow"}, headers=admin_headers)
    assert res_slow.status_code == 200
    assert res_slow.json()["chaos_mode"] == "slow"
