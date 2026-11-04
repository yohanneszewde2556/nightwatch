import React from 'react';

export type StatusDotType = 'healthy' | 'degraded' | 'critical' | 'neutral' | 'accent';

export interface StatusDotProps {
  status: StatusDotType;
  pulse?: boolean;
  size?: number;
  className?: string;
  style?: React.CSSProperties;
}

export const StatusDot: React.FC<StatusDotProps> = ({
  status,
  pulse = false,
  size = 7,
  className = '',
  style,
}) => {
  const colorMap: Record<StatusDotType, string> = {
    healthy: 'var(--status-healthy)',
    degraded: 'var(--status-degraded)',
    critical: 'var(--status-critical)',
    neutral: 'var(--status-neutral)',
    accent: 'var(--accent)',
  };

  const color = colorMap[status] || colorMap.neutral;

  return (
    <span
      className={`nw-status-dot-wrapper ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        width: `${size}px`,
        height: `${size}px`,
        ...style,
      }}
      aria-hidden="true"
    >
      {pulse && (
        <span
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            borderRadius: '50%',
            backgroundColor: color,
            opacity: 0.6,
            animation: 'nw-pulse 1.8s ease-in-out infinite',
          }}
        />
      )}
      <span
        style={{
          width: `${size}px`,
          height: `${size}px`,
          borderRadius: '50%',
          backgroundColor: color,
          display: 'block',
        }}
      />
    </span>
  );
};
