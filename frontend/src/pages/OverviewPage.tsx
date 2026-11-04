import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { apiClient } from '../api/client';
import { Incident, Service } from '../api/types';
import { Panel } from '../components/ui/Panel';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { StatusDot } from '../components/ui/StatusDot';
import { Stat } from '../components/ui/Stat';
import { Table, TableHead, TableRow, TableHeaderCell, TableCell } from '../components/ui/Table';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';

// Tiny latency sparkline generator
const Sparkline: React.FC<{ data: number[]; color?: string }> = ({
  data,
  color = 'var(--status-healthy)',
}) => {
  const chartData = data.map((val, idx) => ({ idx, val }));
  return (
    <div style={{ width: '64px', height: '18px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
          <Line
            type="monotone"
            dataKey="val"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export const OverviewPage: React.FC = () => {
  const [services, setServices] = useState<Service[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

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
    }
  };

  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, 10000);
    return () => clearInterval(timer);
  }, []);

  const activeIncidents = incidents.filter((i) => i.status !== 'resolved');
  const topActive = activeIncidents[0];
  const allHealthy = activeIncidents.length === 0;

  // Mock agent activity feed derived from state
  const agentActivity = [
    {
      id: 'act-1',
      title: allHealthy ? 'Sweep check passed' : 'Dispatched diagnostic sweep',
      target: 'svc-demo-shop',
      time: '12s ago',
      type: allHealthy ? 'healthy' : 'critical',
    },
    {
      id: 'act-2',
      title: 'Scanned /logs ring buffer (1,000 entries)',
      target: 'svc-demo-shop',
      time: '28s ago',
      type: 'neutral',
    },
    {
      id: 'act-3',
      title: 'Evaluated DT-3 confirmation criteria',
      target: 'svc-demo-shop',
      time: '44s ago',
      type: 'neutral',
    },
    {
      id: 'act-4',
      title: 'Synced runbook vector embeddings',
      target: 'nightwatch-core',
      time: '2m ago',
      type: 'healthy',
    },
  ];

  if (isLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <Skeleton height="48px" />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          <Skeleton height="76px" />
          <Skeleton height="76px" />
          <Skeleton height="76px" />
          <Skeleton height="76px" />
        </div>
        <Skeleton height="240px" />
      </div>
    );
  }

  const healthyCount = services.filter((s) => s.status === 'healthy').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Full-width Status Banner (One line) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 16px',
          borderRadius: 'var(--radius-panel)',
          backgroundColor: allHealthy ? 'var(--status-healthy-tint)' : 'var(--status-critical-tint)',
          border: `1px solid ${allHealthy ? 'rgba(61, 214, 140, 0.25)' : 'rgba(255, 107, 107, 0.25)'}`,
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <StatusDot
            status={allHealthy ? 'healthy' : 'critical'}
            pulse={!allHealthy}
            size={8}
          />
          <span
            style={{
              fontSize: 'var(--font-size-13)',
              fontWeight: 600,
              color: allHealthy ? 'var(--status-healthy)' : 'var(--status-critical)',
            }}
          >
            {allHealthy
              ? 'All systems operational'
              : `${activeIncidents.length} active incident${activeIncidents.length > 1 ? 's' : ''}: ${topActive?.summary || 'Service degraded'}`}
          </span>
          {!allHealthy && topActive && (
            <Chip variant="critical" size="sm">
              {topActive.severity}
            </Chip>
          )}
        </div>

        {!allHealthy && topActive && (
          <Link to={`/incidents/${topActive.id}`}>
            <Button variant="primary" size="sm" icon={<ArrowRight size={13} />}>
              Open war-room
            </Button>
          </Link>
        )}
      </div>

      {/* 2. KPI Strip: 4 compact metrics */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '12px',
        }}
      >
        <Panel padding="md">
          <Stat
            label="Services healthy"
            value={`${healthyCount} / ${services.length}`}
            subtext="100% target coverage"
          />
        </Panel>
        <Panel padding="md">
          <Stat
            label="Active incidents"
            value={activeIncidents.length}
            subtext={activeIncidents.length === 0 ? 'Quiet on-call' : 'Requires review'}
            deltaType={activeIncidents.length === 0 ? 'positive' : 'negative'}
          />
        </Panel>
        <Panel padding="md">
          <Stat
            label="MTTR (30d)"
            value="1.8"
            unit="min"
            delta="-32%"
            deltaType="positive"
            subtext="vs last period"
          />
        </Panel>
        <Panel padding="md">
          <Stat
            label="Uptime (7d)"
            value="99.92"
            unit="%"
            subtext="Within SLA target"
          />
        </Panel>
      </div>

      {/* 3. Monitored Services Clean List / Table */}
      <Panel padding="none">
        <div
          style={{
            padding: '14px 16px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span
            style={{
              fontSize: 'var(--font-size-12)',
              fontWeight: 600,
              color: 'var(--text-secondary)',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            Monitored Services ({services.length})
          </span>
          <Link to="/services">
            <Button variant="ghost" size="sm">
              Manage services
            </Button>
          </Link>
        </div>

        {services.length === 0 ? (
          <EmptyState
            title="No services registered"
            description="Add services to begin automated health checks and log telemetry."
          />
        ) : (
          <Table>
            <TableHead>
              <TableRow hoverable={false}>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Service</TableHeaderCell>
                <TableHeaderCell>Latency</TableHeaderCell>
                <TableHeaderCell>Error Rate</TableHeaderCell>
                <TableHeaderCell>Autonomy</TableHeaderCell>
                <TableHeaderCell>Last Check</TableHeaderCell>
              </TableRow>
            </TableHead>
            <tbody>
              {services.map((svc) => {
                const isHealthy = svc.status === 'healthy';
                const sparklineData = isHealthy ? [18, 22, 19, 21, 24, 20] : [24, 80, 240, 520, 1200, 2500];
                const sparkColor = isHealthy ? 'var(--status-healthy)' : 'var(--status-critical)';

                return (
                  <TableRow key={svc.id}>
                    <TableCell>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <StatusDot
                          status={svc.status === 'down' ? 'critical' : svc.status === 'degraded' ? 'degraded' : 'healthy'}
                          pulse={svc.status === 'down'}
                        />
                        <span style={{ fontSize: 'var(--font-size-12)', textTransform: 'capitalize' }}>
                          {svc.status}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{svc.name}</div>
                      <div className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        {svc.id}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Sparkline data={sparklineData} color={sparkColor} />
                        <span className="tabular-nums font-mono" style={{ fontSize: 'var(--font-size-12)', color: 'var(--text-secondary)' }}>
                          {isHealthy ? '21ms' : '2.5s'}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="tabular-nums font-mono" style={{ fontSize: 'var(--font-size-12)', color: isHealthy ? 'var(--text-muted)' : 'var(--status-critical)' }}>
                        {isHealthy ? '0.00%' : '71.4%'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Chip variant="neutral" size="sm">
                        {svc.autonomyLevel.replace('_', ' ')}
                      </Chip>
                    </TableCell>
                    <TableCell>
                      <span className="tabular-nums" style={{ fontSize: 'var(--font-size-12)', color: 'var(--text-muted)' }}>
                        Just now
                      </span>
                    </TableCell>
                  </TableRow>
                );
              })}
            </tbody>
          </Table>
        )}
      </Panel>

      {/* 4. Two Columns Below: Incidents & Agent Activity Feed */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1.4fr) minmax(0, 1fr)',
          gap: '20px',
        }}
      >
        {/* Left: Active & Recent Incidents */}
        <Panel padding="none">
          <div
            style={{
              padding: '14px 16px',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span
              style={{
                fontSize: 'var(--font-size-12)',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              Active and Recent Incidents
            </span>
            <span className="tabular-nums" style={{ fontSize: 'var(--font-size-12)', color: 'var(--text-muted)' }}>
              {incidents.length} total
            </span>
          </div>

          {incidents.length === 0 ? (
            <EmptyState
              title="No incidents in the last 7 days"
              description="Nightwatch is quietly monitoring all services."
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {incidents.slice(0, 6).map((inc) => {
                const isResolved = inc.status === 'resolved';
                return (
                  <Link
                    key={inc.id}
                    to={`/incidents/${inc.id}`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 16px',
                      borderBottom: '1px solid var(--border-subtle)',
                      transition: 'background-color var(--motion-fast)',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--bg-raised)')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Chip
                        variant={inc.severity === 'P1' ? 'critical' : inc.severity === 'P2' ? 'degraded' : 'neutral'}
                        size="sm"
                      >
                        {inc.severity}
                      </Chip>
                      <div>
                        <div style={{ fontSize: 'var(--font-size-13)', fontWeight: 500, color: 'var(--text-primary)' }}>
                          {inc.summary}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                          Service: <span className="font-mono">{inc.serviceId}</span>
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <Chip variant={isResolved ? 'healthy' : 'critical'} size="sm">
                        {inc.status.replace('_', ' ')}
                      </Chip>
                      <span className="tabular-nums" style={{ fontSize: 'var(--font-size-12)', color: 'var(--text-muted)' }}>
                        {new Date(inc.openedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </Panel>

        {/* Right: Agent Activity Feed */}
        <Panel padding="none">
          <div
            style={{
              padding: '14px 16px',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span
              style={{
                fontSize: 'var(--font-size-12)',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              Agent Activity Feed
            </span>
            <Chip variant="accent" size="sm">
              Live
            </Chip>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {agentActivity.map((act) => (
              <div
                key={act.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '10px',
                  padding: '12px 16px',
                  borderBottom: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ marginTop: '4px' }}>
                  <StatusDot
                    status={act.type === 'critical' ? 'critical' : act.type === 'healthy' ? 'healthy' : 'neutral'}
                    size={6}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 'var(--font-size-12)', fontWeight: 500, color: 'var(--text-primary)' }}>
                    {act.title}
                  </div>
                  <div className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                    {act.target}
                  </div>
                </div>
                <span className="tabular-nums" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  {act.time}
                </span>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
};
