import React, { useState } from 'react';
import { Shield, KeyRound, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [password, setPassword] = useState('');
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
    <div className="login-card">
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
        <div style={{
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          padding: '0.75rem',
          borderRadius: '50%',
          border: '1px solid rgba(16, 185, 129, 0.3)',
        }}>
          <Shield size={36} color="#10b981" />
        </div>
      </div>

      <h1 className="login-title">Nightwatch</h1>
      <p className="login-subtitle">
        Autonomous AI On-Call SRE & War-Room Dashboard
      </p>

      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#f87171',
          padding: '0.65rem 0.85rem',
          borderRadius: '0.375rem',
          fontSize: '0.825rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          marginBottom: '1rem',
        }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="password">
            Dashboard Password
          </label>
          <input
            id="password"
            type="password"
            className="form-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter DASHBOARD_PASSWORD..."
            autoFocus
          />
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%', justifyContent: 'center', marginTop: '0.5rem' }}
          disabled={isLoading}
        >
          <KeyRound size={16} />
          <span>{isLoading ? 'Verifying...' : 'Access War-Room'}</span>
        </button>
      </form>

      <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.75rem', color: '#64748b' }}>
        Default dev password: <code style={{ color: '#94a3b8' }}>nightwatch-dev-secret</code>
      </div>
    </div>
  );
};
