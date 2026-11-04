import React, { useState } from 'react';
import { Play, RotateCcw, AlertTriangle, Activity, AlertOctagon, Info } from 'lucide-react';
import { apiClient } from '../api/client';
import { Dialog } from './ui/Dialog';
import { Button } from './ui/Button';
import { Chip } from './ui/Chip';

interface DemoChaosModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTriggered?: () => void;
}

export const DemoChaosModal: React.FC<DemoChaosModalProps> = ({
  isOpen,
  onClose,
  onTriggered,
}) => {
  const [loadingScenario, setLoadingScenario] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ text: string; isError?: boolean } | null>(null);

  const handleChaos = async (scenario: string) => {
    setLoadingScenario(scenario);
    setStatusMessage(null);
    try {
      const res = await apiClient.injectDemoChaos(scenario);
      setStatusMessage({ text: res.message });
      if (onTriggered) onTriggered();
    } catch (err: any) {
      setStatusMessage({ text: err.message || 'Failed to trigger scenario', isError: true });
    } finally {
      setLoadingScenario(null);
    }
  };

  const scenarios = [
    {
      id: 'bad_deploy',
      title: 'Deploy bad release (v2)',
      description: 'Applies discount code bug in checkout.py, raising 500 errors on ~70% of orders.',
      icon: <AlertTriangle size={15} color="var(--status-critical)" />,
      badge: 'P1 Deploy Bug',
      badgeVariant: 'critical' as const,
    },
    {
      id: 'slow',
      title: 'Inject slowness',
      description: 'Adds 2,500ms artificial latency to responses, triggering high-latency alerts.',
      icon: <Activity size={15} color="var(--status-degraded)" />,
      badge: 'P2 Latency',
      badgeVariant: 'degraded' as const,
    },
    {
      id: 'crash',
      title: 'Take service down',
      description: 'Forces /health endpoint to respond with HTTP 503 Service Unavailable.',
      icon: <AlertOctagon size={15} color="var(--status-critical)" />,
      badge: 'P1 Outage',
      badgeVariant: 'critical' as const,
    },
    {
      id: 'reset',
      title: 'Reset to healthy (v1)',
      description: 'Restores stable v1 release and clears all latency and chaos flags.',
      icon: <RotateCcw size={15} color="var(--status-healthy)" />,
      badge: 'Recovery',
      badgeVariant: 'healthy' as const,
    },
  ];

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Demo controls"
      description="Inject controlled failures into the demo-shop service (port 8001) to demonstrate autonomous detection, Gemini triage, and human-in-the-loop rollback."
      maxWidth="540px"
      footer={
        <div style={{ display: 'flex', width: '100%', alignItems: 'center', justifyContent: 'space-between' }}>
          <Chip variant="neutral" size="sm" icon={<Info size={12} />}>
            Demo Environment Only
          </Chip>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {scenarios.map((sc) => {
          const isLoading = loadingScenario === sc.id;
          return (
            <div
              key={sc.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 14px',
                borderRadius: 'var(--radius-control)',
                backgroundColor: 'var(--bg-raised)',
                border: '1px solid var(--border-subtle)',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', flex: 1 }}>
                <div style={{ marginTop: '3px' }}>{sc.icon}</div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        fontSize: 'var(--font-size-13)',
                        fontWeight: 600,
                        color: 'var(--text-primary)',
                      }}
                    >
                      {sc.title}
                    </span>
                    <Chip variant={sc.badgeVariant} size="sm">
                      {sc.badge}
                    </Chip>
                  </div>
                  <p
                    style={{
                      fontSize: 'var(--font-size-12)',
                      color: 'var(--text-secondary)',
                      marginTop: '3px',
                      lineHeight: 1.35,
                    }}
                  >
                    {sc.description}
                  </p>
                </div>
              </div>
              <Button
                variant={sc.id === 'reset' ? 'secondary' : 'secondary'}
                size="sm"
                loading={isLoading}
                onClick={() => handleChaos(sc.id)}
                icon={<Play size={12} />}
              >
                Trigger
              </Button>
            </div>
          );
        })}

        {statusMessage && (
          <div
            style={{
              marginTop: '6px',
              padding: '10px 12px',
              borderRadius: 'var(--radius-control)',
              fontSize: 'var(--font-size-12)',
              backgroundColor: statusMessage.isError ? 'var(--status-critical-tint)' : 'var(--status-healthy-tint)',
              color: statusMessage.isError ? 'var(--status-critical)' : 'var(--status-healthy)',
              border: `1px solid ${statusMessage.isError ? 'rgba(255, 107, 107, 0.25)' : 'rgba(61, 214, 140, 0.25)'}`,
            }}
          >
            {statusMessage.text}
          </div>
        )}
      </div>
    </Dialog>
  );
};
