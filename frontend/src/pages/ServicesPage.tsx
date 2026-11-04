import React, { useEffect, useState } from 'react';
import { Plus, Trash2, Pause, Play, AlertCircle, RefreshCw } from 'lucide-react';
import { apiClient } from '../api/client';
import { AutonomyLevel, Criticality, Service, ServiceCreate } from '../api/types';
import { StatusBadge } from '../components/StatusBadge';

export const ServicesPage: React.FC = () => {
  const [services, setServices] = useState<Service[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [name, setName] = useState('');
  const [healthUrl, setHealthUrl] = useState('');
  const [cloudRunService, setCloudRunService] = useState('');
  const [githubRepo, setGithubRepo] = useState('');
  const [criticality, setCriticality] = useState<Criticality>('medium');
  const [autonomyLevel, setAutonomyLevel] = useState<AutonomyLevel>('observe');

  const loadServices = async () => {
    try {
      const data = await apiClient.getServices();
      setServices(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadServices();
  }, []);

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 0', color: '#94a3b8' }}>
        <RefreshCw size={24} className="spin" style={{ marginBottom: '1rem' }} />
        <p>Loading registered services...</p>
      </div>
    );
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !healthUrl) {
      alert('Service name and Health URL are required');
      return;
    }

    const payload: ServiceCreate = {
      name,
      healthUrl,
      cloudRunService: cloudRunService || undefined,
      githubRepo: githubRepo || undefined,
      criticality,
      autonomyLevel,
      paused: false,
    };

    try {
      await apiClient.createService(payload);
      setShowAddModal(false);
      setName('');
      setHealthUrl('');
      setCloudRunService('');
      setGithubRepo('');
      loadServices();
    } catch (err: any) {
      alert(`Registration failed: ${err.message}`);
    }
  };

  const handleTogglePause = async (service: Service) => {
    try {
      await apiClient.updateService(service.id, { paused: !service.paused });
      loadServices();
    } catch (err: any) {
      alert(`Update failed: ${err.message}`);
    }
  };

  const handleDelete = async (serviceId: string) => {
    if (!confirm('Are you sure you want to unregister this service?')) return;
    try {
      await apiClient.deleteService(serviceId);
      loadServices();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
            Registered Services
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            Configure autonomy levels and monitoring endpoints for Cloud Run services.
          </p>
        </div>

        <button onClick={() => setShowAddModal(true)} className="btn btn-primary">
          <Plus size={16} />
          <span>Register Service</span>
        </button>
      </div>

      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#f87171',
          padding: '0.75rem',
          borderRadius: '0.375rem',
          marginBottom: '1rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Services List Table */}
      <div className="card">
        <div style={{ overflowX: 'auto' }}>
          <table className="incident-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Service Name</th>
                <th>Health URL</th>
                <th>Cloud Run / Repo</th>
                <th>Criticality</th>
                <th>Autonomy</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {services.map((svc) => (
                <tr key={svc.id}>
                  <td>
                    <StatusBadge status={svc.status} />
                  </td>
                  <td style={{ fontWeight: 600 }}>
                    {svc.name}
                    {svc.paused && (
                      <span style={{ marginLeft: '0.5rem', fontSize: '0.7rem', color: '#f59e0b' }}>
                        (Paused)
                      </span>
                    )}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: '#94a3b8' }}>
                    {svc.healthUrl}
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
                    <div>{svc.cloudRunService || '—'}</div>
                    <div style={{ color: '#64748b' }}>{svc.githubRepo || '—'}</div>
                  </td>
                  <td>
                    <span className="badge badge-unknown">{svc.criticality}</span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.8rem', fontWeight: 500, color: '#38bdf8' }}>
                      {svc.autonomyLevel.replace('_', ' ')}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        onClick={() => handleTogglePause(svc)}
                        className="btn btn-outline"
                        style={{ padding: '0.3rem 0.5rem' }}
                        title={svc.paused ? 'Resume monitoring' : 'Pause monitoring'}
                      >
                        {svc.paused ? <Play size={13} color="#10b981" /> : <Pause size={13} color="#f59e0b" />}
                      </button>
                      <button
                        onClick={() => handleDelete(svc.id)}
                        className="btn btn-outline"
                        style={{ padding: '0.3rem 0.5rem' }}
                        title="Delete service"
                      >
                        <Trash2 size={13} color="#ef4444" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Service Modal */}
      {showAddModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 50,
          padding: '1rem',
        }}>
          <div style={{
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '0.75rem',
            maxWidth: '500px',
            width: '100%',
            padding: '1.75rem',
          }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1.25rem' }}>
              Register Service
            </h2>

            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="form-label">Service Name *</label>
                <input
                  className="form-input"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Order Processing Service"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Health Check URL *</label>
                <input
                  className="form-input"
                  value={healthUrl}
                  onChange={(e) => setHealthUrl(e.target.value)}
                  placeholder="https://service.example.com/health"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Cloud Run Service Name</label>
                <input
                  className="form-input"
                  value={cloudRunService}
                  onChange={(e) => setCloudRunService(e.target.value)}
                  placeholder="e.g. order-processing"
                />
              </div>

              <div className="form-group">
                <label className="form-label">GitHub Repository</label>
                <input
                  className="form-input"
                  value={githubRepo}
                  onChange={(e) => setGithubRepo(e.target.value)}
                  placeholder="e.g. my-org/order-processing"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Criticality</label>
                  <select
                    className="form-select"
                    value={criticality}
                    onChange={(e) => setCriticality(e.target.value as Criticality)}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Autonomy Level</label>
                  <select
                    className="form-select"
                    value={autonomyLevel}
                    onChange={(e) => setAutonomyLevel(e.target.value as AutonomyLevel)}
                  >
                    <option value="observe">Observe (Read only)</option>
                    <option value="suggest">Suggest (Propose fix)</option>
                    <option value="act_with_approval">Act With Approval</option>
                    <option value="auto_act">Auto Act (Low risk)</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn btn-outline"
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Service
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
