"""Firestore storage adapter stub.

This module provides a stub for Google Cloud Firestore integration.
It implements the BaseRepository interface and is clearly marked as a placeholder
for production Cloud Run deployments. For the local foundation build, SQLite is used.
"""

from datetime import datetime
from typing import List, Optional

from app.models.enums import IncidentStatus, Severity
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
)
from app.storage.base import BaseRepository


class FirestoreRepository(BaseRepository):
    """Google Cloud Firestore adapter stub.

    Raises NotImplementedError on all operations. To activate, install
    `google-cloud-firestore` and set `STORAGE_BACKEND=firestore`.
    """

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id
        # In production:
        # from google.cloud import firestore
        # self.client = firestore.Client(project=project_id)

    def list_services(self) -> List[Service]:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def get_service(self, service_id: str) -> Optional[Service]:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def create_service(self, service_in: ServiceCreate) -> Service:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def update_service(self, service_id: str, update_in: ServiceUpdate) -> Optional[Service]:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def delete_service(self, service_id: str) -> bool:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[Severity] = None,
        service_id: Optional[str] = None,
    ) -> List[Incident]:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def create_incident(self, incident_in: IncidentCreate) -> Incident:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def update_incident(
        self,
        incident_id: str,
        status: Optional[IncidentStatus] = None,
        root_cause: Optional[str] = None,
        confidence: Optional[float] = None,
        resolved_at: Optional[datetime] = None,
    ) -> Optional[Incident]:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def list_incident_events(self, incident_id: str) -> List[IncidentEvent]:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def add_incident_event(self, event_in: IncidentEvent) -> IncidentEvent:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def record_check(self, check: Check) -> Check:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def list_checks(self, service_id: str, limit: int = 50) -> List[Check]:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def list_runbooks(self, limit: int = 50) -> List[Runbook]:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def create_runbook(self, runbook: Runbook) -> Runbook:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def add_audit_log(self, entry: AuditLog) -> AuditLog:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def list_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def get_settings(self) -> SystemSettings:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")

    def update_kill_switch(self, kill_switch: bool) -> SystemSettings:
        raise NotImplementedError("Firestore adapter is a stub in this foundation phase.")
