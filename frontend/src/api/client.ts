/** Typed API client for Nightwatch backend. */

import {
  Incident,
  IncidentEvent,
  IncidentStatus,
  Service,
  ServiceCreate,
  ServiceUpdate,
  Severity,
  SystemSettings,
} from './types';

const TOKEN_KEY = 'nightwatch_dashboard_token';
const API_BASE = '/api';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

class NightwatchClient {
  private getToken(): string | null {
    return sessionStorage.getItem(TOKEN_KEY);
  }

  setToken(token: string): void {
    sessionStorage.setItem(TOKEN_KEY, token);
  }

  clearToken(): void {
    sessionStorage.removeItem(TOKEN_KEY);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.clearToken();
      window.dispatchEvent(new CustomEvent('nightwatch:unauthorized'));
      throw new ApiError(401, 'Unauthorized or session expired');
    }

    if (!response.ok) {
      let errorMsg = `Request failed (${response.status})`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          errorMsg = errorJson.detail;
        }
      } catch {
        // use fallback error message
      }
      throw new ApiError(response.status, errorMsg);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // Auth verification
  async verifyPassword(password: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE}/services`, {
        headers: {
          Authorization: `Bearer ${password}`,
        },
      });
      if (response.ok) {
        this.setToken(password);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  // Services
  async getServices(): Promise<Service[]> {
    return this.request<Service[]>('/services');
  }

  async getService(id: string): Promise<Service> {
    return this.request<Service>(`/services/${id}`);
  }

  async createService(payload: ServiceCreate): Promise<Service> {
    return this.request<Service>('/services', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateService(id: string, payload: ServiceUpdate): Promise<Service> {
    return this.request<Service>(`/services/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteService(id: string): Promise<void> {
    return this.request<void>(`/services/${id}`, {
      method: 'DELETE',
    });
  }

  // Incidents
  async getIncidents(filters?: {
    status?: IncidentStatus;
    severity?: Severity;
    serviceId?: string;
  }): Promise<Incident[]> {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.severity) params.append('severity', filters.severity);
    if (filters?.serviceId) params.append('service_id', filters.serviceId);

    const qs = params.toString() ? `?${params.toString()}` : '';
    return this.request<Incident[]>(`/incidents${qs}`);
  }

  async getIncident(id: string): Promise<Incident> {
    return this.request<Incident>(`/incidents/${id}`);
  }

  async getIncidentEvents(id: string): Promise<IncidentEvent[]> {
    return this.request<IncidentEvent[]>(`/incidents/${id}/events`);
  }

  async approveAction(id: string, comment?: string): Promise<void> {
    return this.request<void>(`/incidents/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approvedBy: 'dashboard-user', comment }),
    });
  }

  async rejectAction(id: string, reason: string): Promise<void> {
    return this.request<void>(`/incidents/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ rejectedBy: 'dashboard-user', reason }),
    });
  }

  // Settings & Kill switch
  async getSettings(): Promise<SystemSettings> {
    return this.request<SystemSettings>('/settings');
  }

  async setKillSwitch(killSwitch: boolean): Promise<SystemSettings> {
    return this.request<SystemSettings>('/settings/kill-switch', {
      method: 'POST',
      body: JSON.stringify({ killSwitch }),
    });
  }
}

export const apiClient = new NightwatchClient();
