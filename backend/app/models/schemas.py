"""Pydantic v2 schemas and models matching the SRS data model."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl

from app.models.enums import (
    AutonomyLevel,
    Criticality,
    EventType,
    IncidentStatus,
    ServiceStatus,
    Severity,
)


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


# ==============================================================================
# Service Schemas
# ==============================================================================

class ServiceBase(BaseModel):
    name: str = Field(..., description="Service display name")
    healthUrl: str = Field(..., description="Health check endpoint URL")
    cloudRunService: Optional[str] = Field(None, description="Cloud Run service identifier")
    githubRepo: Optional[str] = Field(None, description="Linked GitHub repo, e.g. org/repo")
    criticality: Criticality = Field(Criticality.MEDIUM, description="Criticality level")
    autonomyLevel: AutonomyLevel = Field(AutonomyLevel.OBSERVE, description="Permitted autonomy level")
    paused: bool = Field(False, description="Whether automated sweeps are paused")


class ServiceCreate(ServiceBase):
    """Schema for registering a service."""
    id: Optional[str] = Field(None, description="Optional custom ID; generated if omitted")


class ServiceUpdate(BaseModel):
    """Schema for editing service settings, autonomy, or pausing."""
    name: Optional[str] = None
    healthUrl: Optional[str] = None
    cloudRunService: Optional[str] = None
    githubRepo: Optional[str] = None
    criticality: Optional[Criticality] = None
    autonomyLevel: Optional[AutonomyLevel] = None
    status: Optional[ServiceStatus] = None
    paused: Optional[bool] = None


class Service(ServiceBase):
    """Stored service model."""
    id: str
    status: ServiceStatus = ServiceStatus.UNKNOWN
    lastCheckAt: Optional[datetime] = None


# ==============================================================================
# Check Schemas
# ==============================================================================

class Check(BaseModel):
    """Periodic health and telemetry check record."""
    id: Optional[str] = None
    serviceId: str
    timestamp: datetime = Field(default_factory=utc_now)
    httpStatus: Optional[int] = None
    latencyMs: Optional[float] = None
    errorLogCount: int = 0


# ==============================================================================
# Incident & IncidentEvent Schemas
# ==============================================================================

class IncidentBase(BaseModel):
    serviceId: str
    severity: Severity = Severity.P2
    summary: str
    rootCause: Optional[str] = None
    confidence: Optional[float] = None


class IncidentCreate(IncidentBase):
    id: Optional[str] = None
    status: IncidentStatus = IncidentStatus.DETECTED
    openedAt: datetime = Field(default_factory=utc_now)


class Incident(IncidentBase):
    id: str
    status: IncidentStatus = IncidentStatus.DETECTED
    openedAt: datetime = Field(default_factory=utc_now)
    resolvedAt: Optional[datetime] = None


class IncidentEvent(BaseModel):
    """Event in an incident's timeline or reasoning trace."""
    id: Optional[str] = None
    incidentId: str
    timestamp: datetime = Field(default_factory=utc_now)
    type: EventType
    payload: Dict[str, Any] = Field(default_factory=dict)


# ==============================================================================
# Runbook & AuditLog Schemas
# ==============================================================================

class Runbook(BaseModel):
    """Searchable knowledge record of a resolved incident and fix."""
    id: Optional[str] = None
    incidentId: str
    symptoms: str
    rootCause: str
    fixApplied: str
    embedding: Optional[List[float]] = None
    outcome: str
    createdAt: datetime = Field(default_factory=utc_now)


class AuditLog(BaseModel):
    """Record of an automated or human-approved action."""
    id: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)
    actor: str = Field(..., description="'agent' or user name")
    action: str
    target: str
    approvedBy: Optional[str] = None
    result: str


# ==============================================================================
# Settings (Kill Switch) Schemas
# ==============================================================================

class SystemSettings(BaseModel):
    """Global system settings and kill switch."""
    killSwitch: bool = Field(False, description="When true, halts all agent automated actions")
    notificationTargets: Optional[Dict[str, Any]] = None
    dailyGeminiBudget: Optional[int] = None


class KillSwitchUpdate(BaseModel):
    killSwitch: bool = Field(..., description="Desired kill switch state")


# ==============================================================================
# Action / Request Schemas
# ==============================================================================

class ActionApprovalRequest(BaseModel):
    approvedBy: Optional[str] = "dashboard-user"
    comment: Optional[str] = None


class ActionRejectionRequest(BaseModel):
    reason: str = Field(..., description="Reason for rejection")
    rejectedBy: Optional[str] = "dashboard-user"


class AgentChatRequest(BaseModel):
    message: str = Field(..., description="User prompt or question")
    serviceId: Optional[str] = None


class ChaosRequest(BaseModel):
    serviceId: Optional[str] = "svc-demo-shop"
    scenario: str = Field(..., description="Failure scenario: crash, slow, bad_deploy, reset")


class WeeklyReport(BaseModel):
    period: str
    uptimePercent: float
    totalIncidents: int
    resolvedIncidents: int
    activeIncidents: int
    mttrMinutes: float
    costAvoidedUsd: float
    topFailureModes: List[Dict[str, Any]]
    serviceMetrics: List[Dict[str, Any]]
    recentPostmortems: List[Dict[str, Any]]
