"""Domain enums for Nightwatch data models."""

from enum import Enum


class Severity(str, Enum):
    """Incident severity levels."""
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class Criticality(str, Enum):
    """Service criticality levels for triage prioritization."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IncidentStatus(str, Enum):
    """Lifecycle statuses of an incident."""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    AWAITING_APPROVAL = "awaiting_approval"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"


class AutonomyLevel(str, Enum):
    """Agent autonomy permission ladder."""
    OBSERVE = "observe"
    SUGGEST = "suggest"
    ACT_WITH_APPROVAL = "act_with_approval"
    AUTO_ACT = "auto_act"


class EventType(str, Enum):
    """Types of events recorded in the incident timeline / reasoning trace."""
    SIGNAL = "signal"
    TOOL_CALL = "tool_call"
    HYPOTHESIS = "hypothesis"
    ACTION = "action"
    NOTIFICATION = "notification"
    APPROVAL = "approval"


class ServiceStatus(str, Enum):
    """Health status of monitored services."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"
