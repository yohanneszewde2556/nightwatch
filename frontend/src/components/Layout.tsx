import React, { useEffect, useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar, AgentStatusType } from './TopBar';
import { DemoChaosModal } from './DemoChaosModal';
import { ToastProvider } from './ui/Toast';
import { apiClient } from '../api/client';

export const Layout: React.FC = () => {
  const [killSwitch, setKillSwitch] = useState<boolean>(false);
  const [isUpdatingKillSwitch, setIsUpdatingKillSwitch] = useState<boolean>(false);
  const [isChaosModalOpen, setIsChaosModalOpen] = useState<boolean>(false);
  const [agentStatus, setAgentStatus] = useState<AgentStatusType>('Watching');
  const [lastSweepSeconds, setLastSweepSeconds] = useState<number>(4);

  // Poll settings and active incidents
  const fetchState = async () => {
    try {
      const [settings, allIncidents] = await Promise.all([
        apiClient.getSettings().catch(() => null),
        apiClient.getIncidents().catch(() => []),
      ]);
      const incidents = (allIncidents || []).filter((i) => i.status !== 'resolved');

      if (settings) {
        setKillSwitch(settings.killSwitch);
      }

      if (settings?.killSwitch) {
        setAgentStatus('Paused');
      } else if (incidents && incidents.length > 0) {
        const top = incidents[0];
        if (top.status === 'investigating') {
          setAgentStatus('Investigating');
        } else if (top.status === 'mitigating') {
          setAgentStatus('Awaiting approval');
        } else {
          setAgentStatus('Investigating');
        }
      } else {
        setAgentStatus('Watching');
      }

      // Reset sweep timer
      setLastSweepSeconds(0);
    } catch {
      // silent background failure
    }
  };

  useEffect(() => {
    fetchState();
    const pollInterval = setInterval(fetchState, 15000);
    const timerInterval = setInterval(() => {
      setLastSweepSeconds((s) => (s < 15 ? s + 1 : 1));
    }, 1000);

    return () => {
      clearInterval(pollInterval);
      clearInterval(timerInterval);
    };
  }, []);

  const handleToggleKillSwitch = async () => {
    setIsUpdatingKillSwitch(true);
    try {
      const updated = await apiClient.setKillSwitch(!killSwitch);
      setKillSwitch(updated.killSwitch);
      setAgentStatus(updated.killSwitch ? 'Paused' : 'Watching');
    } catch (err: any) {
      alert(`Failed to update kill switch: ${err.message}`);
    } finally {
      setIsUpdatingKillSwitch(false);
    }
  };

  return (
    <ToastProvider>
      <div className="app-layout">
        <Sidebar
          killSwitch={killSwitch}
          isUpdatingKillSwitch={isUpdatingKillSwitch}
          onToggleKillSwitch={handleToggleKillSwitch}
          lastSweepSeconds={lastSweepSeconds}
        />
        <div className="app-main-wrapper">
          <TopBar
            agentStatus={agentStatus}
            onOpenDemoControls={() => setIsChaosModalOpen(true)}
          />
          <main className="app-content">
            <Outlet />
          </main>
        </div>
        <DemoChaosModal
          isOpen={isChaosModalOpen}
          onClose={() => setIsChaosModalOpen(false)}
          onTriggered={() => {
            fetchState();
          }}
        />
      </div>
    </ToastProvider>
  );
};
