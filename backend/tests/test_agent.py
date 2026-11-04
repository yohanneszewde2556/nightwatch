"""Unit tests for the AI Investigation Agent, Runbook Memory, and Telegram Webhook."""

import asyncio
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.agent.investigator import investigation_agent
from app.agent.runbook_memory import cosine_similarity, search_similar_runbooks
from app.models.enums import AutonomyLevel, Criticality, EventType, IncidentStatus, Severity
from app.models.schemas import IncidentCreate, Runbook, ServiceCreate
from app.storage.base import BaseRepository


def test_cosine_similarity_calculation():
    """Verify vector cosine similarity arithmetic."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert cosine_similarity(v1, v2) == 1.0

    v3 = [0.0, 1.0, 0.0]
    assert cosine_similarity(v1, v3) == 0.0

    assert cosine_similarity([], [1.0]) == 0.0
    assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0


def test_search_runbooks_lexical_fallback(test_storage: BaseRepository):
    """Runbook search finds relevant precedent using symptoms query."""
    test_storage.create_runbook(
        Runbook(
            id="rb-test-1",
            incidentId="inc-past-1",
            symptoms="Database connection pool timeout under load",
            rootCause="Max connections limit reached in pgbouncer",
            fixApplied="Scale up connection pool size to 100",
            outcome="Pool recovered",
        )
    )
    test_storage.create_runbook(
        Runbook(
            id="rb-test-2",
            incidentId="inc-past-2",
            symptoms="TypeError in checkout calculation after promo code update",
            rootCause="NoneType rate multiplication on unknown promo code",
            fixApplied="Rollback deploy to previous release",
            outcome="Restored checkout",
        )
    )

    async def _test():
        results = await search_similar_runbooks("checkout TypeError promo code", test_storage, limit=1)
        assert len(results) == 1
        assert results[0]["id"] == "rb-test-2"
        assert results[0]["similarity_score"] > 0.0

    asyncio.run(_test())


def test_investigation_agent_end_to_end(test_storage: BaseRepository):
    """Investigation agent gathers evidence, formulates hypothesis, and dispatches approval."""
    svc = test_storage.create_service(
        ServiceCreate(
            id="svc-investigate-test",
            name="Demo Shop API",
            healthUrl="http://127.0.0.1:8001/health",
            criticality=Criticality.HIGH,
            autonomyLevel=AutonomyLevel.ACT_WITH_APPROVAL,
            paused=False,
        )
    )

    inc = test_storage.create_incident(
        IncidentCreate(
            id="inc-inv-001",
            serviceId=svc.id,
            severity=Severity.P1,
            status=IncidentStatus.DETECTED,
            summary="High error rate on checkout: TypeError",
        )
    )

    mock_logs = [
        {
            "route": "/checkout",
            "status": 500,
            "exception": "TypeError: unsupported operand type(s) for *: 'float' and 'NoneType' in app/checkout.py:apply_discount",
        }
    ]
    mock_commits = [
        {
            "sha": "a1b2c3d",
            "message": "Add discount codes to checkout",
            "author": "dev@nightwatch.io",
        }
    ]

    async def _test():
        with patch(
            "app.agent.investigator.fetch_logs",
            new=AsyncMock(return_value=mock_logs),
        ), patch(
            "app.agent.investigator.list_recent_commits",
            new=AsyncMock(return_value=mock_commits),
        ), patch(
            "app.agent.investigator.send_telegram_message",
            new=AsyncMock(return_value=True),
        ) as mock_tg:
            res = await investigation_agent.investigate(inc.id, test_storage)
            assert res["status"] == "awaiting_approval"
            mock_tg.assert_called_once()

            # Confirm incident updated with root cause and confidence
            updated_inc = test_storage.get_incident(inc.id)
            assert updated_inc.status == IncidentStatus.AWAITING_APPROVAL
            assert updated_inc.confidence == 0.86
            assert "discount" in updated_inc.rootCause.lower()

            # Confirm timeline events recorded (tool calls, hypothesis, action)
            events = test_storage.list_incident_events(inc.id)
            event_types = [e.type for e in events]
            assert EventType.TOOL_CALL in event_types
            assert EventType.HYPOTHESIS in event_types
            assert EventType.ACTION in event_types

    asyncio.run(_test())


def test_telegram_webhook_approval_button(client: TestClient, test_storage: BaseRepository):
    """POST /webhooks/telegram processes mobile inline button approval."""
    svc = test_storage.create_service(
        ServiceCreate(
            id="svc-tg-test",
            name="Demo Shop API",
            healthUrl="http://127.0.0.1:8001/health",
            criticality=Criticality.HIGH,
            paused=False,
        )
    )
    inc = test_storage.create_incident(
        IncidentCreate(
            id="inc-tg-001",
            serviceId=svc.id,
            severity=Severity.P1,
            status=IncidentStatus.AWAITING_APPROVAL,
            summary="Outage on demo-shop",
        )
    )

    with patch(
        "app.api.webhooks.rollback_deploy",
        new=AsyncMock(return_value={"success": True, "message": "Rolled back"}),
    ):
        payload = {
            "callback_query": {
                "id": "cb_123",
                "data": f"approve:{inc.id}",
                "from": {"first_name": "Yohannes"},
            }
        }
        res = client.post("/webhooks/telegram", json=payload)
        assert res.status_code == 200
        assert res.json()["action"] == "approved"

        # Confirm incident status shifted to mitigating
        updated = test_storage.get_incident(inc.id)
        assert updated.status == IncidentStatus.MITIGATING


def test_agent_chat_endpoint(client: TestClient, auth_headers: dict):
    """POST /api/agent/chat answers questions with production context."""
    payload = {"message": "What is the status of our services?"}
    res = client.post("/api/agent/chat", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert len(data["reply"]) > 0
