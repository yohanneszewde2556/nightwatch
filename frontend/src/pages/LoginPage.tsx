import React, { useState } from 'react';
import { Eye, EyeOff, AlertCircle, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/Button';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) {
      setError('Please enter dashboard password');
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const success = await login(password.trim());
      if (!success) {
        setError('Invalid password. Check DASHBOARD_PASSWORD in .env');
      }
    } catch {
      setError('Connection failed. Ensure backend server is running on port 8000.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--bg-ink)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '380px',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
        }}
      >
        {/* Wordmark & Description */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
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
                width="16"
                height="16"
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
            <span
              style={{
                fontSize: 'var(--font-size-16)',
                fontWeight: 600,
                color: 'var(--text-primary)',
                letterSpacing: '-0.02em',
              }}
            >
              Nightwatch
            </span>
          </div>
          <p
            style={{
              fontSize: 'var(--font-size-13)',
              color: 'var(--text-secondary)',
              letterSpacing: '-0.01em',
            }}
          >
            Your on-call engineer, awake 24/7
          </p>
        </div>

        {/* Form Card */}
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-panel)',
            padding: '24px',
          }}
        >
          {error && (
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
                padding: '10px 12px',
                borderRadius: 'var(--radius-control)',
                backgroundColor: 'var(--status-critical-tint)',
                border: '1px solid rgba(255, 107, 107, 0.25)',
                color: 'var(--status-critical)',
                fontSize: 'var(--font-size-12)',
                marginBottom: '16px',
                lineHeight: 1.4,
              }}
            >
              <AlertCircle size={15} style={{ flexShrink: 0, marginTop: '1px' }} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label
                htmlFor="password"
                style={{
                  display: 'block',
                  fontSize: 'var(--font-size-12)',
                  fontWeight: 500,
                  color: 'var(--text-secondary)',
                  marginBottom: '6px',
                }}
              >
                Dashboard Password
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter DASHBOARD_PASSWORD"
                  autoFocus
                  style={{
                    width: '100%',
                    padding: '8px 36px 8px 10px',
                    fontSize: 'var(--font-size-13)',
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute',
                    right: '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={isLoading}
              icon={<ArrowRight size={14} />}
              style={{ width: '100%' }}
            >
              Sign in to War-Room
            </Button>
          </form>

          <div
            style={{
              marginTop: '16px',
              paddingTop: '14px',
              borderTop: '1px solid var(--border-subtle)',
              fontSize: '11px',
              color: 'var(--text-muted)',
              textAlign: 'center',
            }}
          >
            Default dev password: <code className="font-mono" style={{ color: 'var(--text-secondary)' }}>nightwatch-dev-secret</code>
          </div>
        </div>
      </div>
    </div>
  );
};
