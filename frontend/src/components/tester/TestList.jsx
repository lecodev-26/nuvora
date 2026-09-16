import React, { useState } from 'react';
import Button from '../Button';

/**
 * TestList — Lista de tests guardados.
 *
 * Props:
 *   - tests: array de TestCaseResponse
 *   - onRun: (testId) => void
 *   - onEdit: (testId) => void
 *   - onDelete: (testId) => void
 *   - onToggleEnabled: (testId) => void
 *   - lastResults: dict { [testId]: TestRunResult } con resultados por test
 *   - loading: boolean
 */

const STATUS_COLORS = {
  passed: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  failed: 'bg-red-500/20 text-red-300 border-red-500/40',
  error: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
};

const STATUS_LABELS = {
  passed: '✅ PASSED',
  failed: '❌ FAILED',
  error: '⚠️ ERROR',
};

const TestList = ({
  tests = [],
  onRun,
  onEdit,
  onDelete,
  onToggleEnabled,
  lastResults = {},
  loading = false,
}) => {
  const [expandedId, setExpandedId] = useState(null);

  if (loading) {
    return (
      <div className="text-center text-white/40 py-8">
        Cargando tests...
      </div>
    );
  }

  if (tests.length === 0) {
    return (
      <div className="text-center text-white/40 py-8 border border-dashed border-white/10 rounded-lg">
        <div className="text-4xl mb-2">🧪</div>
        <div className="text-sm">
          Aún no hay tests. Crea el primero o genera automáticamente.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {tests.map((test) => {
        const result = lastResults[test.id];
        const expanded = expandedId === test.id;

        return (
          <div
            key={test.id}
            className={`
              border rounded-lg transition-all
              ${test.enabled
                ? 'border-white/10 bg-white/5'
                : 'border-white/5 bg-white/[0.02] opacity-60'}
            `}
          >
            {/* Fila principal */}
            <div className="flex items-center gap-3 p-3">
              {/* Toggle enabled */}
              <input
                type="checkbox"
                checked={test.enabled}
                onChange={() => onToggleEnabled && onToggleEnabled(test.id)}
                className="w-4 h-4 cursor-pointer accent-cyan-400"
                title={test.enabled ? 'Deshabilitar test' : 'Habilitar test'}
              />

              {/* Info */}
              <button
                type="button"
                onClick={() => setExpandedId(expanded ? null : test.id)}
                className="flex-1 text-left min-w-0"
              >
                <div className="text-white font-medium text-sm truncate">
                  {test.name}
                </div>
                <div className="text-white/40 text-xs truncate">
                  {test.input_messages?.length || 0} mensajes ·{' '}
                  {test.assertions?.length || 0} assertions
                </div>
              </button>

              {/* Último resultado */}
              {result && (
                <span
                  className={`
                    px-2 py-1 rounded text-[10px] font-bold tracking-wider
                    border ${STATUS_COLORS[result.status] || STATUS_COLORS.error}
                  `}
                >
                  {STATUS_LABELS[result.status] || result.status}
                </span>
              )}

              {/* Acciones */}
              <div className="flex items-center gap-1 shrink-0">
                <button
                  type="button"
                  onClick={() => onRun && onRun(test.id)}
                  disabled={!test.enabled}
                  className={`
                    px-2 py-1 rounded text-sm transition-colors
                    ${test.enabled
                      ? 'text-cyan-400 hover:bg-cyan-500/10'
                      : 'text-white/20 cursor-not-allowed'}
                  `}
                  title="Ejecutar test"
                >
                  ▶
                </button>
                <button
                  type="button"
                  onClick={() => onEdit && onEdit(test.id)}
                  className="px-2 py-1 rounded text-sm text-white/60 hover:text-white hover:bg-white/10 transition-colors"
                  title="Editar"
                >
                  ✎
                </button>
                <button
                  type="button"
                  onClick={() => onDelete && onDelete(test.id)}
                  className="px-2 py-1 rounded text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                  title="Eliminar"
                >
                  🗑
                </button>
              </div>
            </div>

            {/* Detalle expandido */}
            {expanded && (
              <div className="border-t border-white/10 p-3 space-y-2 text-xs">
                {test.description && (
                  <div>
                    <span className="text-white/40">Descripción: </span>
                    <span className="text-white/80">{test.description}</span>
                  </div>
                )}

                <div>
                  <span className="text-white/40">Mensajes:</span>
                  <ul className="ml-4 mt-1 text-white/70 space-y-0.5">
                    {test.input_messages?.map((m, i) => (
                      <li key={i} className="truncate">
                        <span className="text-white/40">{i + 1}.</span> {m}
                      </li>
                    ))}
                  </ul>
                </div>

                {test.initial_variables &&
                  Object.keys(test.initial_variables).length > 0 && (
                    <div>
                      <span className="text-white/40">Variables iniciales:</span>
                      <pre className="mt-1 bg-black/30 rounded p-2 overflow-x-auto text-white/80">
                        {JSON.stringify(test.initial_variables, null, 2)}
                      </pre>
                    </div>
                  )}

                <div>
                  <span className="text-white/40">Assertions:</span>
                  <ul className="ml-4 mt-1 text-white/70 space-y-0.5">
                    {test.assertions?.map((a, i) => (
                      <li key={i}>
                        <span className="text-cyan-400">{a.type}</span>
                        {a.value && <span className="text-white/60"> → '{a.value}'</span>}
                        {a.node_id && <span className="text-white/60"> → {a.node_id}</span>}
                        {a.variable && (
                          <span className="text-white/60">
                            {' '}→ {a.variable}
                            {a.expected !== undefined && ` == ${JSON.stringify(a.expected)}`}
                          </span>
                        )}
                        {a.max_steps && <span className="text-white/60"> → {a.max_steps}</span>}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Resultado expandido */}
                {result && (
                  <div className="pt-2 border-t border-white/10">
                    {result.status === 'passed' && (
                      <div className="text-emerald-400">
                        ✅ {result.assertions_passed} assertions passed
                        {' · '}
                        {result.steps_used} steps
                        {' · '}
                        {result.duration_ms}ms
                      </div>
                    )}
                    {result.status === 'failed' && (
                      <div className="space-y-1">
                        <div className="text-red-400">
                          ❌ {result.assertions_failed} assertions failed ·{' '}
                          {result.assertions_passed} passed
                        </div>
                        {result.assertion_results
                          ?.filter((ar) => !ar.passed)
                          .map((ar, i) => (
                            <div
                              key={i}
                              className="bg-red-500/10 rounded p-2 text-red-300"
                            >
                              <div className="font-mono">{ar.type}</div>
                              <div className="text-white/60">{ar.message}</div>
                            </div>
                          ))}
                      </div>
                    )}
                    {result.status === 'error' && (
                      <div className="bg-amber-500/10 rounded p-2 text-amber-300">
                        ⚠️ {result.error}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default TestList;
