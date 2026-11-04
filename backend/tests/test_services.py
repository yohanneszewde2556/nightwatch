"""Tests for Service CRUD API endpoints."""


def test_list_services(client, auth_headers):
    """Test retrieving list of registered services."""
    res = client.get("/api/services", headers=auth_headers)
    assert res.status_code == 200
    services = res.json()
    assert len(services) >= 2
    service_ids = [s["id"] for s in services]
    assert "svc-payment-gateway" in service_ids
    assert "svc-cart-checkout" in service_ids


def test_get_service_detail(client, auth_headers):
    """Test getting single service by ID."""
    res = client.get("/api/services/svc-payment-gateway", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Payment Gateway API"
    assert data["criticality"] == "high"
    assert data["autonomyLevel"] == "act_with_approval"


def test_get_nonexistent_service(client, auth_headers):
    """Test 404 for unknown service."""
    res = client.get("/api/services/nonexistent-id", headers=auth_headers)
    assert res.status_code == 404


def test_create_service(client, auth_headers):
    """Test registering a new service."""
    payload = {
        "name": "Auth & Identity Service",
        "healthUrl": "https://auth.example.com/health",
        "cloudRunService": "auth-service",
        "githubRepo": "acme-corp/auth-service",
        "criticality": "high",
        "autonomyLevel": "observe",
        "paused": False,
    }
    res = client.post("/api/services", json=payload, headers=auth_headers)
    assert res.status_code == 201
    created = res.json()
    assert created["id"].startswith("svc-")
    assert created["name"] == payload["name"]
    assert created["status"] == "unknown"


def test_update_service(client, auth_headers):
    """Test updating autonomy level and pausing a service."""
    update_payload = {
        "autonomyLevel": "auto_act",
        "paused": True,
    }
    res = client.patch(
        "/api/services/svc-cart-checkout",
        json=update_payload,
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["autonomyLevel"] == "auto_act"
    assert data["paused"] is True


def test_delete_service(client, auth_headers):
    """Test deleting a service."""
    res = client.delete("/api/services/svc-payment-gateway", headers=auth_headers)
    assert res.status_code == 204

    # Verify deleted
    get_res = client.get("/api/services/svc-payment-gateway", headers=auth_headers)
    assert get_res.status_code == 404
