import React, { useEffect, useState } from 'react';
import { Plus, Trash2, Pause, Play } from 'lucide-react';
import { apiClient } from '../api/client';
import { AutonomyLevel, Criticality, Service, ServiceCreate } from '../api/types';
import { Panel } from '../components/ui/Panel';
import { Button } from '../components/ui/Button';
import { Chip, ChipVariant } from '../components/ui/Chip';
import { StatusDot } from '../components/ui/StatusDot';
import { Table, TableHead, TableRow, TableHeaderCell, TableCell } from '../components/ui/Table';
import { Drawer } from '../components/ui/Drawer';
import { Tabs } from '../components/ui/Tabs';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { useToast } from '../components/ui/Toast';

export const ServicesPage: React.FC = () => {
  const [services, setServices] = useState<Service[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);

  // Form State
  const [name, setName] = useState('');
  const [healthUrl, setHealthUrl] = useState('');
  const [cloudRunService, setCloudRunService] = useState('');
  const [githubRepo, setGithubRepo] = useState('');
  const [criticality, setCriticality] = useState<Criticality>('medium');
  const [autonomyLevel, setAutonomyLevel] = useState<AutonomyLevel>('observe');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const { addToast } = useToast();

  const loadServices = async () => {
    try {
      const data = await apiClient.getServices();
      setServices(data);
    } catch (err: any) {
      addToast('error', 'Failed to load services', err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadServices();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !healthUrl.trim()) {
      addToast('error', 'Missing Fields', 'Service name and Health URL are required.');
      return;
    }

    setIsSubmitting(true);
    const payload: ServiceCreate = {
      name: name.trim(),
      healthUrl: healthUrl.trim(),
      cloudRunService: cloudRunService.trim() || undefined,
      githubRepo: githubRepo.trim() || undefined,
      criticality,
      autonomyLevel,
      paused: false,
    };

    try {
      await apiClient.createService(payload);
      addToast('success', 'Service Registered', `${name} is now monitored by Nightwatch.`);
      setIsDrawerOpen(false);
      setName('');
      setHealthUrl('');
      setCloudRunService('');
      setGithubRepo('');
      loadServices();
    } catch (err: any) {
      addToast('error', 'Registration Failed', err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateAutonomy = async (service: Service, newLevel: AutonomyLevel) => {
    try {
      await apiClient.updateService(service.id, { autonomyLevel: newLevel });
      addToast('info', 'Autonomy Updated', `${service.name} autonomy set to ${newLevel}.`);
      loadServices();
    } catch (err: any) {
      addToast('error', 'Update Failed', err.message);
    }
  };

  const handleTogglePause = async (service: Service) => {
    try {
      await apiClient.updateService(service.id, { paused: !service.paused });
      addToast(
        service.paused ? 'success' : 'warning',
        service.paused ? 'Monitoring Resumed' : 'Monitoring Paused',
        `${service.name} sweeps are now ${service.paused ? 'active' : 'paused'}.`
      );
      loadServices();
    } catch (err: any) {
      addToast('error', 'Update Failed', err.message);
    }
  };

  const handleDelete = async (service: Service) => {
    if (!confirm(`Are you sure you want to unregister ${service.name}?`)) return;
    try {
      await apiClient.deleteService(service.id);
      addToast('info', 'Service Removed', `${service.name} was deleted.`);
      loadServices();
    } catch (err: any) {
      addToast('error', 'Deletion Failed', err.message);
    }
  };

  const criticalityVariantMap: Record<Criticality, ChipVariant> = {
    high: 'critical',
    medium: 'degraded',
    low: 'neutral',
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Skeleton width="160px" height="28px" />
          <Skeleton width="120px" height="36px" />
        </div>
        <Skeleton height="320px" />
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2
            style={{
              fontSize: 'var(--font-size-20)',
              fontWeight: 600,
              color: 'var(--text-primary)',
              letterSpacing: '-0.02em',
            }}
          >
            Registered Services
          </h2>
          <p style={{ fontSize: 'var(--font-size-12)', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Configure monitored HTTP targets, diagnostic probes, and autonomy approval gates.
          </p>
        </div>
        <Button variant="primary" size="md" onClick={() => setIsDrawerOpen(true)} icon={<Plus size={14} />}>
          Add service
        </Button>
      </div>

      {/* Services Table Panel */}
      <Panel padding="none">
        {services.length === 0 ? (
          <EmptyState
            title="No services configured"
            description="Register a service endpoint to begin health checks, log scanning, and autonomous triage."
            action={
              <Button variant="secondary" size="sm" onClick={() => setIsDrawerOpen(true)} icon={<Plus size={13} />}>
                Register first service
              </Button>
            }
          />
        ) : (
          <Table>
            <TableHead>
              <TableRow hoverable={false}>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Service Name</TableHeaderCell>
                <TableHeaderCell>Health Probe URL</TableHeaderCell>
                <TableHeaderCell>Criticality</TableHeaderCell>
                <TableHeaderCell>Autonomy Control</TableHeaderCell>
                <TableHeaderCell style={{ textAlign: 'right' }}>Actions</TableHeaderCell>
              </TableRow>
            </TableHead>
            <tbody>
              {services.map((svc) => (
                <TableRow key={svc.id}>
                  {/* Status dot */}
                  <TableCell>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <StatusDot
                        status={svc.paused ? 'neutral' : svc.status === 'down' ? 'critical' : svc.status === 'degraded' ? 'degraded' : 'healthy'}
                        pulse={!svc.paused && svc.status === 'down'}
                      />
                      <span style={{ fontSize: 'var(--font-size-12)', textTransform: 'capitalize' }}>
                        {svc.paused ? 'Paused' : svc.status}
                      </span>
                    </div>
                  </TableCell>

                  {/* Name and ID */}
                  <TableCell>
                    <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{svc.name}</div>
                    <div className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {svc.id}
                    </div>
                  </TableCell>

                  {/* Health URL in Mono */}
                  <TableCell>
                    <code
                      className="font-mono tabular-nums"
                      style={{
                        fontSize: '12px',
                        color: 'var(--text-secondary)',
                        backgroundColor: 'var(--bg-ink)',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      {svc.healthUrl}
                    </code>
                  </TableCell>

                  {/* Criticality Chip */}
                  <TableCell>
                    <Chip variant={criticalityVariantMap[svc.criticality]} size="sm">
                      {svc.criticality}
                    </Chip>
                  </TableCell>

                  {/* Autonomy Level Segmented Control */}
                  <TableCell>
                    <Tabs
                      variant="segmented"
                      size="sm"
                      activeId={svc.autonomyLevel}
                      onChange={(id) => handleUpdateAutonomy(svc, id as AutonomyLevel)}
                      items={[
                        { id: 'observe', label: 'Observe' },
                        { id: 'suggest', label: 'Suggest' },
                        { id: 'act_with_approval', label: 'Act w/ approval' },
                      ]}
                    />
                  </TableCell>

                  {/* Row Actions Menu */}
                  <TableCell style={{ textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleTogglePause(svc)}
                        icon={svc.paused ? <Play size={13} color="var(--status-healthy)" /> : <Pause size={13} />}
                        title={svc.paused ? 'Resume sweeps' : 'Pause sweeps'}
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(svc)}
                        icon={<Trash2 size={13} color="var(--status-critical)" />}
                        title="Delete service"
                      />
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </tbody>
          </Table>
        )}
      </Panel>

      {/* Side Drawer: Add Service */}
      <Drawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        title="Register New Service"
        subtitle="Configure target HTTP endpoint and autonomy rules for Nightwatch."
        footer={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px', width: '100%' }}>
            <Button variant="secondary" size="sm" onClick={() => setIsDrawerOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              loading={isSubmitting}
              onClick={handleCreate}
              icon={<Plus size={13} />}
            >
              Save Service
            </Button>
          </div>
        }
      >
        <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label
              style={{
                display: 'block',
                fontSize: 'var(--font-size-12)',
                fontWeight: 500,
                color: 'var(--text-secondary)',
                marginBottom: '6px',
              }}
            >
              Service Name *
            </label>
            <input
              type="text"
              placeholder="e.g., Demo Shop API"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '8px 10px',
                fontSize: 'var(--font-size-13)',
              }}
            />
          </div>

          <div>
            <label
              style={{
                display: 'block',
                fontSize: 'var(--font-size-12)',
                fontWeight: 500,
                color: 'var(--text-secondary)',
                marginBottom: '6px',
              }}
            >
              Health Check URL *
            </label>
            <input
              type="url"
              placeholder="http://127.0.0.1:8001/health"
              value={healthUrl}
              onChange={(e) => setHealthUrl(e.target.value)}
              required
              className="font-mono"
              style={{
                width: '100%',
                padding: '8px 10px',
                fontSize: 'var(--font-size-13)',
              }}
            />
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Nightwatch probes this endpoint every 15 seconds.
            </p>
          </div>

          <div>
            <label
              style={{
                display: 'block',
                fontSize: 'var(--font-size-12)',
                fontWeight: 500,
                color: 'var(--text-secondary)',
                marginBottom: '6px',
              }}
            >
              Cloud Run Service Identifier (optional)
            </label>
            <input
              type="text"
              placeholder="e.g., demo-shop"
              value={cloudRunService}
              onChange={(e) => setCloudRunService(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 10px',
                fontSize: 'var(--font-size-13)',
              }}
            />
          </div>

          <div>
            <label
              style={{
                display: 'block',
                fontSize: 'var(--font-size-12)',
                fontWeight: 500,
                color: 'var(--text-secondary)',
                marginBottom: '6px',
              }}
            >
              GitHub Repository (optional)
            </label>
            <input
              type="text"
              placeholder="owner/demo-shop"
              value={githubRepo}
              onChange={(e) => setGithubRepo(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 10px',
                fontSize: 'var(--font-size-13)',
              }}
            />
          </div>

          <div>
            <label
              style={{
                display: 'block',
                fontSize: 'var(--font-size-12)',
                fontWeight: 500,
                color: 'var(--text-secondary)',
                marginBottom: '6px',
              }}
            >
              Criticality
            </label>
            <select
              value={criticality}
              onChange={(e) => setCriticality(e.target.value as Criticality)}
              style={{
                width: '100%',
                padding: '8px 10px',
                fontSize: 'var(--font-size-13)',
              }}
            >
              <option value="high">High (P1 on outage)</option>
              <option value="medium">Medium (P2 on outage)</option>
              <option value="low">Low (P3 on outage)</option>
            </select>
          </div>

          <div>
            <label
              style={{
                display: 'block',
                fontSize: 'var(--font-size-12)',
                fontWeight: 500,
                color: 'var(--text-secondary)',
                marginBottom: '6px',
              }}
            >
              Autonomy Level
            </label>
            <select
              value={autonomyLevel}
              onChange={(e) => setAutonomyLevel(e.target.value as AutonomyLevel)}
              style={{
                width: '100%',
                padding: '8px 10px',
                fontSize: 'var(--font-size-13)',
              }}
            >
              <option value="observe">Observe (Alert and diagnose only)</option>
              <option value="suggest">Suggest (Propose remediation cards)</option>
              <option value="act_with_approval">Act with Approval (Human approval gate)</option>
            </select>
          </div>
        </form>
      </Drawer>
    </div>
  );
};
