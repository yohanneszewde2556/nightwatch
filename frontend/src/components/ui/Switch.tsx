import React from 'react';

export interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  sublabel?: string;
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const Switch: React.FC<SwitchProps> = ({
  checked,
  onChange,
  label,
  sublabel,
  disabled = false,
  className = '',
  style,
}) => {
  return (
    <label
      className={`nw-switch-wrapper ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '12px',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        userSelect: 'none',
        minHeight: '36px',
        ...style,
      }}
    >
      {(label || sublabel) && (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {label && (
            <span
              style={{
                fontSize: 'var(--font-size-13)',
                fontWeight: 500,
                color: 'var(--text-primary)',
              }}
            >
              {label}
            </span>
          )}
          {sublabel && (
            <span
              style={{
                fontSize: 'var(--font-size-12)',
                color: 'var(--text-secondary)',
              }}
            >
              {sublabel}
            </span>
          )}
        </div>
      )}

      {/* Switch Track */}
      <span
        role="switch"
        aria-checked={checked}
        tabIndex={disabled ? -1 : 0}
        onKeyDown={(e) => {
          if (disabled) return;
          if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            onChange(!checked);
          }
        }}
        onClick={(e) => {
          e.preventDefault();
          if (!disabled) onChange(!checked);
        }}
        style={{
          position: 'relative',
          display: 'inline-block',
          width: '38px',
          height: '22px',
          backgroundColor: checked ? 'var(--status-healthy)' : 'var(--bg-ink)',
          border: `1px solid ${checked ? 'var(--status-healthy)' : 'var(--border-strong)'}`,
          borderRadius: '12px',
          transition: 'background-color var(--motion-fast), border-color var(--motion-fast)',
          flexShrink: 0,
        }}
      >
        {/* Thumb */}
        <span
          style={{
            position: 'absolute',
            top: '2px',
            left: checked ? '18px' : '2px',
            width: '16px',
            height: '16px',
            borderRadius: '50%',
            backgroundColor: checked ? '#0D1014' : 'var(--text-muted)',
            transition: 'left var(--motion-fast), background-color var(--motion-fast)',
          }}
        />
      </span>
    </label>
  );
};
