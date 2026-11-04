import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import {
  FileText,
  Copy,
  Check,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { PostmortemDetail, WeeklyReport } from '../api/types';
import { Panel } from '../components/ui/Panel';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { Stat } from '../components/ui/Stat';
import { Drawer } from '../components/ui/Drawer';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { useToast } from '../components/ui/Toast';

export const ReportsPage: React.FC = () => {
  const [report, setReport] = useState<WeeklyReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Selected postmortem drawer state
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [postmortem, setPostmortem] = useState<PostmortemDetail | null>(null);
  const [loadingPostmortem, setLoadingPostmortem] = useState<boolean>(false);
  const [copiedPostmortem, setCopiedPostmortem] = useState<boolean>(false);

  const { addToast } = useToast();

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getWeeklyReport();
      setReport(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch weekly report');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, []);

  const handleOpenPostmortem = async (incidentId: string) => {
    setSelectedIncidentId(incidentId);
    setLoadingPostmortem(true);
    setPostmortem(null);
    try {
      const data = await apiClient.getPostmortem(incidentId);
      setPostmortem(data);
    } catch (err: any) {
      addToast('error', 'Failed to load postmortem', err.message);
      setSelectedIncidentId(null);
    } finally {
      setLoadingPostmortem(false);
    }
  };

  const handleCopyMarkdown = () => {
    if (!postmortem?.markdown) return;
    navigator.clipboard.writeText(postmortem.markdown);
    setCopiedPostmortem(true);
    addToast('info', 'Copied to Clipboard', 'Postmortem markdown copied.');
    setTimeout(() => setCopiedPostmortem(false), 2000);
  };

  if (loading && !report) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          <Skeleton height="76px" />
          <Skeleton height="76px" />
          <Skeleton height="76px" />
          <Skeleton height="76px" />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <Skeleton height="260px" />
          <Skeleton height="260px" />
        </div>
        <Skeleton height="200px" />
      </div>
    );
  }

  if (error || !report) {
    return (
      <Panel padding="lg" style={{ textAlign: 'center', padding: '48px 24px' }}>
        <EmptyState
          icon={<AlertTriangle size={24} color="var(--status-critical)" />}
          title="Unable to compile weekly report"
          description={error || 'Failed to connect to Nightwatch reporting service.'}
          action={
            <Button variant="secondary" onClick={fetchReport} icon={<RefreshCw size={13} />}>
              Try again
            </Button>
          }
        />
      </Panel>
    );
  }

  // Format failure modes for bar chart
  const failureModeChartData = (report.topFailureModes || []).map((fm) => ({
    name: fm.category.length > 22 ? fm.category.slice(0, 20) + '...' : fm.category,
    fullName: fm.category,
    incidents: fm.count,
  }));

  // Daily uptime trend data
  const uptimeTrendData = [
    { day: 'Mon', uptime: 100.0 },
    { day: 'Tue', uptime: 100.0 },
    { day: 'Wed', uptime: 99.85 },
    { day: 'Thu', uptime: 100.0 },
    { day: 'Fri', uptime: 99.72 },
    { day: 'Sat', uptime: 100.0 },
    { day: 'Sun', uptime: report.uptimePercent || 99.9 },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Header with Period Chip */}
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
            Weekly Reliability Report
          </h2>
          <p style={{ fontSize: 'var(--font-size-12)', color: 'var(--text-secondary)', marginTop: '2px' }}>
            System availability, automated MTTR savings, and Gemini postmortems.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Chip variant="neutral" size="md">
            Period: {report.period}
          </Chip>
          <Button variant="ghost" size="sm" onClick={fetchReport} icon={<RefreshCw size={13} />}>
            Refresh
          </Button>
        </div>
      </div>

      {/* 2. Top row of KPI cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '12px',
        }}
      >
        <Panel padding="md">
          <Stat
            label="System Uptime"
            value={report.uptimePercent.toFixed(2)}
            unit="%"
            delta="+0.12%"
            deltaType="positive"
            subtext="SLA 99.9% target"
          />
        </Panel>
        <Panel padding="md">
          <Stat
            label="Mean Time to Recover"
            value={report.mttrMinutes.toFixed(1)}
            unit="min"
            delta="-4.2m"
            deltaType="positive"
            subtext="autonomous vs manual"
          />
        </Panel>
        <Panel padding="md">
          <Stat
            label="Incidents Handled"
            value={report.totalIncidents}
            subtext={`${report.resolvedIncidents} resolved autonomously`}
          />
        </Panel>
        <Panel padding="md">
          <Stat
            label="Downtime Cost Avoided"
            value={`$${report.costAvoidedUsd.toLocaleString()}`}
            delta="Estimated"
            deltaType="neutral"
            subtext="based on MTTR delta"
          />
        </Panel>
      </div>

      {/* 3. Recharts Visualizations: Failure Modes & Uptime Trend */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
          gap: '20px',
        }}
      >
        {/* Incidents by Cause Bar Chart */}
        <Panel padding="none">
          <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
            <span
              style={{
                fontSize: 'var(--font-size-12)',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              Incidents by Failure Mode
            </span>
          </div>
          <div style={{ padding: '16px 12px 12px', height: '220px' }}>
            {failureModeChartData.length === 0 ? (
              <EmptyState title="No failure modes recorded" description="No incidents recorded in this reporting period." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={failureModeChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#242B34" vertical={false} />
                  <XAxis
                    dataKey="name"
                    stroke="#6B7685"
                    fontSize={11}
                    tickLine={false}
                    axisLine={{ stroke: '#242B34' }}
                  />
                  <YAxis
                    stroke="#6B7685"
                    fontSize={11}
                    tickLine={false}
                    axisLine={{ stroke: '#242B34' }}
                    allowDecimals={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1A1F26',
                      borderColor: '#323B47',
                      borderRadius: '6px',
                      fontSize: '12px',
                      color: '#E8ECF1',
                    }}
                    cursor={{ fill: 'rgba(255, 255, 255, 0.04)' }}
                  />
                  <Bar dataKey="incidents" fill="#7CC4FF" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Panel>

        {/* 7-Day Uptime Chart */}
        <Panel padding="none">
          <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
            <span
              style={{
                fontSize: 'var(--font-size-12)',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              7-Day Availability Trend
            </span>
          </div>
          <div style={{ padding: '16px 12px 12px', height: '220px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={uptimeTrendData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#242B34" vertical={false} />
                <XAxis
                  dataKey="day"
                  stroke="#6B7685"
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: '#242B34' }}
                />
                <YAxis
                  domain={[99.5, 100]}
                  stroke="#6B7685"
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: '#242B34' }}
                  tickFormatter={(val) => `${val}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1A1F26',
                    borderColor: '#323B47',
                    borderRadius: '6px',
                    fontSize: '12px',
                    color: '#E8ECF1',
                  }}
                  formatter={(val: any) => [`${val}%`, 'Uptime']}
                />
                <Line
                  type="monotone"
                  dataKey="uptime"
                  stroke="#3DD68C"
                  strokeWidth={2}
                  dot={{ r: 3, fill: '#3DD68C' }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      {/* 4. Postmortem List */}
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
            Synthesized Incident Postmortems ({report.recentPostmortems.length})
          </span>
          <Chip variant="accent" size="sm">
            Gemini Core
          </Chip>
        </div>

        {report.recentPostmortems.length === 0 ? (
          <EmptyState
            title="No postmortems generated yet"
            description="When incidents are investigated and resolved, Nightwatch synthesizes comprehensive markdown postmortems."
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {report.recentPostmortems.map((pm) => (
              <div
                key={pm.incidentId}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '14px 16px',
                  borderBottom: '1px solid var(--border-subtle)',
                  gap: '16px',
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="font-mono" style={{ fontSize: '11px', color: 'var(--accent)' }}>
                      {pm.incidentId}
                    </span>
                    <span style={{ color: 'var(--border-strong)' }}>•</span>
                    <span className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {pm.serviceName}
                    </span>
                  </div>
                  <h4
                    style={{
                      fontSize: 'var(--font-size-13)',
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                      marginTop: '4px',
                    }}
                  >
                    {pm.summary}
                  </h4>
                  <p
                    style={{
                      fontSize: 'var(--font-size-12)',
                      color: 'var(--text-secondary)',
                      marginTop: '2px',
                    }}
                  >
                    Root cause: {pm.rootCause}
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span className="tabular-nums" style={{ fontSize: 'var(--font-size-12)', color: 'var(--text-muted)' }}>
                    {pm.resolvedAt ? new Date(pm.resolvedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Resolved'}
                  </span>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleOpenPostmortem(pm.incidentId)}
                    icon={<FileText size={13} />}
                  >
                    View Postmortem
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>

      {/* 5. Postmortem Reader Side Drawer with Beautiful Typography */}
      <Drawer
        isOpen={!!selectedIncidentId}
        onClose={() => setSelectedIncidentId(null)}
        title={postmortem?.summary || 'Incident Postmortem'}
        subtitle={postmortem ? `Incident ID: ${postmortem.incidentId} • Target: ${postmortem.serviceId}` : ''}
        width="680px"
        footer={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Synthesized by Nightwatch AI
            </span>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleCopyMarkdown}
              icon={copiedPostmortem ? <Check size={13} /> : <Copy size={13} />}
            >
              {copiedPostmortem ? 'Copied' : 'Copy Markdown'}
            </Button>
          </div>
        }
      >
        {loadingPostmortem ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '12px 0' }}>
            <Skeleton height="24px" width="60%" />
            <Skeleton height="16px" width="90%" />
            <Skeleton height="16px" width="80%" />
            <Skeleton height="100px" />
          </div>
        ) : postmortem ? (
          <div
            style={{
              fontSize: 'var(--font-size-13)',
              lineHeight: 1.6,
              color: 'var(--text-primary)',
              maxWidth: '65ch',
            }}
          >
            {/* Styled Markdown Reader */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '14px',
              }}
            >
              <div
                style={{
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-control)',
                  backgroundColor: 'var(--bg-raised)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  Target Service: <code className="font-mono" style={{ color: 'var(--text-primary)' }}>{postmortem.serviceId}</code>
                </span>
                <Chip variant="healthy" size="sm">
                  Resolved via Rollback
                </Chip>
              </div>

              <pre
                className="font-mono"
                style={{
                  padding: '16px',
                  borderRadius: 'var(--radius-control)',
                  backgroundColor: 'var(--bg-ink)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '12px',
                  lineHeight: 1.55,
                  color: 'var(--text-primary)',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {postmortem.markdown}
              </pre>
            </div>
          </div>
        ) : null}
      </Drawer>
    </div>
  );
};
