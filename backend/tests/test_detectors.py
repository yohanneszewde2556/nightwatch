"""Unit tests for the detection sweep engine, DT-3 confirmation, and triage."""

import asyncio
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.detectors.sweep_service import DetectorEngine, detector_engine
from app.models.enums import (
    Criticality,
    EventType,
    IncidentStatus,
    ServiceStatus,
    Severity,
)
from app.models.schemas import ServiceCreate
from app.storage.base import BaseRepository


@pytest.fixture(autouse=True)
def reset_detector():
    """Reset detector memory counters before and after each test."""
    detector_engine.reset_state()
    yield
    detector_engine.reset_state()


def test_single_failure_does_not_open_incident(test_storage: BaseRepository):
    """DT-3: A single failure must NOT open an incident until confirmed by a 2nd check."""
    async def _test():
        svc = test_storage.create_service(
            ServiceCreate(
                id="test-svc-1",
                name="Test Service",
                healthUrl="http://test.local/health",
                criticality=Criticality.HIGH,
                paused=False,
            )
        )

        with patch(
            "app.detectors.sweep_service.probe_service_health",
            new=AsyncMock(return_value=(503, 20.0, "Service Unavailable")),
        ), patch(
            "app.detectors.sweep_service.probe_service_logs",
            new=AsyncMock(return_value=[]),
        ), patch(
            "app.detectors.sweep_service.notify_incident_detected",
            new=AsyncMock(),
        ) as mock_notify:
            # Sweep 1: Failing (1st time)
            res1 = await detector_engine.check_service(svc, test_storage)
            assert res1["consecutive_failures"] == 1
            assert res1["incident_created"] is False
            mock_notify.assert_not_called()

            # Service status should be marked DOWN
            updated_svc = test_storage.get_service("test-svc-1")
            assert updated_svc.status == ServiceStatus.DOWN

            # No incidents should exist for this service
            incidents = test_storage.list_incidents(service_id="test-svc-1")
            assert len(incidents) == 0

    asyncio.run(_test())


def test_second_failure_confirms_and_opens_incident(test_storage: BaseRepository):
    """DT-3: The 2nd consecutive failure confirms the incident, creates timeline event, and alerts."""
    async def _test():
        svc = test_storage.create_service(
            ServiceCreate(
                id="test-svc-2",
                name="Orders API",
                healthUrl="http://orders.local/health",
                criticality=Criticality.HIGH,
                paused=False,
            )
        )

        with patch(
            "app.detectors.sweep_service.probe_service_health",
            new=AsyncMock(return_value=(503, 15.0, "Service Down")),
        ), patch(
            "app.detectors.sweep_service.probe_service_logs",
            new=AsyncMock(return_value=[]),
        ), patch(
            "app.detectors.sweep_service.notify_incident_detected",
            new=AsyncMock(),
        ) as mock_notify:
            # Sweep 1: 1st failure
            await detector_engine.check_service(svc, test_storage)

            # Sweep 2: 2nd failure -> Confirmation!
            res2 = await detector_engine.check_service(svc, test_storage)
            assert res2["consecutive_failures"] == 2
            assert res2["incident_created"] is True
            mock_notify.assert_called_once()

            # Verify incident in storage
            incidents = test_storage.list_incidents(service_id="test-svc-2")
            assert len(incidents) == 1
            inc = incidents[0]
            assert inc.severity == Severity.P1  # Critical service down
            assert inc.status == IncidentStatus.DETECTED
            assert "Orders API outage" in inc.summary

            # Verify initial timeline event
            events = test_storage.list_incident_events(inc.id)
            assert len(events) == 1
            assert events[0].type == EventType.SIGNAL
            assert events[0].payload["http_status"] == 503

    asyncio.run(_test())


