import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  Cpu,
  FileSearch,
  MessageSquare,
  Radio,
  RefreshCw,
  ShieldAlert,
  ThumbsDown,
  ThumbsUp,
  Wrench,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Incident, IncidentEvent } from '../api/types';
import { SeverityBadge } from '../components/SeverityBadge';

export const WarRoomPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [events, setEvents] = useState<IncidentEvent[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadIncidentData = async () => {
    if (!id) return;
    try {
      const [inc, evts] = await Promise.all([
        apiClient.getIncident(id),
        apiClient.getIncidentEvents(id),
      ]);
      setIncident(inc);
      setEvents(evts);
    } catch (err: any) {
      console.error('Failed to load incident:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadIncidentData();
    const timer = setInterval(loadIncidentData, 10000);
    return () => clearInterval(timer);
  }, [id]);

  const handleApprove = async () => {
    if (!id) return;
    setActionLoading(true);
    setActionMessage(null);
    try {
      await apiClient.approveAction(id, 'Approved via War-Room dashboard');
      setActionMessage('Action approved successfully.');
      loadIncidentData();
    } catch (err: any) {
      setActionMessage(`Notice: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!id) return;
    const reason = prompt('Please enter reason for rejection:');
    if (!reason) return;
    setActionLoading(true);
    setActionMessage(null);
    try {
      await apiClient.rejectAction(id, reason);
      setActionMessage('Action rejected.');
      loadIncidentData();
    } catch (err: any) {
      setActionMessage(`Notice: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const renderEventIcon = (type: string) => {
    switch (type) {
      case 'signal':
        return <Radio size={18} color="#f87171" />;
      case 'tool_call':
        return <Wrench size={18} color="#38bdf8" />;
      case 'hypothesis':
        return <Cpu size={18} color="#a855f7" />;
      case 'action':
        return <FileSearch size={18} color="#fbbf24" />;
      case 'approval':
        return <CheckCircle2 size={18} color="#34d399" />;
      case 'notification':
        return <MessageSquare size={18} color="#60a5fa" />;
      default:
        return <Clock size={18} color="#94a3b8" />;
    }
  };

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 0', color: '#94a3b8' }}>
        <RefreshCw size={24} className="spin" style={{ marginBottom: '1rem' }} />
        <p>Loading war-room timeline...</p>
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <h2>Incident Not Found</h2>
        <p style={{ color: '#94a3b8', margin: '1rem 0' }}>The incident '{id}' does not exist.</p>
        <Link to="/" className="btn btn-outline">
          <ArrowLeft size={16} /> Back to Overview
        </Link>
      </div>
    );
  }

  return (
    <div>
      {/* Back button & Title */}
      <div style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Link to="/" className="btn btn-outline" style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}>
          <ArrowLeft size={14} />
          <span>Back to Overview</span>
        </Link>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
          Incident ID: <code style={{ color: '#f8fafc' }}>{incident.id}</code>
        </div>
      </div>

      {/* Incident Header Card */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <SeverityBadge severity={incident.severity} />
              <span className="badge" style={{
                backgroundColor: incident.status === 'resolved' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                color: incident.status === 'resolved' ? '#34d399' : '#f87171',
              }}>
                {incident.status.replace('_', ' ')}
              </span>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                Service: <strong>{incident.serviceId}</strong>
              </span>
            </div>
            <h1 style={{ fontSize: '1.35rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
              {incident.summary}
            </h1>
          </div>

          {/* Action Approval Gate */}
          {incident.status === 'awaiting_approval' && (
            <div style={{
              display: 'flex',
              gap: '0.5rem',
              backgroundColor: 'rgba(245, 158, 11, 0.1)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              padding: '0.75rem',
              borderRadius: '0.5rem',
            }}>
              <button
                onClick={handleApprove}
                disabled={actionLoading}
                className="btn btn-primary"
                style={{ backgroundColor: '#10b981' }}
              >
                <ThumbsUp size={14} />
                <span>Approve Fix</span>
              </button>
              <button
                onClick={handleReject}
                disabled={actionLoading}
                className="btn btn-danger"
              >
                <ThumbsDown size={14} />
                <span>Reject</span>
              </button>
            </div>
          )}
        </div>

        {actionMessage && (
          <div style={{
            marginTop: '1rem',
            padding: '0.65rem 0.85rem',
            borderRadius: '0.375rem',
            backgroundColor: 'rgba(56, 189, 248, 0.1)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            color: '#38bdf8',
            fontSize: '0.825rem',
          }}>
            {actionMessage}
          </div>
        )}

        {/* RCA & Evidence */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
          marginTop: '1.5rem',
          paddingTop: '1.25rem',
          borderTop: '1px solid var(--border-subtle)',
        }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>
              Root Cause Analysis
            </div>
            <div style={{ marginTop: '0.35rem', fontSize: '0.9rem', color: incident.rootCause ? '#f8fafc' : '#94a3b8' }}>
              {incident.rootCause || 'Investigation in progress...'}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>
              Confidence Score
            </div>
            <div style={{ marginTop: '0.35rem', fontSize: '0.9rem', fontWeight: 600, color: '#38bdf8' }}>
              {incident.confidence ? `${(incident.confidence * 100).toFixed(0)}%` : 'Pending'}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>
              Timeline Timing
            </div>
            <div style={{ marginTop: '0.35rem', fontSize: '0.85rem', color: '#cbd5e1' }}>
              Opened: {new Date(incident.openedAt).toLocaleTimeString()}
              {incident.resolvedAt && ` • Resolved: ${new Date(incident.resolvedAt).toLocaleTimeString()}`}
            </div>
          </div>
        </div>
      </div>

      {/* War-Room Timeline & Reasoning Trace */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldAlert size={18} color="#10b981" />
            <h3 className="section-title">Agent Reasoning Trace & Timeline</h3>
          </div>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
            {events.length} event(s) recorded
          </span>
        </div>

        <div className="timeline">
          {events.map((evt, idx) => (
            <div key={evt.id || idx} className="timeline-item">
              <div className="timeline-icon">
                {renderEventIcon(evt.type)}
              </div>
              <div className="timeline-content">
                <div className="timeline-header">
                  <span className="timeline-type">{evt.type.replace('_', ' ')}</span>
                  <span className="timeline-time">
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="timeline-payload">
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {JSON.stringify(evt.payload, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
