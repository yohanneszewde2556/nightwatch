import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  Cpu,
  MessageSquare,
  Radio,
  Terminal,
  ThumbsDown,
  ThumbsUp,
  Copy,
  Check,
  Send,
  ChevronDown,
  ChevronRight,
  History,
  Activity,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Incident, IncidentEvent } from '../api/types';
import { Panel } from '../components/ui/Panel';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { StatusDot } from '../components/ui/StatusDot';
import { Dialog } from '../components/ui/Dialog';
import { Skeleton } from '../components/ui/Skeleton';
import { useToast } from '../components/ui/Toast';

export const WarRoomPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [events, setEvents] = useState<IncidentEvent[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  // Rejection & Approval state
  const [isApproveDialogOpen, setIsApproveDialogOpen] = useState<boolean>(false);
  const [isRejectDialogOpen, setIsRejectDialogOpen] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>('');
  const [copiedLog, setCopiedLog] = useState<boolean>(false);

  // Chat state
  const [chatMessages, setChatMessages] = useState<Array<{ sender: 'user' | 'agent'; text: string; time: string }>>([
    {
      sender: 'agent',
      text: 'I am monitoring this incident. Ask me about root-cause evidence, recent git diffs, or runbook history.',
      time: 'Just now',
    },
  ]);
  const [chatInput, setChatInput] = useState<string>('');
  const [isChatSending, setIsChatSending] = useState<boolean>(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Collapsed tool calls state
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});

  const { addToast } = useToast();

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
    const timer = setInterval(loadIncidentData, 8000);
    return () => clearInterval(timer);
  }, [id]);

  const toggleToolExpanded = (evtId: string) => {
    setExpandedTools((prev) => ({
      ...prev,
      [evtId]: !prev[evtId],
    }));
  };

  const handleConfirmApprove = async () => {
    if (!id) return;
    setActionLoading(true);
    setActionMessage(null);
    try {
      await apiClient.approveAction(id, 'Approved by on-call engineer in War-Room');
      setActionMessage('Rollback action approved and dispatched to target.');
      setIsApproveDialogOpen(false);
      addToast('success', 'Action Approved', 'Rollback to v1 has been initiated.');
      await loadIncidentData();
    } catch (err: any) {
      setActionMessage(`Notice: ${err.message}`);
      addToast('error', 'Approval Failed', err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirmReject = async () => {
    if (!id || !rejectReason.trim()) return;
    setActionLoading(true);
    setActionMessage(null);
    try {
      await apiClient.rejectAction(id, rejectReason.trim());
      setActionMessage(`Action rejected: ${rejectReason}`);
      setIsRejectDialogOpen(false);
      setRejectReason('');
      addToast('warning', 'Action Rejected', 'Proposed remediation was declined.');
      await loadIncidentData();
    } catch (err: any) {
      setActionMessage(`Notice: ${err.message}`);
      addToast('error', 'Rejection Failed', err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isChatSending) return;

    const userText = chatInput.trim();
    setChatInput('');
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setChatMessages((prev) => [...prev, { sender: 'user', text: userText, time: now }]);
    setIsChatSending(true);

    try {
      const resp = await apiClient.chatWithAgent(userText, incident?.serviceId);
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: resp.reply,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: `Error contacting agent: ${err.message || 'Service unavailable'}`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsChatSending(false);
      setTimeout(() => {
        chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  };

  const copyEvidenceLog = () => {
    const rawText = `2026-11-04 18:24:12 ERROR [app.checkout:78 apply_discount]
TypeError: unsupported operand type(s) for *: 'float' and 'NoneType'
  File "app/checkout.py", line 78, in apply_discount
    discount_amount = total * rate
  File "app/main.py", line 112, in checkout_endpoint
    order = process_checkout(cart, discount_code)
HTTP 500 Internal Server Error (checkout_failed, code=SAVE20)`;

    navigator.clipboard.writeText(rawText);
    setCopiedLog(true);
    addToast('info', 'Copied to Clipboard', 'Traceback copied.');
    setTimeout(() => setCopiedLog(false), 2000);
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Skeleton width="180px" height="24px" />
          <Skeleton width="120px" height="24px" />
        </div>
        <Panel padding="lg">
          <Skeleton width="40%" height="28px" style={{ marginBottom: '12px' }} />
          <Skeleton width="80%" height="16px" />
        </Panel>
        <div style={{ display: 'grid', gridTemplateColumns: '62% 38%', gap: '24px' }}>
          <Skeleton height="400px" />
          <Skeleton height="400px" />
        </div>
      </div>
    );
  }

  if (!incident) {
    return (
      <Panel padding="lg" style={{ textAlign: 'center', padding: '48px 24px' }}>
        <h2 style={{ fontSize: 'var(--font-size-16)', fontWeight: 600, color: 'var(--text-primary)' }}>
          Incident not found
        </h2>
        <p style={{ color: 'var(--text-secondary)', margin: '8px 0 20px', fontSize: 'var(--font-size-13)' }}>
          The incident '{id}' does not exist or has expired.
        </p>
        <Link to="/">
          <Button variant="secondary" icon={<ArrowLeft size={14} />}>
            Back to Overview
          </Button>
        </Link>
      </Panel>
    );
  }

  // Stepper calculations
  const steps = [
    { key: 'detected', label: 'Detected' },
    { key: 'investigating', label: 'Investigating' },
    { key: 'awaiting_approval', label: 'Awaiting approval' },
    { key: 'mitigating', label: 'Mitigating' },
    { key: 'resolved', label: 'Resolved' },
  ];

  const getStepIndex = (status: string) => {
    switch (status) {
      case 'open':
      case 'detected':
        return 0;
      case 'investigating':
        return 1;
      case 'awaiting_approval':
        return 2;
      case 'mitigating':
        return 3;
      case 'resolved':
        return 4;
      default:
        return 1;
    }
  };

  const currentStepIdx = getStepIndex(incident.status);

  // Render timeline item icon
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'signal':
        return <Radio size={14} color="var(--status-critical)" />;
      case 'tool_call':
        return <Terminal size={14} color="var(--accent)" />;
      case 'hypothesis':
        return <Cpu size={14} color="var(--status-degraded)" />;
      case 'action':
        return <Activity size={14} color="var(--status-healthy)" />;
      case 'approval':
        return <CheckCircle2 size={14} color="var(--status-healthy)" />;
      case 'notification':
        return <MessageSquare size={14} color="var(--accent)" />;
      default:
        return <Clock size={14} color="var(--text-muted)" />;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header Card */}
      <Panel padding="lg" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Chip
                variant={incident.severity === 'P1' ? 'critical' : incident.severity === 'P2' ? 'degraded' : 'neutral'}
                size="sm"
              >
                {incident.severity}
              </Chip>
              <span
                style={{
                  fontSize: 'var(--font-size-12)',
                  color: 'var(--text-muted)',
                }}
              >
                Service: <strong style={{ color: 'var(--text-primary)' }}>{incident.serviceId}</strong>
              </span>
              <span style={{ color: 'var(--border-strong)' }}>•</span>
              <span className="tabular-nums" style={{ fontSize: 'var(--font-size-12)', color: 'var(--text-muted)' }}>
                Opened at {new Date(incident.openedAt).toLocaleTimeString()}
              </span>
            </div>
            <h1
              style={{
                fontSize: 'var(--font-size-20)',
                fontWeight: 600,
                color: 'var(--text-primary)',
                letterSpacing: '-0.02em',
                lineHeight: 1.3,
              }}
            >
              {incident.summary}
            </h1>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              className="tabular-nums"
              style={{
                fontSize: 'var(--font-size-12)',
                color: 'var(--text-muted)',
                padding: '4px 8px',
                borderRadius: 'var(--radius-control)',
                backgroundColor: 'var(--bg-raised)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              ID: {incident.id}
            </span>
          </div>
        </div>

        {/* Horizontal Status Stepper */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingTop: '16px',
            borderTop: '1px solid var(--border-subtle)',
            overflowX: 'auto',
            gap: '8px',
          }}
        >
          {steps.map((st, idx) => {
            const isCompleted = idx < currentStepIdx;
            const isCurrent = idx === currentStepIdx;
            return (
              <div
                key={st.key}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  flex: 1,
                  opacity: isCurrent ? 1 : isCompleted ? 0.8 : 0.4,
                }}
              >
                <div
                  style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11px',
                    fontWeight: 600,
                    backgroundColor: isCurrent
                      ? 'var(--accent)'
                      : isCompleted
                      ? 'var(--status-healthy)'
                      : 'var(--bg-raised)',
                    color: isCurrent || isCompleted ? '#0D1014' : 'var(--text-muted)',
                    border: isCurrent || isCompleted ? 'none' : '1px solid var(--border-subtle)',
                  }}
                >
                  {isCompleted ? <Check size={11} strokeWidth={3} /> : idx + 1}
                </div>
                <span
                  style={{
                    fontSize: 'var(--font-size-12)',
                    fontWeight: isCurrent ? 600 : 400,
                    color: isCurrent ? 'var(--text-primary)' : 'var(--text-secondary)',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {st.label}
                </span>
                {idx < steps.length - 1 && (
                  <div
                    style={{
                      flex: 1,
                      height: '1px',
                      backgroundColor: isCompleted ? 'var(--status-healthy)' : 'var(--border-subtle)',
                      marginLeft: '4px',
                      minWidth: '16px',
                    }}
                  />
                )}
              </div>
            );
          })}
        </div>
      </Panel>

      {/* Main Two-Column Layout */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1.6fr) minmax(0, 1fr)',
          gap: '24px',
          alignItems: 'start',
        }}
      >
        {/* Left Column: Reasoning Timeline Rail (about 62%) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 4px' }}>
            <span
              style={{
                fontSize: 'var(--font-size-12)',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              Investigation Reasoning Trace
            </span>
            <span className="tabular-nums" style={{ fontSize: 'var(--font-size-12)', color: 'var(--text-muted)' }}>
              {events.length} event{events.length === 1 ? '' : 's'}
            </span>
          </div>

          <div
            style={{
              position: 'relative',
              paddingLeft: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
            }}
          >
            {/* Vertical Rail Line */}
            <div
              style={{
                position: 'absolute',
                top: '12px',
                bottom: '12px',
                left: '7px',
                width: '1px',
                backgroundColor: 'var(--border-subtle)',
              }}
            />

            {events.map((evt, idx) => {
              const isHypothesis = evt.type === 'hypothesis';
              const isToolCall = evt.type === 'tool_call';
              const evtId = evt.id || `evt-${idx}`;
              const isExpanded = !!expandedTools[evtId];

              // Check if top hypothesis
              const conf = evt.payload?.confidence || (isHypothesis ? 0.86 : 0);

              return (
                <div
                  key={evtId}
                  style={{
                    position: 'relative',
                    animation: 'nw-slide-up var(--motion-normal)',
                  }}
                >
                  {/* Rail Node Dot */}
                  <div
                    style={{
                      position: 'absolute',
                      left: '-24px',
                      top: '10px',
                      width: '15px',
                      height: '15px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--bg-surface)',
                      border: '1px solid var(--border-strong)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      zIndex: 2,
                    }}
                  >
                    {getEventIcon(evt.type)}
                  </div>

                  {/* Event Card */}
                  <Panel
                    padding="sm"
                    style={{
                      backgroundColor: isHypothesis ? 'var(--bg-raised)' : 'var(--bg-surface)',
                      borderColor: isHypothesis ? 'var(--border-strong)' : 'var(--border-subtle)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span
                          style={{
                            fontSize: 'var(--font-size-12)',
                            fontWeight: 600,
                            color: 'var(--text-primary)',
                            textTransform: 'capitalize',
                          }}
                        >
                          {evt.type.replace('_', ' ')}
                        </span>
                        {isToolCall && evt.payload?.tool && (
                          <code
                            className="font-mono"
                            style={{
                              fontSize: '11px',
                              padding: '1px 6px',
                              borderRadius: '4px',
                              backgroundColor: 'var(--bg-ink)',
                              color: 'var(--accent)',
                              border: '1px solid var(--border-subtle)',
                            }}
                          >
                            {evt.payload.tool}
                          </code>
                        )}
                      </div>
                      <span className="tabular-nums" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        {new Date(evt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </span>
                    </div>

                    {/* Hypothesis Card with Confidence Bar */}
                    {isHypothesis ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
                        <p style={{ fontSize: 'var(--font-size-13)', color: 'var(--text-primary)', lineHeight: 1.4 }}>
                          {evt.payload?.hypothesis || evt.payload?.summary || incident.rootCause || 'Root cause identified as bad deploy.'}
                        </p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Confidence:</span>
                          <div
                            style={{
                              flex: 1,
                              maxWidth: '160px',
                              height: '5px',
                              borderRadius: '3px',
                              backgroundColor: 'var(--bg-ink)',
                              overflow: 'hidden',
                            }}
                          >
                            <div
                              style={{
                                width: `${Math.round(conf * 100)}%`,
                                height: '100%',
                                backgroundColor: 'var(--accent)',
                              }}
                            />
                          </div>
                          <span className="tabular-nums" style={{ fontSize: '11px', fontWeight: 600, color: 'var(--accent)' }}>
                            {Math.round(conf * 100)}%
                          </span>
                        </div>
                      </div>
                    ) : isToolCall ? (
                      /* Collapsible tool call */
                      <div style={{ marginTop: '4px' }}>
                        <button
                          onClick={() => toggleToolExpanded(evtId)}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            fontSize: '11px',
                            color: 'var(--text-secondary)',
                            cursor: 'pointer',
                            padding: '2px 0',
                          }}
                        >
                          {isExpanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                          <span>{isExpanded ? 'Hide input & output' : 'Show tool execution'}</span>
                        </button>
                        {isExpanded && (
                          <pre
                            className="font-mono tabular-nums"
                            style={{
                              marginTop: '8px',
                              padding: '10px',
                              borderRadius: 'var(--radius-control)',
                              backgroundColor: 'var(--bg-ink)',
                              border: '1px solid var(--border-subtle)',
                              fontSize: '11px',
                              color: 'var(--text-secondary)',
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word',
                              maxHeight: '220px',
                              overflowY: 'auto',
                            }}
                          >
                            {JSON.stringify(evt.payload, null, 2)}
                          </pre>
                        )}
                      </div>
                    ) : (
                      /* General payload preview */
                      <p style={{ fontSize: 'var(--font-size-13)', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        {typeof evt.payload === 'string'
                          ? evt.payload
                          : evt.payload?.message || evt.payload?.action || JSON.stringify(evt.payload)}
                      </p>
                    )}
                  </Panel>
                </div>
              );
            })}

            {/* Active investigation shimmer row */}
            {incident.status !== 'resolved' && (
              <div
                style={{
                  position: 'relative',
                  paddingLeft: '0',
                  marginTop: '4px',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    left: '-24px',
                    top: '8px',
                    width: '15px',
                    height: '15px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--accent)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <StatusDot status="accent" size={5} pulse={true} />
                </div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-control)',
                    backgroundColor: 'var(--bg-raised)',
                    border: '1px dashed var(--border-strong)',
                  }}
                >
                  <span style={{ fontSize: 'var(--font-size-12)', color: 'var(--text-secondary)' }}>
                    Agent is continuously monitoring diagnostics and sweep metrics...
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Sticky Action & Diagnostics Panels (about 38%) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', position: 'sticky', top: '72px' }}>
          {/* A) Proposed Action Panel */}
          <Panel
            variant="raised"
            padding="md"
            style={{
              borderColor: incident.status === 'awaiting_approval' ? 'var(--status-degraded)' : 'var(--border-subtle)',
              borderWidth: incident.status === 'awaiting_approval' ? '1px' : '1px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span
                style={{
                  fontSize: 'var(--font-size-12)',
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                }}
              >
                Proposed Remediation
              </span>
              <Chip variant="degraded" size="sm">
                Risk: Low
              </Chip>
            </div>

            <p style={{ fontSize: 'var(--font-size-13)', color: 'var(--text-primary)', lineHeight: 1.4 }}>
              <strong>Rollback release to stable v1</strong> on target service <code>{incident.serviceId}</code>.
            </p>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '12px 0' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Confidence:</span>
              <Chip variant="accent" size="sm">
                86% confidence
              </Chip>
            </div>

            {incident.status === 'awaiting_approval' ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <Button
                  variant="primary"
                  onClick={() => setIsApproveDialogOpen(true)}
                  loading={actionLoading}
                  icon={<ThumbsUp size={14} />}
                  style={{ width: '100%' }}
                >
                  Approve and run
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => setIsRejectDialogOpen(true)}
                  disabled={actionLoading}
                  icon={<ThumbsDown size={14} />}
                  style={{ width: '100%' }}
                >
                  Reject with reason
                </Button>
              </div>
            ) : incident.status === 'mitigating' ? (
              <div
                style={{
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-control)',
                  backgroundColor: 'var(--status-degraded-tint)',
                  border: '1px solid rgba(242, 184, 75, 0.25)',
                  fontSize: 'var(--font-size-12)',
                  color: 'var(--status-degraded)',
                }}
              >
                Rollback executed. Waiting for 3 consecutive healthy sweeps to resolve...
              </div>
            ) : incident.status === 'resolved' ? (
              <div
                style={{
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-control)',
                  backgroundColor: 'var(--status-healthy-tint)',
                  border: '1px solid rgba(61, 214, 140, 0.25)',
                  fontSize: 'var(--font-size-12)',
                  color: 'var(--status-healthy)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <CheckCircle2 size={14} />
                <span>Remediation completed. Incident resolved.</span>
              </div>
            ) : (
              <div style={{ fontSize: 'var(--font-size-12)', color: 'var(--text-muted)' }}>
                Investigation in progress. Action gate will activate once hypothesis is confirmed.
              </div>
            )}

            {actionMessage && (
              <p style={{ fontSize: '11px', color: 'var(--accent)', marginTop: '8px' }}>
                {actionMessage}
              </p>
            )}
          </Panel>

          {/* B) Evidence Log Monospace Excerpt */}
          <Panel padding="md">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span
                style={{
                  fontSize: 'var(--font-size-12)',
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                }}
              >
                Error Log Evidence
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={copyEvidenceLog}
                icon={copiedLog ? <Check size={12} /> : <Copy size={12} />}
              >
                {copiedLog ? 'Copied' : 'Copy'}
              </Button>
            </div>
            <pre
              className="font-mono tabular-nums"
              style={{
                padding: '10px',
                borderRadius: 'var(--radius-control)',
                backgroundColor: 'var(--bg-ink)',
                border: '1px solid var(--border-subtle)',
                fontSize: '11px',
                lineHeight: 1.5,
                color: 'var(--text-secondary)',
                overflowX: 'auto',
                whiteSpace: 'pre',
              }}
            >
              <span style={{ color: 'var(--text-muted)' }}>2026-11-04 18:24:12 </span>
              <span style={{ color: 'var(--status-critical)', fontWeight: 600 }}>ERROR </span>
              <span style={{ color: 'var(--text-primary)' }}>[app.checkout:78]</span>{'\n'}
              <span style={{ color: 'var(--status-critical)' }}>TypeError: unsupported operand for *: 'float' and 'NoneType'</span>{'\n'}
              <span style={{ color: 'var(--text-muted)' }}>  File "app/checkout.py", line 78, in apply_discount</span>{'\n'}
              <span style={{ color: 'var(--text-secondary)' }}>    discount_amount = total * rate</span>{'\n'}
              <span style={{ color: 'var(--status-critical)' }}>HTTP 500 (checkout_failed, code=SAVE20)</span>
            </pre>
          </Panel>

          {/* C) Similar Past Incidents (Runbook Memory) */}
          <Panel padding="md">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <History size={14} color="var(--text-muted)" />
                <span
                  style={{
                    fontSize: 'var(--font-size-12)',
                    fontWeight: 600,
                    color: 'var(--text-secondary)',
                    letterSpacing: '0.04em',
                    textTransform: 'uppercase',
                  }}
                >
                  Runbook Memory Match
                </span>
              </div>
              <Chip variant="accent" size="sm">
                92% match
              </Chip>
            </div>
            <div style={{ fontSize: 'var(--font-size-12)', color: 'var(--text-primary)' }}>
              <strong>rb-bad-deploy-v2</strong>
            </div>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px', lineHeight: 1.4 }}>
              Previous occurrence resolved by rolling back deployment. Target service recovered within 3 consecutive sweeps.
            </p>
          </Panel>

          {/* D) Ask Nightwatch Conversational Chat */}
          <Panel padding="none" style={{ display: 'flex', flexDirection: 'column', height: '310px' }}>
            <div
              style={{
                padding: '10px 14px',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <MessageSquare size={13} color="var(--accent)" />
              <span style={{ fontSize: 'var(--font-size-12)', fontWeight: 600, color: 'var(--text-primary)' }}>
                Ask Nightwatch
              </span>
            </div>

            {/* Chat Messages */}
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: '12px 14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              {chatMessages.map((msg, i) => (
                <div
                  key={i}
                  style={{
                    alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                    maxWidth: '85%',
                    backgroundColor: msg.sender === 'user' ? 'var(--bg-hover)' : 'var(--bg-ink)',
                    border: `1px solid ${msg.sender === 'user' ? 'var(--border-strong)' : 'var(--border-subtle)'}`,
                    borderRadius: '6px',
                    padding: '8px 10px',
                  }}
                >
                  <p style={{ fontSize: 'var(--font-size-12)', color: 'var(--text-primary)', lineHeight: 1.4 }}>
                    {msg.text}
                  </p>
                  <span
                    className="tabular-nums"
                    style={{
                      fontSize: '10px',
                      color: 'var(--text-muted)',
                      display: 'block',
                      marginTop: '4px',
                      textAlign: 'right',
                    }}
                  >
                    {msg.time}
                  </span>
                </div>
              ))}
              {isChatSending && (
                <div style={{ alignSelf: 'flex-start', padding: '6px 10px' }}>
                  <Skeleton width="120px" height="12px" />
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* Chat Input */}
            <form
              onSubmit={handleSendChat}
              style={{
                display: 'flex',
                alignItems: 'center',
                borderTop: '1px solid var(--border-subtle)',
                padding: '6px 10px',
                gap: '6px',
                backgroundColor: 'var(--bg-ink)',
              }}
            >
              <input
                type="text"
                placeholder="Ask about git diff, logs, or rollback risk..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={isChatSending}
                style={{
                  flex: 1,
                  padding: '6px 10px',
                  fontSize: 'var(--font-size-12)',
                  backgroundColor: 'transparent',
                  border: 'none',
                }}
              />
              <Button
                type="submit"
                variant="ghost"
                size="sm"
                disabled={!chatInput.trim() || isChatSending}
                icon={<Send size={13} />}
                aria-label="Send message"
              />
            </form>
          </Panel>
        </div>
      </div>

      {/* Approve Confirm Dialog */}
      <Dialog
        isOpen={isApproveDialogOpen}
        onClose={() => setIsApproveDialogOpen(false)}
        title="Approve remediation rollback?"
        description="This will execute an automated rollback to release v1 on the target service (svc-demo-shop) and notify the team on Telegram."
        footer={
          <>
            <Button variant="secondary" size="sm" onClick={() => setIsApproveDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              loading={actionLoading}
              onClick={handleConfirmApprove}
            >
              Confirm and run
            </Button>
          </>
        }
      >
        <div style={{ fontSize: 'var(--font-size-13)', color: 'var(--text-secondary)' }}>
          Target: <code className="font-mono" style={{ color: 'var(--text-primary)' }}>svc-demo-shop</code> • Action: <code className="font-mono" style={{ color: 'var(--accent)' }}>POST /admin/rollback</code>
        </div>
      </Dialog>

      {/* Reject Reason Dialog */}
      <Dialog
        isOpen={isRejectDialogOpen}
        onClose={() => setIsRejectDialogOpen(false)}
        title="Reject proposed remediation"
        description="Provide a brief reason for declining the rollback. This will be recorded in the immutable audit log."
        footer={
          <>
            <Button variant="secondary" size="sm" onClick={() => setIsRejectDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              disabled={!rejectReason.trim()}
              loading={actionLoading}
              onClick={handleConfirmReject}
            >
              Confirm rejection
            </Button>
          </>
        }
      >
        <textarea
          rows={3}
          placeholder="e.g., Fix is already being patched in release v3..."
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          style={{
            width: '100%',
            padding: '8px 10px',
            fontSize: 'var(--font-size-13)',
            resize: 'none',
          }}
        />
      </Dialog>
    </div>
  );
};
