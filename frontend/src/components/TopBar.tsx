import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Sliders, ChevronRight } from 'lucide-react';
import { Button } from './ui/Button';
import { Chip } from './ui/Chip';
import { StatusDot } from './ui/StatusDot';

export type AgentStatusType = 'Watching' | 'Investigating' | 'Awaiting approval' | 'Paused';

interface TopBarProps {
  agentStatus: AgentStatusType;
  onOpenDemoControls: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ agentStatus, onOpenDemoControls }) => {
  const location = useLocation();

  // Determine page title & breadcrumbs
  const getBreadcrumb = () => {
    const path = location.pathname;
    if (path === '/') return { title: 'Overview' };
    if (path.startsWith('/incidents/')) {
      const id = path.split('/')[2];
      return {
        title: id,
        parent: { label: 'Overview', to: '/' },
      };
    }
    if (path === '/services') return { title: 'Services' };
    if (path === '/reports') return { title: 'Reports' };
    return { title: 'Dashboard' };
  };

  const breadcrumb = getBreadcrumb();

  const getStatusChip = () => {
    switch (agentStatus) {
      case 'Investigating':
        return (
          <Chip
            variant="accent"
            size="sm"
            icon={<StatusDot status="accent" size={6} pulse={true} />}
          >
            Investigating
          </Chip>
        );
      case 'Awaiting approval':
        return (
          <Chip
            variant="degraded"
            size="sm"
            icon={<StatusDot status="degraded" size={6} pulse={false} />}
          >
            Awaiting approval
          </Chip>
        );
      case 'Paused':
        return (
          <Chip
            variant="neutral"
            size="sm"
            icon={<StatusDot status="neutral" size={6} pulse={false} />}
          >
            Agent paused
          </Chip>
        );
      case 'Watching':
      default:
        return (
          <Chip
            variant="healthy"
            size="sm"
            icon={<StatusDot status="healthy" size={6} pulse={false} />}
          >
            Watching
          </Chip>
        );
    }
  };

  return (
    <header className="app-topbar">
      {/* Title & Breadcrumbs */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {breadcrumb.parent ? (
          <>
            <Link
              to={breadcrumb.parent.to}
              style={{
                fontSize: 'var(--font-size-13)',
                color: 'var(--text-secondary)',
                fontWeight: 500,
                transition: 'color var(--motion-fast)',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
            >
              {breadcrumb.parent.label}
            </Link>
            <ChevronRight size={13} color="var(--text-muted)" />
            <h1
              className="tabular-nums"
              style={{
                fontSize: 'var(--font-size-13)',
                fontWeight: 600,
                color: 'var(--text-primary)',
              }}
            >
              {breadcrumb.title}
            </h1>
          </>
        ) : (
          <h1
            style={{
              fontSize: 'var(--font-size-14)',
              fontWeight: 600,
              color: 'var(--text-primary)',
              letterSpacing: '-0.01em',
            }}
          >
            {breadcrumb.title}
          </h1>
        )}
      </div>

      {/* Right Actions: Agent Status pill & Demo controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {getStatusChip()}

        <Button
          variant="secondary"
          size="sm"
          onClick={onOpenDemoControls}
          icon={<Sliders size={13} />}
          title="Open Demo Controls"
        >
          Demo controls
        </Button>
      </div>
    </header>
  );
};
