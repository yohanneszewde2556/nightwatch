import React from 'react';

export interface PanelProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'surface' | 'raised' | 'bordered';
  hoverable?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Panel: React.FC<PanelProps> = ({
  variant = 'surface',
  hoverable = false,
  padding = 'md',
  children,
  className = '',
  style,
  ...props
}) => {
  const paddingMap = {
    none: '0',
    sm: '12px',
    md: '16px',
    lg: '20px',
  };

  const bgMap = {
    surface: 'var(--bg-surface)',
    raised: 'var(--bg-raised)',
    bordered: 'transparent',
  };

  return (
    <div
      className={`nw-panel nw-panel-${variant} ${hoverable ? 'nw-panel-hoverable' : ''} ${className}`}
      style={{
        backgroundColor: bgMap[variant],
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-panel)',
        padding: paddingMap[padding],
        transition: hoverable ? 'border-color var(--motion-fast), background var(--motion-fast)' : undefined,
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  );
};
