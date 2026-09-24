import React from 'react';
import { useNavigate } from 'react-router-dom';
import TraceView from './TraceView';

/**
 * TestResults — Vista detallada del resultado de un test.
 *
 * Props:
 *   - result: TestRunResult (o null)
 *   - botId: number (para el botón "Ir al nodo")
 *   - workflowId: number (para el botón "Ir al nodo")
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

const TestResults = ({ result, botId, workflowId, onClose }) => {
  const navigate = useNavigate();

  if (!result) return null;

  const style = STATUS_STYLES[result.status] || STATUS_STYLES.error;

  const goToNode = (nodeId) => {
    if (!botId || !workflowId) return;
    navigate(`/bots/${botId}/workflows/${workflowId}?node=${nodeId}`);
  };

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

      {/* Error técnico */}
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

      {/* Assertions fallidas con botón "Ir al nodo" */}
      {result.assertion_results?.some((ar) => !ar.passed) && (
        <div className="px-4 py-3 border-b border-white/10 bg-red-500/5">
          <div className="text-red-300 text-xs font-semibold mb-2">
            ❌ Assertions fallidas
          </div>
          <div className="space-y-2">
            {result.assertion_results
              .filter((ar) => !ar.passed)
              .map((ar, i) => {
                // Detectar si podemos extraer un node_id relevante
                let goNodeId = null;
                if (ar.type === 'node_visited' && ar.expected) {
                  // expected: "nodo 'X' visitado"
                  const m = String(ar.expected).match(/'([^']+)'/);
                  if (m) goNodeId = m[1];
                }

                return (
                  <div
                    key={i}
                    className="flex items-start gap-2 text-xs bg-black/20 rounded px-2 py-1.5"
                  >
                    <span className="text-red-400 shrink-0">❌</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-mono text-white/80">{ar.type}</div>
                      {ar.message && (
                        <div className="text-white/60 mt-0.5">{ar.message}</div>
                      )}
                      {ar.actual !== undefined && ar.actual !== null && (
                        <div className="text-white/40 mt-0.5">
                          actual: <span className="font-mono">{JSON.stringify(ar.actual)}</span>
                        </div>
                      )}
                    </div>
                    {goNodeId && (
                      <button
                        type="button"
                        onClick={() => goToNode(goNodeId)}
                        className="text-cyan-400 hover:text-cyan-300 text-xs shrink-0 whitespace-nowrap"
                        title={`Ir al nodo '${goNodeId}' en el Builder`}
                      >
                        Ir al nodo →
                      </button>
                    )}
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Respuestas */}
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

      {/* Variables */}
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
