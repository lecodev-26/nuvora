import React from 'react';
import TraceView from './TraceView';

/**
 * TestResults — Vista detallada del resultado de un test.
 *
 * Props:
 *   - result: TestRunResult (o null)
 *   - onClose: () => void
 */

const STATUS_STYLES = {
  passed: {
    bg: 'bg-emerald-500/10 border-emerald-500/30',
    text: 'text-emerald-300',
    icon: '✅',
    label: 'PASSED',
  },
  failed: {
    bg: 'bg-red-500/10 border-red-500/30',
    text: 'text-red-300',
    icon: '❌',
    label: 'FAILED',
  },
  error: {
    bg: 'bg-amber-500/10 border-amber-500/30',
    text: 'text-amber-300',
    icon: '⚠️',
    label: 'ERROR',
  },
};

const TestResults = ({ result, onClose }) => {
  if (!result) return null;

  const style = STATUS_STYLES[result.status] || STATUS_STYLES.error;

  return (
    <div className="bg-navy border border-white/10 rounded-xl overflow-hidden">
      {/* Header */}
      <div
        className={`px-4 py-3 border-b ${style.bg} flex items-center justify-between`}
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">{style.icon}</span>
          <span className={`font-bold text-sm ${style.text}`}>
            {style.label}
          </span>
          {result.test_name && (
            <span className="text-white/70 text-sm">· {result.test_name}</span>
          )}
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="text-white/50 hover:text-white text-sm"
          >
            ✕
          </button>
        )}
      </div>

      {/* Stats */}
      <div className="px-4 py-3 border-b border-white/10 grid grid-cols-4 gap-3 text-xs">
        <div>
          <div className="text-white/40 uppercase tracking-wider">Duración</div>
          <div className="text-white font-mono">{result.duration_ms}ms</div>
        </div>
        <div>
          <div className="text-white/40 uppercase tracking-wider">Steps</div>
          <div className="text-white font-mono">{result.steps_used}</div>
        </div>
        <div>
          <div className="text-white/40 uppercase tracking-wider">Assertions</div>
          <div className="font-mono">
            <span className="text-emerald-400">{result.assertions_passed}</span>
            <span className="text-white/40"> / </span>
            <span className="text-red-400">{result.assertions_failed}</span>
          </div>
        </div>
        <div>
          <div className="text-white/40 uppercase tracking-wider">Workflow</div>
          <div className="text-white font-mono text-xs">
            {result.workflow_status || '—'}
          </div>
        </div>
      </div>

      {/* Error técnico (solo si status='error') */}
      {result.status === 'error' && result.error && (
        <div className="px-4 py-3 border-b border-amber-500/30 bg-amber-500/5">
          <div className="text-amber-300 text-xs font-semibold mb-1">
            Error técnico:
          </div>
          <div className="text-amber-200 text-xs font-mono break-words">
            {result.error}
          </div>
        </div>
      )}

      {/* Respuestas generadas */}
      {result.responses && result.responses.length > 0 && (
        <div className="px-4 py-3 border-b border-white/10">
          <div className="text-white/60 text-xs uppercase tracking-wider mb-2">
            Respuestas generadas ({result.responses.length})
          </div>
          <div className="space-y-1">
            {result.responses.map((r, i) => (
              <div
                key={i}
                className="text-white/80 text-xs bg-white/5 rounded px-2 py-1 break-words"
              >
                {r}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Variables finales */}
      {result.variables && Object.keys(result.variables).length > 0 && (
        <div className="px-4 py-3 border-b border-white/10">
          <div className="text-white/60 text-xs uppercase tracking-wider mb-2">
            Variables finales
          </div>
          <pre className="bg-black/30 rounded p-2 text-white/80 text-xs font-mono overflow-x-auto">
            {JSON.stringify(result.variables, null, 2)}
          </pre>
        </div>
      )}

      {/* Trace */}
      <div className="px-4 py-3">
        <div className="text-white/60 text-xs uppercase tracking-wider mb-2">
          Trace de ejecución
        </div>
        <TraceView
          trace={result.trace || []}
          assertionResults={result.assertion_results || []}
        />
      </div>
    </div>
  );
};

export default TestResults;
