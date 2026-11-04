"""Tests for Incident listing, details, and events."""


def test_list_all_incidents(client, auth_headers):
    """Test retrieving list of incidents."""
    res = client.get("/api/incidents", headers=auth_headers)
    assert res.status_code == 200
    incidents = res.json()
    assert len(incidents) == 3
    inc_ids = [i["id"] for i in incidents]
    assert "inc-101" in inc_ids
    assert "inc-102" in inc_ids
    assert "inc-103" in inc_ids


def test_filter_incidents_by_status(client, auth_headers):
    """Test filtering incidents by status query parameter."""
    res = client.get("/api/incidents?status=resolved", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["id"] == "inc-101"
    assert data[0]["status"] == "resolved"


def test_filter_incidents_by_severity(client, auth_headers):
    """Test filtering incidents by severity."""
    res = client.get("/api/incidents?severity=P2", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["id"] == "inc-103"
    assert data[0]["severity"] == "P2"


def test_get_incident_detail(client, auth_headers):
    """Test fetching incident detail."""
    res = client.get("/api/incidents/inc-101", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "inc-101"
    assert data["severity"] == "P1"
    assert data["confidence"] == 0.94
    assert "TLS cert" in data["rootCause"]


def test_get_incident_events(client, auth_headers):
    """Test retrieving timeline events for an incident."""
    res = client.get("/api/incidents/inc-101/events", headers=auth_headers)
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 5
    types = [e["type"] for e in events]
    assert "signal" in types
    assert "tool_call" in types
    assert "hypothesis" in types
    assert "approval" in types
    assert "action" in types


def test_approve_action_stub(client, auth_headers):
    """Test action approval endpoint returns 501 stub."""
    payload = {"approvedBy": "tester@acme.corp", "comment": "Approved rollback"}
    res = client.post("/api/incidents/inc-103/approve", json=payload, headers=auth_headers)
    assert res.status_code == 501
    assert "pending implementation" in res.json()["detail"]


def test_reject_action_stub(client, auth_headers):
    """Test action rejection endpoint returns 501 stub."""
    payload = {"reason": "Not the correct revision", "rejectedBy": "tester@acme.corp"}
    res = client.post("/api/incidents/inc-103/reject", json=payload, headers=auth_headers)
    assert res.status_code == 501
    assert "pending implementation" in res.json()["detail"]
