import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Server, BarChart2, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Switch } from './ui/Switch';

interface SidebarProps {
  killSwitch: boolean;
  isUpdatingKillSwitch: boolean;
  onToggleKillSwitch: () => void;
  lastSweepSeconds: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  killSwitch,
  isUpdatingKillSwitch,
  onToggleKillSwitch,
  lastSweepSeconds,
}) => {
  const { logout } = useAuth();

  const navItems = [
    { to: '/', label: 'Overview', icon: <LayoutDashboard size={16} /> },
    { to: '/services', label: 'Services', icon: <Server size={16} /> },
    { to: '/reports', label: 'Reports', icon: <BarChart2 size={16} /> },
  ];

  return (
    <aside className="app-sidebar" aria-label="Main Navigation">
      {/* Brand Header */}
      <div
        className="sidebar-header"
        style={{
          height: '52px',
          padding: '0 16px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        {/* Custom SVG Crescent Mark */}
        <div
          style={{
            width: '26px',
            height: '26px',
            borderRadius: '6px',
            backgroundColor: 'var(--bg-raised)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <svg
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--accent)"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
        </div>
        <div className="sidebar-wordmark-text">
          <span
            style={{
              fontSize: 'var(--font-size-14)',
              fontWeight: 600,
              color: 'var(--text-primary)',
              letterSpacing: '-0.02em',
            }}
          >
            Nightwatch
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav
        className="sidebar-nav"
        style={{
          flex: 1,
          padding: '12px 8px',
          display: 'flex',
          flexDirection: 'column',
          gap: '2px',
        }}
      >
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `sidebar-nav-link ${isActive ? 'active' : ''}`}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '8px 10px',
              borderRadius: 'var(--radius-control)',
              fontSize: 'var(--font-size-13)',
              fontWeight: isActive ? 500 : 400,
              color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
              backgroundColor: isActive ? 'var(--bg-raised)' : 'transparent',
              border: isActive ? '1px solid var(--border-subtle)' : '1px solid transparent',
              transition: 'background-color var(--motion-fast), color var(--motion-fast)',
            })}
          >
            <span style={{ display: 'inline-flex', alignItems: 'center', opacity: 0.9 }}>
              {item.icon}
            </span>
            <span className="sidebar-link-text">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Bottom Panel */}
      <div
        className="sidebar-bottom"
        style={{
          padding: '14px 16px',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          backgroundColor: 'var(--bg-ink)',
        }}
      >
        {/* System sweep status */}
        <div
          className="sidebar-system-panel"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: 'var(--font-size-12)',
            color: 'var(--text-muted)',
          }}
        >
          <span>Health sweep</span>
          <span className="tabular-nums" style={{ color: 'var(--text-secondary)' }}>
            {lastSweepSeconds}s ago
          </span>
        </div>

        {/* Kill switch labeled switch */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span
              style={{
                fontSize: 'var(--font-size-12)',
                fontWeight: 500,
                color: 'var(--text-primary)',
              }}
            >
              Agent actions
            </span>
            <span
              style={{
                fontSize: '11px',
                color: killSwitch ? 'var(--status-critical)' : 'var(--status-healthy)',
              }}
            >
              {killSwitch ? 'Paused' : 'On'}
            </span>
          </div>
          <Switch
            checked={!killSwitch}
            onChange={() => onToggleKillSwitch()}
            disabled={isUpdatingKillSwitch}
            aria-label="Toggle agent automated actions"
          />
        </div>

        {/* Logout button */}
        <button
          onClick={logout}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: 'var(--font-size-12)',
            color: 'var(--text-muted)',
            padding: '4px 0',
            marginTop: '4px',
            cursor: 'pointer',
            transition: 'color var(--motion-fast)',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
        >
          <LogOut size={13} />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  );
};
