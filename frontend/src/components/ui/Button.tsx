import React from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: React.ReactNode;
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'secondary',
  size = 'md',
  icon,
  loading = false,
  children,
  className = '',
  disabled,
  style,
  ...props
}) => {
  const baseStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    borderRadius: 'var(--radius-control)',
    fontWeight: 500,
    fontSize: size === 'sm' ? 'var(--font-size-12)' : 'var(--font-size-13)',
    lineHeight: 1,
    transition: 'background var(--motion-fast), border-color var(--motion-fast), color var(--motion-fast)',
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    opacity: disabled || loading ? 0.5 : 1,
    whiteSpace: 'nowrap',
    userSelect: 'none',
    minHeight: size === 'sm' ? '32px' : size === 'lg' ? '42px' : '36px',
    padding: size === 'sm' ? '0 10px' : size === 'lg' ? '0 16px' : '0 12px',
    border: '1px solid transparent',
  };

  const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
    primary: {
      backgroundColor: 'var(--accent)',
      color: '#0D1014',
      fontWeight: 600,
    },
    secondary: {
      backgroundColor: 'var(--bg-raised)',
      color: 'var(--text-primary)',
      borderColor: 'var(--border-subtle)',
    },
    ghost: {
      backgroundColor: 'transparent',
      color: 'var(--text-secondary)',
    },
    danger: {
      backgroundColor: 'var(--status-critical-tint)',
      color: 'var(--status-critical)',
      borderColor: 'rgba(255, 107, 107, 0.25)',
    },
  };

  return (
    <button
      className={`nw-button nw-button-${variant} nw-button-${size} ${className}`}
      disabled={disabled || loading}
      style={{
        ...baseStyle,
        ...variantStyles[variant],
        ...style,
      }}
      {...props}
    >
      {loading ? (
        <span
          style={{
            width: '14px',
            height: '14px',
            border: '2px solid currentColor',
            borderTopColor: 'transparent',
            borderRadius: '50%',
            animation: 'nw-spin 0.6s linear infinite',
            display: 'inline-block',
          }}
          aria-hidden="true"
        />
      ) : (
        icon && <span style={{ display: 'inline-flex', alignItems: 'center' }}>{icon}</span>
      )}
      {children}
    </button>
  );
};
