import React from 'react';

export interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
}

export interface TabsProps {
  items: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  variant?: 'segmented' | 'underline';
  size?: 'sm' | 'md';
  style?: React.CSSProperties;
}

export const Tabs: React.FC<TabsProps> = ({
  items,
  activeId,
  onChange,
  variant = 'segmented',
  size = 'md',
  style,
}) => {
  if (variant === 'segmented') {
    return (
      <div
        role="tablist"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          backgroundColor: 'var(--bg-ink)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-control)',
          padding: '2px',
          gap: '2px',
          ...style,
        }}
      >
        {items.map((tab) => {
          const isActive = tab.id === activeId;
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={isActive}
              onClick={() => onChange(tab.id)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: size === 'sm' ? '3px 8px' : '5px 12px',
                borderRadius: '4px',
                fontSize: size === 'sm' ? 'var(--font-size-12)' : 'var(--font-size-13)',
                fontWeight: isActive ? 600 : 400,
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                backgroundColor: isActive ? 'var(--bg-raised)' : 'transparent',
                border: isActive ? '1px solid var(--border-subtle)' : '1px solid transparent',
                transition: 'all var(--motion-fast)',
                cursor: 'pointer',
              }}
            >
              {tab.icon}
              {tab.label}
              {tab.badge && <span style={{ marginLeft: '2px' }}>{tab.badge}</span>}
            </button>
          );
        })}
      </div>
    );
  }

  // Underline tab variant
  return (
    <div
      role="tablist"
      style={{
        display: 'flex',
        borderBottom: '1px solid var(--border-subtle)',
        gap: '20px',
        ...style,
      }}
    >
      {items.map((tab) => {
        const isActive = tab.id === activeId;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '10px 0',
              fontSize: 'var(--font-size-13)',
              fontWeight: isActive ? 600 : 400,
              color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
              borderBottom: `2px solid ${isActive ? 'var(--accent)' : 'transparent'}`,
              marginBottom: '-1px',
              transition: 'color var(--motion-fast)',
              cursor: 'pointer',
            }}
          >
            {tab.icon}
            {tab.label}
            {tab.badge}
          </button>
        );
      })}
    </div>
  );
};
