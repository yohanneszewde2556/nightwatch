import React from 'react';

export type ChipVariant = 'healthy' | 'degraded' | 'critical' | 'neutral' | 'accent';

export interface ChipProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: ChipVariant;
  label?: string;
  icon?: React.ReactNode;
  size?: 'sm' | 'md';
}

export const Chip: React.FC<ChipProps> = ({
  variant = 'neutral',
  label,
  icon,
  size = 'md',
  children,
  className = '',
  style,
  ...props
}) => {
  const colorMap: Record<ChipVariant, { color: string; bg: string; border: string }> = {
    healthy: {
      color: 'var(--status-healthy)',
      bg: 'var(--status-healthy-tint)',
      border: 'rgba(61, 214, 140, 0.2)',
    },
    degraded: {
      color: 'var(--status-degraded)',
      bg: 'var(--status-degraded-tint)',
      border: 'rgba(242, 184, 75, 0.2)',
    },
    critical: {
      color: 'var(--status-critical)',
      bg: 'var(--status-critical-tint)',
      border: 'rgba(255, 107, 107, 0.2)',
    },
    neutral: {
      color: 'var(--status-neutral)',
      bg: 'var(--status-neutral-tint)',
      border: 'rgba(139, 149, 163, 0.2)',
    },
    accent: {
      color: 'var(--accent)',
      bg: 'var(--accent-tint)',
      border: 'rgba(124, 196, 255, 0.2)',
    },
  };

  const current = colorMap[variant];

  return (
    <span
      className={`nw-chip nw-chip-${variant} ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: size === 'sm' ? '1px 6px' : '2px 8px',
        borderRadius: 'var(--radius-control)',
        fontSize: size === 'sm' ? '11px' : 'var(--font-size-12)',
        fontWeight: 500,
        lineHeight: 1.4,
        color: current.color,
        backgroundColor: current.bg,
        border: `1px solid ${current.border}`,
        whiteSpace: 'nowrap',
        letterSpacing: '0.01em',
        ...style,
      }}
      {...props}
    >
      {icon && <span style={{ display: 'inline-flex', alignItems: 'center' }}>{icon}</span>}
      {label || children}
    </span>
  );
};
