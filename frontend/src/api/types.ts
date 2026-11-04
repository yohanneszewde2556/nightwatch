/** Domain types for Nightwatch frontend application matching SRS schemas. */

export type Severity = 'P1' | 'P2' | 'P3';
export type Criticality = 'low' | 'medium' | 'high';
export type IncidentStatus = 'detected' | 'investigating' | 'awaiting_approval' | 'mitigating' | 'resolved';
export type AutonomyLevel = 'observe' | 'suggest' | 'act_with_approval' | 'auto_act';
export type ServiceStatus = 'healthy' | 'degraded' | 'down' | 'unknown';
export type EventType = 'signal' | 'tool_call' | 'hypothesis' | 'action' | 'notification' | 'approval';

export interface Service {
  id: string;
  name: string;
  healthUrl: string;
  cloudRunService?: string | null;
  githubRepo?: string | null;
  criticality: Criticality;
  autonomyLevel: AutonomyLevel;
  status: ServiceStatus;
  lastCheckAt?: string | null;
  paused: boolean;
}

export interface ServiceCreate {
  id?: string;
  name: string;
  healthUrl: string;
  cloudRunService?: string | null;
  githubRepo?: string | null;
  criticality: Criticality;
  autonomyLevel: AutonomyLevel;
  paused?: boolean;
}

export interface ServiceUpdate {
  name?: string;
  healthUrl?: string;
  cloudRunService?: string | null;
  githubRepo?: string | null;
  criticality?: Criticality;
  autonomyLevel?: AutonomyLevel;
  status?: ServiceStatus;
  paused?: boolean;
}

export interface Incident {
  id: string;
  serviceId: string;
  severity: Severity;
  status: IncidentStatus;
  openedAt: string;
  resolvedAt?: string | null;
  summary: string;
  rootCause?: string | null;
  confidence?: number | null;
}

export interface IncidentEvent {
  id?: string;
  incidentId: string;
  timestamp: string;
  type: EventType;
  payload: Record<string, any>;
}

export interface SystemSettings {
  killSwitch: boolean;
  notificationTargets?: Record<string, any> | null;
  dailyGeminiBudget?: number | null;
}
