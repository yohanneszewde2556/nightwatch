"""Unit tests for demo chaos endpoints and weekly reliability reports."""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.models.enums import IncidentStatus, Severity
from app.models.schemas import IncidentCreate, ServiceCreate
from app.storage.base import BaseRepository


def test_demo_chaos_bad_deploy(client: TestClient, auth_headers: dict):
    """POST /api/demo/chaos injects bad_deploy into demo-shop."""
    with patch(
        "app.api.demo.httpx.AsyncClient.post",
        new=AsyncMock(return_value=AsyncMock(status_code=200, json=lambda: {"version": "v2"})),
    ), patch(
        "app.api.demo.httpx.AsyncClient.get",
        new=AsyncMock(return_value=AsyncMock(status_code=200, json=lambda: {"version": "v2", "chaos_mode": "none"})),
    ):
        payload = {"scenario": "bad_deploy"}
        res = client.post("/api/demo/chaos", json=payload, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["scenario"] == "bad_deploy"


def test_demo_chaos_crash_down(client: TestClient, auth_headers: dict):
    """POST /api/demo/chaos injects crash scenario."""
    with patch(
        "app.api.demo.httpx.AsyncClient.post",
        new=AsyncMock(return_value=AsyncMock(status_code=200, json=lambda: {"mode": "down"})),
    ), patch(
        "app.api.demo.httpx.AsyncClient.get",
        new=AsyncMock(return_value=AsyncMock(status_code=200, json=lambda: {"version": "v1", "chaos_mode": "down"})),
    ):
        payload = {"scenario": "crash"}
        res = client.post("/api/demo/chaos", json=payload, headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["scenario"] == "crash"


def test_demo_chaos_invalid_scenario(client: TestClient, auth_headers: dict):
    """POST /api/demo/chaos rejects invalid scenario."""
    payload = {"scenario": "invalid_mode"}
    res = client.post("/api/demo/chaos", json=payload, headers=auth_headers)
    assert res.status_code == 400


def test_weekly_report_metrics(client: TestClient, auth_headers: dict, test_storage: BaseRepository):
    """GET /api/reports/weekly returns aggregated reliability telemetry."""
    res = client.get("/api/reports/weekly", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "uptimePercent" in data
    assert "mttrMinutes" in data
    assert "costAvoidedUsd" in data
    assert "topFailureModes" in data
    assert "serviceMetrics" in data
    assert data["totalIncidents"] >= 0


def test_get_incident_postmortem(client: TestClient, auth_headers: dict, test_storage: BaseRepository):
    """GET /api/reports/postmortems/{id} generates structured postmortem markdown."""
    svc = test_storage.create_service(
        ServiceCreate(
            id="svc-pm-test",
            name="Checkout API",
            healthUrl="http://127.0.0.1:8001/health",
            paused=False,
        )
    )
    inc = test_storage.create_incident(
        IncidentCreate(
            id="inc-pm-001",
            serviceId=svc.id,
            severity=Severity.P1,
            status=IncidentStatus.RESOLVED,
            summary="Checkout discount calculation crash",
        )
    )

    res = client.get(f"/api/reports/postmortems/{inc.id}", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["incidentId"] == inc.id
    assert "markdown" in data
    assert "# Incident Postmortem" in data["markdown"]
