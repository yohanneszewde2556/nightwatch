"""Core detection and triage sweep service.

Executes periodic health and log scans across registered services,
enforces 2-consecutive-check confirmation before opening incidents (DT-3),
calculates severity, logs timeline events, sends Telegram alerts, and
auto-resolves incidents upon 3 consecutive healthy sweeps.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from app.detectors.health_checker import probe_service_health, probe_service_logs
from app.models.enums import (
    Criticality,
    EventType,
    IncidentStatus,
    ServiceStatus,
    Severity,
)
from app.models.schemas import (
    Check,
    Incident,
    IncidentCreate,
    IncidentEvent,
    Service,
    ServiceUpdate,
)
from app.notifiers.telegram import notify_incident_detected, notify_incident_resolved
from app.storage.base import BaseRepository

logger = logging.getLogger("nightwatch.detectors.sweep")


class DetectorEngine:
    """Manages failure confirmation states and sweep executions."""

    def __init__(self) -> None:
        self._consecutive_failures: Dict[str, int] = {}
        self._consecutive_healthy: Dict[str, int] = {}
        self._last_log_timestamps: Dict[str, str] = {}

    def reset_state(self) -> None:
        """Clear memory counters (useful for unit tests)."""
        self._consecutive_failures.clear()
        self._consecutive_healthy.clear()
        self._last_log_timestamps.clear()

    async def sweep_all_services(self, storage: BaseRepository) -> Dict[str, Any]:
        """Perform a full detection sweep across all registered active services."""
        services = storage.list_services()
        active_services = [s for s in services if not s.paused]

        results = {
            "services_checked": len(active_services),
            "incidents_created": 0,
            "incidents_resolved": 0,
            "checks": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        for service in active_services:
            res = await self.check_service(service, storage)
            results["checks"].append(res)
            if res.get("incident_created"):
                results["incidents_created"] += 1
            if res.get("incident_resolved"):
                results["incidents_resolved"] += 1

        return results

    async def check_service(
        self,
        service: Service,
        storage: BaseRepository,
    ) -> Dict[str, Any]:
        """Check a single service, evaluate health, and handle incident transitions."""
        # 1. Probe health endpoint
        http_status, latency_ms, error_msg = await probe_service_health(service.healthUrl)

        # 2. Probe recent structured logs
        since_time = self._last_log_timestamps.get(service.id)
        error_logs = await probe_service_logs(service.healthUrl, since=since_time, limit=20)
        if error_logs:
            # Update watermark to the newest log timestamp
            self._last_log_timestamps[service.id] = error_logs[0].get("timestamp")

        # 3. Record Check record in storage
        check = Check(
            id=f"chk-{uuid.uuid4().hex[:8]}",
            serviceId=service.id,
            timestamp=datetime.now(timezone.utc),
            httpStatus=http_status,
            latencyMs=latency_ms,
            errorLogCount=len(error_logs),
        )
        saved_check = storage.record_check(check)

        # 4. Determine health status
        is_hard_down = (http_status == 0 or http_status >= 500)
        has_error_spike = (len(error_logs) >= 3)
        is_slow = (latency_ms >= 4000.0)

        is_failing = is_hard_down or has_error_spike or is_slow

        incident_created = False
        incident_resolved = False

        if is_failing:
            # Increment failure counter, reset healthy counter
            self._consecutive_failures[service.id] = self._consecutive_failures.get(service.id, 0) + 1
            self._consecutive_healthy[service.id] = 0

            # Update service status in registry
            new_status = ServiceStatus.DOWN if is_hard_down else ServiceStatus.DEGRADED
            storage.update_service(
                service.id,
                ServiceUpdate(status=new_status),
            )

            # DT-3: Require 2 consecutive failures before opening an incident
            consecutive = self._consecutive_failures[service.id]
            logger.warning(
                "Service '%s' failing check (consecutive: %d, http=%d, latency=%.1fms, errors=%d)",
                service.name,
                consecutive,
                http_status,
                latency_ms,
                len(error_logs),
            )

            if consecutive >= 2:
                # Check for existing active incident
                active_incidents = [
                    inc for inc in storage.list_incidents(service_id=service.id)
                    if inc.status in (
                        IncidentStatus.DETECTED,
                        IncidentStatus.INVESTIGATING,
                        IncidentStatus.AWAITING_APPROVAL,
                        IncidentStatus.MITIGATING,
                    )
                ]

                if not active_incidents:
                    # Open new Incident
                    incident = await self._open_incident(
                        service=service,
                        http_status=http_status,
                        latency_ms=latency_ms,
                        error_msg=error_msg,
                        error_logs=error_logs,
                        check=saved_check,
                        storage=storage,
                    )
                    incident_created = True
                else:
                    # Append ongoing failure signal event
                    storage.add_incident_event(
                        IncidentEvent(
                            incidentId=active_incidents[0].id,
                            type=EventType.SIGNAL,
                            payload={
                                "source": "detector_sweep",
                                "http_status": http_status,
                                "latency_ms": latency_ms,
                                "error_count": len(error_logs),
                                "message": f"Service still unhealthy: HTTP {http_status}, latency {latency_ms:.1f}ms",
                            },
                        )
                    )

        else:
            # Service is healthy
            self._consecutive_healthy[service.id] = self._consecutive_healthy.get(service.id, 0) + 1
            self._consecutive_failures[service.id] = 0

            storage.update_service(
                service.id,
                ServiceUpdate(status=ServiceStatus.HEALTHY),
            )

            # Check if active incident can be closed (3 consecutive healthy checks)
            consecutive_healthy = self._consecutive_healthy[service.id]
            if consecutive_healthy >= 3:
                active_incidents = [
                    inc for inc in storage.list_incidents(service_id=service.id)
                    if inc.status in (
                        IncidentStatus.DETECTED,
                        IncidentStatus.INVESTIGATING,
                        IncidentStatus.AWAITING_APPROVAL,
                        IncidentStatus.MITIGATING,
                    )
                ]
                for inc in active_incidents:
                    storage.update_incident(
                        inc.id,
                        status=IncidentStatus.RESOLVED,
                        resolved_at=datetime.now(timezone.utc),
                    )
                    storage.add_incident_event(
                        IncidentEvent(
                            incidentId=inc.id,
                            type=EventType.ACTION,
                            payload={
                                "source": "detector_sweep",
                                "message": "Incident resolved: 3 consecutive healthy checks verified.",
                            },
                        )
                    )
                    logger.info("Auto-resolved incident %s after 3 healthy checks", inc.id)
                    await notify_incident_resolved(inc, service)
                    incident_resolved = True

        return {
            "service_id": service.id,
            "service_name": service.name,
            "http_status": http_status,
            "latency_ms": latency_ms,
            "error_logs": len(error_logs),
            "consecutive_failures": self._consecutive_failures.get(service.id, 0),
            "consecutive_healthy": self._consecutive_healthy.get(service.id, 0),
            "incident_created": incident_created,
            "incident_resolved": incident_resolved,
        }

    async def _open_incident(
        self,
        service: Service,
        http_status: int,
        latency_ms: float,
        error_msg: Optional[str],
        error_logs: List[Dict[str, Any]],
        check: Check,
        storage: BaseRepository,
    ) -> Incident:
        """Create new Incident and initial detection event in storage, and dispatch alert."""
        # 1. Triage Severity
        if service.criticality == Criticality.HIGH and (http_status == 0 or http_status >= 500 or len(error_logs) >= 5):
            severity = Severity.P1
        elif service.criticality == Criticality.HIGH or len(error_logs) >= 3 or latency_ms >= 4000.0:
            severity = Severity.P2
        else:
            severity = Severity.P3

        # 2. Formulate Summary
        if http_status == 0:
            summary = f"{service.name} unreachable: {error_msg or 'Connection refused'}"
        elif http_status >= 500:
            summary = f"{service.name} outage: Health check returned HTTP {http_status}"
        elif len(error_logs) >= 3:
            summary = f"High error rate on {service.name}: {len(error_logs)} 5xx errors detected in recent traffic"
        else:
            summary = f"{service.name} degraded latency: {latency_ms:.0f}ms response time"

        incident_id = f"inc-{uuid.uuid4().hex[:6]}"
        inc_in = IncidentCreate(
            id=incident_id,
            serviceId=service.id,
            severity=severity,
            status=IncidentStatus.DETECTED,
            summary=summary,
        )
        incident = storage.create_incident(inc_in)

        # 3. Record Initial Signal Event
        sample_stack = None
        if error_logs and error_logs[0].get("exception"):
            sample_stack = error_logs[0]["exception"][:400]

        event = IncidentEvent(
            id=f"evt-{uuid.uuid4().hex[:6]}",
            incidentId=incident.id,
            type=EventType.SIGNAL,
            payload={
                "source": "detector_sweep",
                "check_id": check.id,
                "http_status": http_status,
                "latency_ms": latency_ms,
                "error_count": len(error_logs),
                "error_details": error_msg,
                "sample_traceback": sample_stack,
                "message": f"Confirmed failure: {summary}",
            },
        )
        storage.add_incident_event(event)

        logger.info(
            "Opened new incident %s (%s) for service %s",
            incident.id,
            incident.severity,
            service.name,
        )

        # 4. Dispatch Telegram alert
        await notify_incident_detected(incident, service, check)

        return incident


# Singleton detector engine
detector_engine = DetectorEngine()
