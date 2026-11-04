import React from 'react';

export interface StatProps {
  label: string;
  value: React.ReactNode;
  unit?: string;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'neutral';
  subtext?: string;
  className?: string;
  style?: React.CSSProperties;
}

export const Stat: React.FC<StatProps> = ({
  label,
  value,
  unit,
  delta,
  deltaType = 'neutral',
  subtext,
  className = '',
  style,
}) => {
  const deltaColorMap = {
    positive: 'var(--status-healthy)',
    negative: 'var(--status-critical)',
    neutral: 'var(--text-muted)',
  };

  return (
    <div
      className={`nw-stat ${className}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        ...style,
      }}
    >
      <span
        style={{
          fontSize: 'var(--font-size-12)',
          color: 'var(--text-secondary)',
          fontWeight: 500,
          letterSpacing: '0.02em',
          textTransform: 'uppercase',
        }}
      >
        {label}
      </span>
      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          gap: '4px',
        }}
      >
        <span
          className="tabular-nums"
          style={{
            fontSize: 'var(--font-size-28)',
            fontWeight: 600,
            lineHeight: 1.1,
            color: 'var(--text-primary)',
            letterSpacing: '-0.02em',
          }}
        >
          {value}
        </span>
        {unit && (
          <span
            style={{
              fontSize: 'var(--font-size-13)',
              color: 'var(--text-muted)',
              fontWeight: 400,
            }}
          >
            {unit}
          </span>
        )}
      </div>
      {(delta || subtext) && (
        <div
          style={{
            fontSize: 'var(--font-size-12)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            marginTop: '2px',
          }}
        >
          {delta && (
            <span
              className="tabular-nums"
              style={{
                color: deltaColorMap[deltaType],
                fontWeight: 500,
              }}
            >
              {delta}
            </span>
          )}
          {subtext && (
            <span style={{ color: 'var(--text-muted)' }}>
              {subtext}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
