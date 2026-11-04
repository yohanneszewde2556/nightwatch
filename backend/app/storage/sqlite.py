"""SQLite implementation of the Nightwatch BaseRepository."""

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.enums import (
    AutonomyLevel,
    Criticality,
    EventType,
    IncidentStatus,
    ServiceStatus,
    Severity,
)
from app.models.schemas import (
    AuditLog,
    Check,
    Incident,
    IncidentCreate,
    IncidentEvent,
    Runbook,
    Service,
    ServiceCreate,
    ServiceUpdate,
    SystemSettings,
    utc_now,
)
from app.storage.base import BaseRepository


def _parse_dt(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except Exception:
        return None


def _format_dt(val: Optional[datetime]) -> Optional[str]:
    return val.isoformat() if val else None


class SQLiteRepository(BaseRepository):
    """Zero-dependency SQLite storage repository implementation."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                health_url TEXT NOT NULL,
                cloud_run_service TEXT,
                github_repo TEXT,
                criticality TEXT NOT NULL,
                autonomy_level TEXT NOT NULL,
                status TEXT NOT NULL,
                last_check_at TEXT,
                paused INTEGER NOT NULL DEFAULT 0
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                service_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                opened_at TEXT NOT NULL,
                resolved_at TEXT,
                summary TEXT NOT NULL,
                root_cause TEXT,
                confidence REAL,
                FOREIGN KEY (service_id) REFERENCES services (id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS incident_events (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                type TEXT NOT NULL,
                payload TEXT NOT NULL,
                FOREIGN KEY (incident_id) REFERENCES incidents (id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id TEXT PRIMARY KEY,
                service_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                http_status INTEGER,
                latency_ms REAL,
                error_log_count INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (service_id) REFERENCES services (id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS runbooks (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                symptoms TEXT NOT NULL,
                root_cause TEXT NOT NULL,
                fix_applied TEXT NOT NULL,
                embedding TEXT,
                outcome TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT NOT NULL,
                approved_by TEXT,
                result TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                kill_switch INTEGER NOT NULL DEFAULT 0,
                notification_targets TEXT,
                daily_gemini_budget INTEGER
            );
            """)

            # Ensure default settings row exists
            cursor.execute("""
            INSERT OR IGNORE INTO settings (id, kill_switch, notification_targets, daily_gemini_budget)
            VALUES (1, 0, '{}', 100);
            """)

            conn.commit()

    # -------------------------------------------------------------------------
    # Services
    # -------------------------------------------------------------------------
    def list_services(self) -> List[Service]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM services ORDER BY name ASC")
            rows = cursor.fetchall()
            return [
                Service(
                    id=row["id"],
                    name=row["name"],
                    healthUrl=row["health_url"],
                    cloudRunService=row["cloud_run_service"],
                    githubRepo=row["github_repo"],
                    criticality=Criticality(row["criticality"]),
                    autonomyLevel=AutonomyLevel(row["autonomy_level"]),
                    status=ServiceStatus(row["status"]),
                    lastCheckAt=_parse_dt(row["last_check_at"]),
                    paused=bool(row["paused"]),
                )
                for row in rows
            ]

    def get_service(self, service_id: str) -> Optional[Service]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM services WHERE id = ?", (service_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Service(
                id=row["id"],
                name=row["name"],
                healthUrl=row["health_url"],
                cloudRunService=row["cloud_run_service"],
                githubRepo=row["github_repo"],
                criticality=Criticality(row["criticality"]),
                autonomyLevel=AutonomyLevel(row["autonomy_level"]),
                status=ServiceStatus(row["status"]),
                lastCheckAt=_parse_dt(row["last_check_at"]),
                paused=bool(row["paused"]),
            )

    def create_service(self, service_in: ServiceCreate) -> Service:
        svc_id = service_in.id or f"svc-{uuid.uuid4().hex[:8]}"
        status_val = ServiceStatus.UNKNOWN.value
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO services (
                    id, name, health_url, cloud_run_service, github_repo,
                    criticality, autonomy_level, status, last_check_at, paused
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    svc_id,
                    service_in.name,
                    str(service_in.healthUrl),
                    service_in.cloudRunService,
                    service_in.githubRepo,
                    service_in.criticality.value,
                    service_in.autonomyLevel.value,
                    status_val,
                    None,
                    1 if service_in.paused else 0,
                ),
            )
            conn.commit()

        return Service(
            id=svc_id,
            name=service_in.name,
            healthUrl=service_in.healthUrl,
            cloudRunService=service_in.cloudRunService,
            githubRepo=service_in.githubRepo,
            criticality=service_in.criticality,
            autonomyLevel=service_in.autonomyLevel,
            status=ServiceStatus.UNKNOWN,
            lastCheckAt=None,
            paused=service_in.paused,
        )

    def update_service(self, service_id: str, update_in: ServiceUpdate) -> Optional[Service]:
        current = self.get_service(service_id)
        if not current:
            return None

        name = update_in.name if update_in.name is not None else current.name
        health_url = str(update_in.healthUrl) if update_in.healthUrl is not None else current.healthUrl
        cloud_run = update_in.cloudRunService if update_in.cloudRunService is not None else current.cloudRunService
        repo = update_in.githubRepo if update_in.githubRepo is not None else current.githubRepo
        criticality = update_in.criticality if update_in.criticality is not None else current.criticality
        autonomy = update_in.autonomyLevel if update_in.autonomyLevel is not None else current.autonomyLevel
        status_val = update_in.status if update_in.status is not None else current.status
        paused = update_in.paused if update_in.paused is not None else current.paused

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE services
                SET name = ?, health_url = ?, cloud_run_service = ?, github_repo = ?,
                    criticality = ?, autonomy_level = ?, status = ?, paused = ?
                WHERE id = ?
                """,
                (
                    name,
                    health_url,
                    cloud_run,
                    repo,
                    criticality.value,
                    autonomy.value,
                    status_val.value,
                    1 if paused else 0,
                    service_id,
                ),
            )
            conn.commit()

        return self.get_service(service_id)

    def delete_service(self, service_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM services WHERE id = ?", (service_id,))
            conn.commit()
            return cursor.rowcount > 0

    # -------------------------------------------------------------------------
    # Incidents & Events
    # -------------------------------------------------------------------------
    def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[Severity] = None,
        service_id: Optional[str] = None,
    ) -> List[Incident]:
        query = "SELECT * FROM incidents WHERE 1=1"
        params: List[Any] = []
        if status:
            query += " AND status = ?"
            params.append(status.value)
        if severity:
            query += " AND severity = ?"
            params.append(severity.value)
        if service_id:
            query += " AND service_id = ?"
            params.append(service_id)
        query += " ORDER BY opened_at DESC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                Incident(
                    id=row["id"],
                    serviceId=row["service_id"],
                    severity=Severity(row["severity"]),
                    status=IncidentStatus(row["status"]),
                    openedAt=_parse_dt(row["opened_at"]) or utc_now(),
                    resolvedAt=_parse_dt(row["resolved_at"]),
                    summary=row["summary"],
                    rootCause=row["root_cause"],
                    confidence=row["confidence"],
                )
                for row in rows
            ]

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Incident(
                id=row["id"],
                serviceId=row["service_id"],
                severity=Severity(row["severity"]),
                status=IncidentStatus(row["status"]),
                openedAt=_parse_dt(row["opened_at"]) or utc_now(),
                resolvedAt=_parse_dt(row["resolved_at"]),
                summary=row["summary"],
                rootCause=row["root_cause"],
                confidence=row["confidence"],
            )

    def create_incident(self, incident_in: IncidentCreate) -> Incident:
        inc_id = incident_in.id or f"inc-{uuid.uuid4().hex[:8]}"
        opened_at_str = _format_dt(incident_in.openedAt)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO incidents (
                    id, service_id, severity, status, opened_at, resolved_at, summary, root_cause, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inc_id,
                    incident_in.serviceId,
                    incident_in.severity.value,
                    incident_in.status.value,
                    opened_at_str,
                    None,
                    incident_in.summary,
                    incident_in.rootCause,
                    incident_in.confidence,
                ),
            )
            conn.commit()

        return Incident(
            id=inc_id,
            serviceId=incident_in.serviceId,
            severity=incident_in.severity,
            status=incident_in.status,
            openedAt=incident_in.openedAt,
            resolvedAt=None,
            summary=incident_in.summary,
            rootCause=incident_in.rootCause,
            confidence=incident_in.confidence,
        )

    def update_incident(
        self,
        incident_id: str,
        status: Optional[IncidentStatus] = None,
        root_cause: Optional[str] = None,
        confidence: Optional[float] = None,
        resolved_at: Optional[datetime] = None,
    ) -> Optional[Incident]:
        current = self.get_incident(incident_id)
        if not current:
            return None

        new_status = status if status is not None else current.status
        new_cause = root_cause if root_cause is not None else current.rootCause
        new_conf = confidence if confidence is not None else current.confidence
        new_resolved = resolved_at if resolved_at is not None else current.resolvedAt

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE incidents
                SET status = ?, root_cause = ?, confidence = ?, resolved_at = ?
                WHERE id = ?
                """,
                (
                    new_status.value,
                    new_cause,
                    new_conf,
                    _format_dt(new_resolved),
                    incident_id,
                ),
            )
            conn.commit()

        return self.get_incident(incident_id)

    def list_incident_events(self, incident_id: str) -> List[IncidentEvent]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM incident_events WHERE incident_id = ? ORDER BY timestamp ASC",
                (incident_id,),
            )
            rows = cursor.fetchall()
            return [
                IncidentEvent(
                    id=row["id"],
                    incidentId=row["incident_id"],
                    timestamp=_parse_dt(row["timestamp"]) or utc_now(),
                    type=EventType(row["type"]),
                    payload=json.loads(row["payload"]),
                )
                for row in rows
            ]

    def add_incident_event(self, event_in: IncidentEvent) -> IncidentEvent:
        evt_id = event_in.id or f"evt-{uuid.uuid4().hex[:8]}"
        payload_str = json.dumps(event_in.payload)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO incident_events (id, incident_id, timestamp, type, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    evt_id,
                    event_in.incidentId,
                    _format_dt(event_in.timestamp),
                    event_in.type.value,
                    payload_str,
                ),
            )
            conn.commit()

        event_copy = event_in.model_copy()
        event_copy.id = evt_id
        return event_copy

    # -------------------------------------------------------------------------
    # Checks
    # -------------------------------------------------------------------------
    def record_check(self, check: Check) -> Check:
        chk_id = check.id or f"chk-{uuid.uuid4().hex[:8]}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO checks (id, service_id, timestamp, http_status, latency_ms, error_log_count)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    chk_id,
                    check.serviceId,
                    _format_dt(check.timestamp),
                    check.httpStatus,
                    check.latencyMs,
                    check.errorLogCount,
                ),
            )
            # Update service last_check_at
            cursor.execute(
                "UPDATE services SET last_check_at = ? WHERE id = ?",
                (_format_dt(check.timestamp), check.serviceId),
            )
            conn.commit()

        copy_chk = check.model_copy()
        copy_chk.id = chk_id
        return copy_chk

    def list_checks(self, service_id: str, limit: int = 50) -> List[Check]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM checks WHERE service_id = ? ORDER BY timestamp DESC LIMIT ?
                """,
                (service_id, limit),
            )
            rows = cursor.fetchall()
            return [
                Check(
                    id=row["id"],
                    serviceId=row["service_id"],
                    timestamp=_parse_dt(row["timestamp"]) or utc_now(),
                    httpStatus=row["http_status"],
                    latencyMs=row["latency_ms"],
                    errorLogCount=row["error_log_count"],
                )
                for row in rows
            ]

    # -------------------------------------------------------------------------
    # Runbooks
    # -------------------------------------------------------------------------
    def list_runbooks(self, limit: int = 50) -> List[Runbook]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM runbooks ORDER BY created_at DESC LIMIT ?", (limit,)
            )
            rows = cursor.fetchall()
            return [
                Runbook(
                    id=row["id"],
                    incidentId=row["incident_id"],
                    symptoms=row["symptoms"],
                    rootCause=row["root_cause"],
                    fixApplied=row["fix_applied"],
                    embedding=json.loads(row["embedding"]) if row["embedding"] else None,
                    outcome=row["outcome"],
                    createdAt=_parse_dt(row["created_at"]) or utc_now(),
                )
                for row in rows
            ]

    def create_runbook(self, runbook: Runbook) -> Runbook:
        rb_id = runbook.id or f"rb-{uuid.uuid4().hex[:8]}"
        emb_str = json.dumps(runbook.embedding) if runbook.embedding is not None else None
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO runbooks (
                    id, incident_id, symptoms, root_cause, fix_applied, embedding, outcome, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rb_id,
                    runbook.incidentId,
                    runbook.symptoms,
                    runbook.rootCause,
                    runbook.fixApplied,
                    emb_str,
                    runbook.outcome,
                    _format_dt(runbook.createdAt),
                ),
            )
            conn.commit()

        copy_rb = runbook.model_copy()
        copy_rb.id = rb_id
        return copy_rb

    # -------------------------------------------------------------------------
    # Audit Logs
    # -------------------------------------------------------------------------
    def add_audit_log(self, entry: AuditLog) -> AuditLog:
        log_id = entry.id or f"aud-{uuid.uuid4().hex[:8]}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_logs (id, timestamp, actor, action, target, approved_by, result)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_id,
                    _format_dt(entry.timestamp),
                    entry.actor,
                    entry.action,
                    entry.target,
                    entry.approvedBy,
                    entry.result,
                ),
            )
            conn.commit()

        copy_log = entry.model_copy()
        copy_log.id = log_id
        return copy_log

    def list_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
            rows = cursor.fetchall()
            return [
                AuditLog(
                    id=row["id"],
                    timestamp=_parse_dt(row["timestamp"]) or utc_now(),
                    actor=row["actor"],
                    action=row["action"],
                    target=row["target"],
                    approvedBy=row["approved_by"],
                    result=row["result"],
                )
                for row in rows
            ]

    # -------------------------------------------------------------------------
    # Settings
    # -------------------------------------------------------------------------
    def get_settings(self) -> SystemSettings:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM settings WHERE id = 1")
            row = cursor.fetchone()
            if not row:
                return SystemSettings(killSwitch=False)
            targets = json.loads(row["notification_targets"]) if row["notification_targets"] else None
            return SystemSettings(
                killSwitch=bool(row["kill_switch"]),
                notificationTargets=targets,
                dailyGeminiBudget=row["daily_gemini_budget"],
            )

    def update_kill_switch(self, kill_switch: bool) -> SystemSettings:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE settings SET kill_switch = ? WHERE id = 1",
                (1 if kill_switch else 0,),
            )
            conn.commit()
        return self.get_settings()
