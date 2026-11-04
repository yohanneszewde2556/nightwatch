import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Shield, ShieldAlert, LogOut, Flame, BarChart3 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../api/client';
import { DemoChaosModal } from './DemoChaosModal';

export const Navbar: React.FC = () => {
  const { logout } = useAuth();
  const [killSwitch, setKillSwitch] = useState<boolean>(false);
  const [isUpdating, setIsUpdating] = useState<boolean>(false);
  const [isChaosModalOpen, setIsChaosModalOpen] = useState<boolean>(false);

  const fetchKillSwitch = async () => {
    try {
      const settings = await apiClient.getSettings();
      setKillSwitch(settings.killSwitch);
    } catch {
      // ignore in silent polling
    }
  };

  useEffect(() => {
    fetchKillSwitch();
    const interval = setInterval(fetchKillSwitch, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleKillSwitch = async () => {
    setIsUpdating(true);
    try {
      const updated = await apiClient.setKillSwitch(!killSwitch);
      setKillSwitch(updated.killSwitch);
    } catch (err: any) {
      alert(`Failed to update kill switch: ${err.message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <>
      <nav className="navbar">
        <div className="nav-brand">
          <Shield size={20} color="#10b981" />
          <span>Nightwatch</span>
          <span className="brand-badge">AI SRE</span>
        </div>

        <div className="nav-links">
          <NavLink
            to="/"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            end
          >
            Overview
          </NavLink>
          <NavLink
            to="/services"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            Services
          </NavLink>
          <NavLink
            to="/reports"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <BarChart3 size={14} className="inline mr-1 opacity-70" />
            Reports
          </NavLink>
        </div>

        <div className="nav-actions">
          {/* Demo Chaos Controls Trigger */}
          <button
            onClick={() => setIsChaosModalOpen(true)}
            className="btn btn-outline border-amber-500/40 text-amber-400 hover:bg-amber-500/10 hover:border-amber-500/80 transition-all font-semibold"
            title="Open Demo Chaos Control Panel"
          >
            <Flame size={14} className="text-amber-400" />
            <span>Demo Chaos</span>
          </button>

          {/* Kill Switch */}
          <button
            onClick={handleToggleKillSwitch}
            disabled={isUpdating}
            className={`kill-switch-btn ${killSwitch ? 'active' : 'inactive'}`}
            title={killSwitch ? 'Agent is PAUSED. Click to resume.' : 'Agent active. Click to pause all automated actions.'}
          >
            <ShieldAlert size={15} />
            {killSwitch ? 'KILL SWITCH ACTIVE' : 'AGENT RUNNING'}
          </button>

          {/* Logout */}
          <button onClick={logout} className="btn btn-outline" title="Log out">
            <LogOut size={14} />
            <span>Exit</span>
          </button>
        </div>
      </nav>

      {/* Demo Chaos Engineering Modal */}
      <DemoChaosModal
        isOpen={isChaosModalOpen}
        onClose={() => setIsChaosModalOpen(false)}
        onTriggered={() => {
          // Trigger a custom event to notify overview page or components to refresh
          window.dispatchEvent(new CustomEvent('nightwatch:refresh'));
        }}
      />
    </>
  );
};
