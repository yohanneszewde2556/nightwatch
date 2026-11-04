import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, AlertTriangle, CheckCircle, ExternalLink, RefreshCw, Server } from 'lucide-react';
import { apiClient } from '../api/client';
import { Incident, Service } from '../api/types';
import { StatusBadge } from '../components/StatusBadge';
import { SeverityBadge } from '../components/SeverityBadge';

export const OverviewPage: React.FC = () => {
  const [services, setServices] = useState<Service[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const [svcData, incData] = await Promise.all([
        apiClient.getServices(),
        apiClient.getIncidents(),
      ]);
      setServices(svcData);
      setIncidents(incData);
    } catch (err: any) {
      console.error('Failed to load overview data:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, 15000);
    return () => clearInterval(timer);
  }, []);

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadData();
  };

  const activeIncidents = incidents.filter((i) => i.status !== 'resolved');
  const allHealthy = services.length > 0 && services.every((s) => s.status === 'healthy') && activeIncidents.length === 0;

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 0', color: '#94a3b8' }}>
        <RefreshCw size={24} className="spin" style={{ marginBottom: '1rem' }} />
        <p>Loading Nightwatch telemetry...</p>
      </div>
    );
  }

  return (
    <div>
      {/* Calm Status Banner */}
      <div
        style={{
          backgroundColor: allHealthy ? 'rgba(16, 185, 129, 0.08)' : 'rgba(245, 158, 11, 0.08)',
          border: `1px solid ${allHealthy ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)'}`,
          borderRadius: '0.75rem',
          padding: '1.25rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1.75rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          {allHealthy ? (
            <CheckCircle size={28} color="#10b981" />
          ) : (
            <AlertTriangle size={28} color="#f59e0b" />
          )}
          <div>
            <h2 style={{ fontSize: '1.05rem', fontWeight: 600 }}>
              {allHealthy ? 'All Monitored Services Healthy' : `${activeIncidents.length} Active Incident(s) Detected`}
            </h2>
            <p style={{ fontSize: '0.825rem', color: '#94a3b8', marginTop: '0.15rem' }}>
              {allHealthy
                ? 'Nightwatch is quietly monitoring health endpoints and Cloud Run error logs.'
                : 'Nightwatch AI SRE is investigating root causes with approval gates active.'}
            </p>
          </div>
        </div>

        <button
          onClick={handleRefresh}
          className="btn btn-outline"
          disabled={isRefreshing}
          title="Refresh telemetry"
        >
          <RefreshCw size={14} className={isRefreshing ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Monitored Services */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Server size={18} color="#38bdf8" />
            <h3 className="section-title">Monitored Services ({services.length})</h3>
          </div>
          <Link to="/services" className="btn btn-outline" style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}>
            Manage Services
          </Link>
        </div>

        <div className="service-grid">
          {services.map((svc) => (
            <div key={svc.id} className="service-card">
              <div className="service-header">
                <div>
                  <h4 className="service-name">{svc.name}</h4>
                  <div className="service-meta" style={{ marginTop: '0.25rem' }}>
                    <span>{svc.cloudRunService || 'Cloud Run: N/A'}</span>
                    <span>{svc.githubRepo || 'Repo: N/A'}</span>
                  </div>
                </div>
                <StatusBadge status={svc.status} />
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingTop: '0.75rem',
                borderTop: '1px solid var(--border-subtle)',
                fontSize: '0.8rem',
                color: '#94a3b8',
              }}>
                <div>
                  Autonomy: <strong style={{ color: '#f8fafc' }}>{svc.autonomyLevel.replace('_', ' ')}</strong>
                </div>
                <div style={{ fontSize: '0.75rem' }}>
                  {svc.paused ? <span style={{ color: '#f59e0b' }}>Paused</span> : 'Active'}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Incidents Table */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={18} color="#f87171" />
            <h3 className="section-title">Incidents ({incidents.length})</h3>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="incident-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Incident ID</th>
                <th>Summary</th>
                <th>Status</th>
                <th>Opened</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((inc) => (
                <tr key={inc.id} className="incident-row">
                  <td>
                    <SeverityBadge severity={inc.severity} />
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                    {inc.id}
                  </td>
                  <td>
                    <div style={{ fontWeight: 500 }}>{inc.summary}</div>
                    {inc.rootCause && (
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                        RCA: {inc.rootCause}
                      </div>
                    )}
                  </td>
                  <td>
                    <span className="badge" style={{
                      backgroundColor: inc.status === 'resolved' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      color: inc.status === 'resolved' ? '#34d399' : '#f87171',
                    }}>
                      {inc.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                    {new Date(inc.openedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td>
                    <Link
                      to={`/incidents/${inc.id}`}
                      className="btn btn-outline"
                      style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                    >
                      <span>War-Room</span>
                      <ExternalLink size={12} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
