"""Abstract repository interface for all Nightwatch storage collections."""

from abc import ABC, abstractmethod
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


class BaseRepository(ABC):
    """Abstract interface for all Nightwatch persistence operations."""

    # -------------------------------------------------------------------------
    # Services
    # -------------------------------------------------------------------------
    @abstractmethod
    def list_services(self) -> List[Service]:
        """List all monitored services."""
        pass

    @abstractmethod
    def get_service(self, service_id: str) -> Optional[Service]:
        """Fetch a single service by ID."""
        pass

    @abstractmethod
    def create_service(self, service_in: ServiceCreate) -> Service:
        """Register a new service."""
        pass

    @abstractmethod
    def update_service(self, service_id: str, update_in: ServiceUpdate) -> Optional[Service]:
        """Update service configurations."""
        pass

    @abstractmethod
    def delete_service(self, service_id: str) -> bool:
        """Delete a service and return True if deleted."""
        pass

    # -------------------------------------------------------------------------
    # Incidents & Events
    # -------------------------------------------------------------------------
    @abstractmethod
    def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[Severity] = None,
        service_id: Optional[str] = None,
    ) -> List[Incident]:
        """List incidents with optional filtering."""
        pass

    @abstractmethod
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Fetch an incident by ID."""
        pass

    @abstractmethod
    def create_incident(self, incident_in: IncidentCreate) -> Incident:
        """Open a new incident."""
        pass

    @abstractmethod
    def update_incident(
        self,
        incident_id: str,
        status: Optional[IncidentStatus] = None,
        root_cause: Optional[str] = None,
        confidence: Optional[float] = None,
        resolved_at: Optional[datetime] = None,
    ) -> Optional[Incident]:
        """Update incident details or lifecycle status."""
        pass

    @abstractmethod
    def list_incident_events(self, incident_id: str) -> List[IncidentEvent]:
        """Fetch timeline events for an incident."""
        pass

    @abstractmethod
    def add_incident_event(self, event_in: IncidentEvent) -> IncidentEvent:
        """Append an event to an incident timeline."""
        pass

    # -------------------------------------------------------------------------
    # Checks
    # -------------------------------------------------------------------------
    @abstractmethod
    def record_check(self, check: Check) -> Check:
        """Store a service health check sweep record."""
        pass

    @abstractmethod
    def list_checks(self, service_id: str, limit: int = 50) -> List[Check]:
        """Fetch recent checks for a service."""
        pass

    # -------------------------------------------------------------------------
    # Runbooks
    # -------------------------------------------------------------------------
    @abstractmethod
    def list_runbooks(self, limit: int = 50) -> List[Runbook]:
        """List saved runbook resolutions."""
        pass

    @abstractmethod
    def create_runbook(self, runbook: Runbook) -> Runbook:
        """Store a new runbook memory record."""
        pass

    # -------------------------------------------------------------------------
    # Audit Logs
    # -------------------------------------------------------------------------
    @abstractmethod
    def add_audit_log(self, entry: AuditLog) -> AuditLog:
        """Append to system audit log."""
        pass

    @abstractmethod
    def list_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        """List audit log records."""
        pass

    # -------------------------------------------------------------------------
    # Settings
    # -------------------------------------------------------------------------
    @abstractmethod
    def get_settings(self) -> SystemSettings:
        """Fetch global settings and kill switch."""
        pass

    @abstractmethod
    def update_kill_switch(self, kill_switch: bool) -> SystemSettings:
        """Toggle global agent kill switch."""
        pass
