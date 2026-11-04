"""Seed database with initial services and sample incidents."""

from datetime import datetime, timedelta, timezone
from app.models.enums import (
    AutonomyLevel,
    Criticality,
    EventType,
    IncidentStatus,
    ServiceStatus,
    Severity,
)
from app.models.schemas import (
    IncidentCreate,
    IncidentEvent,
    ServiceCreate,
    ServiceUpdate,
)
from app.storage.base import BaseRepository


def seed_database(storage: BaseRepository) -> None:
    """Populate storage with 2 sample services and 3 sample incidents."""
    now = datetime.now(timezone.utc)

    # -------------------------------------------------------------------------
    # 1. Services
    # -------------------------------------------------------------------------
    svc_payment = ServiceCreate(
        id="svc-payment-gateway",
        name="Payment Gateway API",
        healthUrl="https://payments.example.com/health",
        cloudRunService="payment-service",
        githubRepo="acme-corp/payment-service",
        criticality=Criticality.HIGH,
        autonomyLevel=AutonomyLevel.ACT_WITH_APPROVAL,
        paused=False,
    )
    storage.create_service(svc_payment)
    storage.update_service(
        "svc-payment-gateway",
        ServiceUpdate(status=ServiceStatus.HEALTHY),
    )

    svc_cart = ServiceCreate(
        id="svc-cart-checkout",
        name="Cart & Checkout Service",
        healthUrl="https://checkout.example.com/healthz",
        cloudRunService="cart-checkout",
        githubRepo="acme-corp/cart-checkout",
        criticality=Criticality.HIGH,
        autonomyLevel=AutonomyLevel.SUGGEST,
        paused=False,
    )
    storage.create_service(svc_cart)
    storage.update_service(
        "svc-cart-checkout",
        ServiceUpdate(status=ServiceStatus.DEGRADED),
    )

    # -------------------------------------------------------------------------
    # 2. Incidents & Events
    # -------------------------------------------------------------------------
    # Incident 1: Resolved P1 (Payment Gateway)
    inc_1 = IncidentCreate(
        id="inc-101",
        serviceId="svc-payment-gateway",
        severity=Severity.P1,
        status=IncidentStatus.RESOLVED,
        openedAt=now - timedelta(hours=2),
        summary="Stripe webhook 500 error spike during morning surge",
        rootCause="Expired TLS cert on egress proxy after certbot renewal failure",
        confidence=0.94,
    )
    storage.create_incident(inc_1)
    storage.update_incident(
        "inc-101",
        status=IncidentStatus.RESOLVED,
        root_cause="Expired TLS cert on egress proxy after certbot renewal failure",
        confidence=0.94,
        resolved_at=now - timedelta(hours=1),
    )

    storage.add_incident_event(
        IncidentEvent(
            id="evt-101-1",
            incidentId="inc-101",
            timestamp=now - timedelta(hours=2),
            type=EventType.SIGNAL,
            payload={"detector": "error_spike", "error_count": 48, "threshold": 10, "status_code": 500},
        )
    )
    storage.add_incident_event(
        IncidentEvent(
            id="evt-101-2",
            incidentId="inc-101",
            timestamp=now - timedelta(hours=1, minutes=50),
            type=EventType.TOOL_CALL,
            payload={"tool": "fetch_logs", "lines": 50, "service": "payment-service"},
        )
    )
    storage.add_incident_event(
        IncidentEvent(
            id="evt-101-3",
            incidentId="inc-101",
            timestamp=now - timedelta(hours=1, minutes=45),
            type=EventType.HYPOTHESIS,
            payload={"cause": "Expired TLS certificate on egress proxy", "confidence": 0.94, "evidence": "curl error 60 SSL cert expired"},
        )
    )
    storage.add_incident_event(
        IncidentEvent(
            id="evt-101-4",
            incidentId="inc-101",
            timestamp=now - timedelta(hours=1, minutes=30),
            type=EventType.APPROVAL,
            payload={"approvedBy": "alice@acme.corp", "action": "restart_proxy", "comment": "Emergency cert refresh approved"},
        )
    )
    storage.add_incident_event(
        IncidentEvent(
            id="evt-101-5",
            incidentId="inc-101",
            timestamp=now - timedelta(hours=1, minutes=25),
            type=EventType.ACTION,
            payload={"action": "restart_proxy", "command": "systemctl reload certbot-proxy", "status": "success"},
        )
    )
    storage.add_incident_event(
        IncidentEvent(
            id="evt-101-6",
            incidentId="inc-101",
            timestamp=now - timedelta(hours=1),
            type=EventType.NOTIFICATION,
            payload={"channel": "telegram", "message": "Incident inc-101 resolved. 3 consecutive checks healthy."},
        )
    )

    # Incident 2: Investigating P1 (Cart & Checkout)
    inc_2 = IncidentCreate(
        id="inc-102",
        serviceId="svc-cart-checkout",
        severity=Severity.P1,
        status=IncidentStatus.INVESTIGATING,
        openedAt=now - timedelta(minutes=25),
        summary="Checkout latency breach > 2500ms following deploy v2.4.1",
        rootCause="Unindexed N+1 query in checkout discount calculation",
        confidence=0.82,
    )
    storage.create_incident(inc_2)

    storage.add_incident_event(
        IncidentEvent(
            id="evt-102-1",
            incidentId="inc-102",
            timestamp=now - timedelta(minutes=25),
            type=EventType.SIGNAL,
            payload={"detector": "latency_breach", "p95_latency_ms": 2840, "threshold_ms": 1000},
        )
    )
    storage.add_incident_event(
        IncidentEvent(
            id="evt-102-2",
            incidentId="inc-102",
            timestamp=now - timedelta(minutes=20),
            type=EventType.TOOL_CALL,
            payload={"tool": "list_recent_commits", "repo": "acme-corp/cart-checkout", "commit": "a4f89d1", "author": "dev@acme.corp"},
        )
    )
    storage.add_incident_event(
        IncidentEvent(
            id="evt-102-3",
            incidentId="inc-102",
            timestamp=now - timedelta(minutes=15),
            type=EventType.HYPOTHESIS,
            payload={"cause": "Unindexed N+1 SQL query in apply_discounts loop", "confidence": 0.82, "file": "cart/discounts.py:84"},
        )
    )

    # Incident 3: Awaiting Approval P2 (Cart & Checkout)
    inc_3 = IncidentCreate(
        id="inc-103",
        serviceId="svc-cart-checkout",
        severity=Severity.P2,
        status=IncidentStatus.AWAITING_APPROVAL,
        openedAt=now - timedelta(minutes=10),
        summary="Memory leak detected on checkout pods",
        rootCause="Unclosed gRPC client connection pool accumulating in checkout worker",
        confidence=0.88,
    )
    storage.create_incident(inc_3)

    storage.add_incident_event(
        IncidentEvent(
            id="evt-103-1",
            incidentId="inc-103",
            timestamp=now - timedelta(minutes=10),
            type=EventType.SIGNAL,
            payload={"detector": "memory_leak", "memory_usage": "93%", "threshold": "85%"},
        )
    )
    storage.add_incident_event(
        IncidentEvent(
            id="evt-103-2",
            incidentId="inc-103",
            timestamp=now - timedelta(minutes=7),
            type=EventType.TOOL_CALL,
            payload={"tool": "fetch_logs", "filter": "ResourceExhausted|OOMKilled"},
        )
    )
    storage.add_incident_event(
        IncidentEvent(
            id="evt-103-3",
            incidentId="inc-103",
            timestamp=now - timedelta(minutes=4),
            type=EventType.HYPOTHESIS,
            payload={"cause": "Unclosed gRPC client connection pool leak", "confidence": 0.88},
        )
    )
    storage.add_incident_event(
        IncidentEvent(
            id="evt-103-4",
            incidentId="inc-103",
            timestamp=now - timedelta(minutes=2),
            type=EventType.ACTION,
            payload={
                "action": "rollback_deploy",
                "proposed_revision": "cart-checkout-v2.3.9",
                "target_service": "cart-checkout",
                "requires_approval": True,
                "confidence": 0.88,
            },
        )
    )
