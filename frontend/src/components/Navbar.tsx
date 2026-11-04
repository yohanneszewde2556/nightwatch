import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Shield, ShieldAlert, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../api/client';

export const Navbar: React.FC = () => {
  const { logout } = useAuth();
  const [killSwitch, setKillSwitch] = useState<boolean>(false);
  const [isUpdating, setIsUpdating] = useState<boolean>(false);

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
      </div>

      <div className="nav-actions">
        <button
          onClick={handleToggleKillSwitch}
          disabled={isUpdating}
          className={`kill-switch-btn ${killSwitch ? 'active' : 'inactive'}`}
          title={killSwitch ? 'Agent is PAUSED. Click to resume.' : 'Agent active. Click to pause all automated actions.'}
        >
          <ShieldAlert size={15} />
          {killSwitch ? 'KILL SWITCH ACTIVE' : 'AGENT RUNNING'}
        </button>

        <button onClick={logout} className="btn btn-outline" title="Log out">
          <LogOut size={14} />
          <span>Exit</span>
        </button>
      </div>
    </nav>
  );
};
