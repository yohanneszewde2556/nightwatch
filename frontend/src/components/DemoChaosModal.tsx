import React, { useState } from 'react';
import { AlertTriangle, CheckCircle, Clock, Flame, Loader2, RefreshCw, X, Zap } from 'lucide-react';
import { apiClient } from '../api/client';

interface DemoChaosModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTriggered?: () => void;
}

export const DemoChaosModal: React.FC<DemoChaosModalProps> = ({
  isOpen,
  onClose,
  onTriggered,
}) => {
  const [loadingScenario, setLoadingScenario] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ text: string; isError?: boolean } | null>(null);

  if (!isOpen) return null;

  const handleChaos = async (scenario: string) => {
    setLoadingScenario(scenario);
    setStatusMessage(null);
    try {
      const res = await apiClient.injectDemoChaos(scenario);
      setStatusMessage({ text: res.message });
      if (onTriggered) onTriggered();
    } catch (err: any) {
      setStatusMessage({ text: err.message || 'Failed to trigger chaos', isError: true });
    } finally {
      setLoadingScenario(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg p-6 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-lg">
            <Flame className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-100">Live Demo Chaos Panel</h2>
            <p className="text-xs text-slate-400">Target service: <span className="font-mono text-emerald-400">Demo Shop API</span> (Port 8001)</p>
          </div>
        </div>

        <p className="text-sm text-slate-300 mb-5">
          Trigger controlled failure scenarios to demonstrate Nightwatch automated detection, investigation, and human-in-the-loop rollback.
        </p>

        {/* Status Message */}
        {statusMessage && (
          <div
            className={`flex items-start gap-2.5 p-3 mb-4 text-xs rounded-lg border ${
              statusMessage.isError
                ? 'bg-rose-950/40 border-rose-800/60 text-rose-300'
                : 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
            }`}
          >
            {statusMessage.isError ? (
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
            ) : (
              <CheckCircle className="w-4 h-4 mt-0.5 shrink-0" />
            )}
            <span>{statusMessage.text}</span>
          </div>
        )}

        {/* Chaos Options */}
        <div className="space-y-3">
          {/* 1. Deploy Bad Release (v2) */}
          <button
            onClick={() => handleChaos('bad_deploy')}
            disabled={loadingScenario !== null}
            className="w-full flex items-center justify-between p-3.5 bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 hover:border-amber-500/50 rounded-lg transition-all group text-left"
          >
            <div className="flex items-start gap-3">
              <div className="p-2 bg-amber-500/10 text-amber-400 rounded-md mt-0.5">
                <Zap className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-200 group-hover:text-amber-400 transition-colors">
                  Deploy Bad Release (v2)
                </div>
                <div className="text-xs text-slate-400">
                  Adds buggy discount codes causing ~70% TypeError error spike on checkout.
                </div>
              </div>
            </div>
            {loadingScenario === 'bad_deploy' ? (
              <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
            ) : (
              <span className="text-xs font-medium px-2 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded">
                Simulate
              </span>
            )}
          </button>

          {/* 2. Inject Latency (Slow) */}
          <button
            onClick={() => handleChaos('slow')}
            disabled={loadingScenario !== null}
            className="w-full flex items-center justify-between p-3.5 bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 hover:border-blue-500/50 rounded-lg transition-all group text-left"
          >
            <div className="flex items-start gap-3">
              <div className="p-2 bg-blue-500/10 text-blue-400 rounded-md mt-0.5">
                <Clock className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
                  Degrade Latency (Slow)
                </div>
                <div className="text-xs text-slate-400">
                  Injects growing artificial delay (up to 6.0s) to simulate thread contention or leaks.
                </div>
              </div>
            </div>
            {loadingScenario === 'slow' ? (
              <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
            ) : (
              <span className="text-xs font-medium px-2 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded">
                Simulate
              </span>
            )}
          </button>

          {/* 3. Crash Service (Down) */}
          <button
            onClick={() => handleChaos('crash')}
            disabled={loadingScenario !== null}
            className="w-full flex items-center justify-between p-3.5 bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 hover:border-rose-500/50 rounded-lg transition-all group text-left"
          >
            <div className="flex items-start gap-3">
              <div className="p-2 bg-rose-500/10 text-rose-400 rounded-md mt-0.5">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-200 group-hover:text-rose-400 transition-colors">
                  Crash Service (Down)
                </div>
                <div className="text-xs text-slate-400">
                  Forces /health to return HTTP 503 Service Unavailable immediately.
                </div>
              </div>
            </div>
            {loadingScenario === 'crash' ? (
              <Loader2 className="w-4 h-4 animate-spin text-rose-400" />
            ) : (
              <span className="text-xs font-medium px-2 py-1 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded">
                Simulate
              </span>
            )}
          </button>

          {/* 4. Reset All to Normal */}
          <button
            onClick={() => handleChaos('reset')}
            disabled={loadingScenario !== null}
            className="w-full flex items-center justify-between p-3.5 bg-emerald-950/20 hover:bg-emerald-950/40 border border-emerald-800/40 hover:border-emerald-500/50 rounded-lg transition-all group text-left"
          >
            <div className="flex items-start gap-3">
              <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-md mt-0.5">
                <RefreshCw className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-200 group-hover:text-emerald-400 transition-colors">
                  Reset to Normal (v1)
                </div>
                <div className="text-xs text-slate-400">
                  Clears all chaos modes and restores application to v1 baseline.
                </div>
              </div>
            </div>
            {loadingScenario === 'reset' ? (
              <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
            ) : (
              <span className="text-xs font-medium px-2 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded">
                Restore
              </span>
            )}
          </button>
        </div>

        <div className="mt-5 pt-4 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
