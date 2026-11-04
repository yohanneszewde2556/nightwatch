import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'warning' | 'error' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
}

interface ToastContextType {
  addToast: (type: ToastType, title: string, description?: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export const useToast = () => {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    return {
      addToast: () => {},
    };
  }
  return ctx;
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = useCallback((type: ToastType, title: string, description?: string) => {
    const id = Math.random().toString(36).slice(2, 9);
    setToasts((prev) => [...prev, { id, type, title, description }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const iconMap: Record<ToastType, React.ReactNode> = {
    success: <CheckCircle2 size={16} color="var(--status-healthy)" />,
    warning: <AlertTriangle size={16} color="var(--status-degraded)" />,
    error: <AlertCircle size={16} color="var(--status-critical)" />,
    info: <Info size={16} color="var(--accent)" />,
  };

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          zIndex: 2000,
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          maxWidth: '380px',
          width: '100%',
          pointerEvents: 'none',
        }}
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            style={{
              pointerEvents: 'auto',
              backgroundColor: 'var(--bg-raised)',
              border: '1px solid var(--border-strong)',
              borderRadius: 'var(--radius-control)',
              padding: '12px 14px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              boxShadow: '0 8px 20px rgba(0, 0, 0, 0.4)',
              animation: 'nw-slide-up var(--motion-normal)',
            }}
          >
            <span style={{ marginTop: '1px' }}>{iconMap[toast.type]}</span>
            <div style={{ flex: 1 }}>
              <div
                style={{
                  fontSize: 'var(--font-size-13)',
                  fontWeight: 500,
                  color: 'var(--text-primary)',
                }}
              >
                {toast.title}
              </div>
              {toast.description && (
                <div
                  style={{
                    fontSize: 'var(--font-size-12)',
                    color: 'var(--text-secondary)',
                    marginTop: '2px',
                  }}
                >
                  {toast.description}
                </div>
              )}
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              style={{
                color: 'var(--text-muted)',
                padding: '2px',
                cursor: 'pointer',
              }}
              aria-label="Dismiss toast"
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};