def test_duplicate_incident_prevented(test_storage: BaseRepository):
    """Ongoing failures while an incident is open append signals instead of opening duplicates."""
    async def _test():
        svc = test_storage.create_service(
            ServiceCreate(
                id="test-svc-3",
                name="Inventory API",
                healthUrl="http://inventory.local/health",
                criticality=Criticality.MEDIUM,
                paused=False,
            )
        )

        with patch(
            "app.detectors.sweep_service.probe_service_health",
            new=AsyncMock(return_value=(500, 25.0, "Internal Server Error")),
        ), patch(
            "app.detectors.sweep_service.probe_service_logs",
            new=AsyncMock(return_value=[]),
        ), patch(
            "app.detectors.sweep_service.notify_incident_detected",
            new=AsyncMock(),
        ):
            # 1st failure
            await detector_engine.check_service(svc, test_storage)
            # 2nd failure (incident created)
            await detector_engine.check_service(svc, test_storage)
            # 3rd failure (ongoing)
            res3 = await detector_engine.check_service(svc, test_storage)

            assert res3["consecutive_failures"] == 3
            assert res3["incident_created"] is False  # No new incident

            # Still only 1 incident
            incidents = test_storage.list_incidents(service_id="test-svc-3")
            assert len(incidents) == 1

            # Second signal event appended
            events = test_storage.list_incident_events(incidents[0].id)
            assert len(events) == 2

    asyncio.run(_test())


def test_three_healthy_checks_auto_resolves(test_storage: BaseRepository):
    """Three consecutive healthy checks close an open incident."""
    async def _test():
        svc = test_storage.create_service(
            ServiceCreate(
                id="test-svc-4",
                name="Search API",
                healthUrl="http://search.local/health",
                criticality=Criticality.HIGH,
                paused=False,
            )
        )

        # 1. Trigger incident with 2 failures
        with patch(
            "app.detectors.sweep_service.probe_service_health",
            new=AsyncMock(return_value=(503, 10.0, "Down")),
        ), patch(
            "app.detectors.sweep_service.probe_service_logs",
            new=AsyncMock(return_value=[]),
        ), patch(
            "app.detectors.sweep_service.notify_incident_detected",
            new=AsyncMock(),
        ):
            await detector_engine.check_service(svc, test_storage)
            await detector_engine.check_service(svc, test_storage)

        incidents = test_storage.list_incidents(service_id="test-svc-4")
        assert len(incidents) == 1
        assert incidents[0].status == IncidentStatus.DETECTED

        # 2. Recover service and run 3 healthy sweeps
        with patch(
            "app.detectors.sweep_service.probe_service_health",
            new=AsyncMock(return_value=(200, 12.0, None)),
        ), patch(
            "app.detectors.sweep_service.probe_service_logs",
            new=AsyncMock(return_value=[]),
        ), patch(
            "app.detectors.sweep_service.notify_incident_resolved",
            new=AsyncMock(),
        ) as mock_resolved_notify:
            # Healthy 1
            res1 = await detector_engine.check_service(svc, test_storage)
            assert res1["incident_resolved"] is False

            # Healthy 2
            res2 = await detector_engine.check_service(svc, test_storage)
            assert res2["incident_resolved"] is False

            # Healthy 3 -> Auto-resolution!
            res3 = await detector_engine.check_service(svc, test_storage)
            assert res3["incident_resolved"] is True
            mock_resolved_notify.assert_called_once()

            # Verify incident is resolved in storage
            updated_inc = test_storage.get_incident(incidents[0].id)
            assert updated_inc.status == IncidentStatus.RESOLVED
            assert updated_inc.resolvedAt is not None

    asyncio.run(_test())


def test_internal_tick_executes_sweep(client: TestClient):
    """POST /internal/tick with X-Tick-Secret executes sweep across services."""
    headers = {"X-Tick-Secret": settings.TICK_SECRET}
    response = client.post("/internal/tick", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "services_checked" in data
    assert "incidents_created" in data
    assert "timestamp" in data
