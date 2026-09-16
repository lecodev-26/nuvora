import React from 'react';

/**
 * TraceView — Visualización del trace de ejecución.
 *
 * Props:
 *   - trace: array de TestStepTrace ({step, node_id, type, output})
 *   - assertionResults: array de AssertionResult (opcional)
 */

const NODE_ICONS = {
  start: '▶',
  message: '💬',
  question: '❓',
  condition: '◆',
  variable: '𝑥',
  response: '↩',
  end: '■',
};

const NODE_COLORS = {
  start: 'text-emerald-400',
  message: 'text-cyan-400',
  question: 'text-violet-400',
  condition: 'text-amber-400',
  variable: 'text-fuchsia-400',
  response: 'text-blue-400',
  end: 'text-red-400',
};

const TraceView = ({ trace = [], assertionResults = [] }) => {
  if (!trace || trace.length === 0) {
    return (
      <div className="text-white/40 text-sm italic">
        Sin trace de ejecución (el workflow no se ejecutó o falló antes de empezar).
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Trace de nodos */}
      <div className="space-y-1">
        {trace.map((step, i) => (
          <div key={i} className="flex items-start gap-2">
            {/* Conector vertical */}
            <div className="flex flex-col items-center shrink-0 pt-1">
              <div className="w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-xs">
                {step.step}
              </div>
              {i < trace.length - 1 && (
                <div className="w-px h-6 bg-white/10" />
              )}
            </div>

            {/* Info nodo */}
            <div className="flex-1 min-w-0 pt-0.5">
              <div className="flex items-center gap-2">
                <span
                  className={`text-base ${NODE_COLORS[step.type] || 'text-white/60'}`}
                >
                  {NODE_ICONS[step.type] || '●'}
                </span>
                <span className="text-white font-mono text-xs">
                  {step.node_id}
                </span>
                <span className="text-white/40 text-[10px] uppercase tracking-wider">
                  {step.type}
                </span>
              </div>
              {step.output && (
                <div className="mt-1 ml-6 text-white/70 text-xs bg-white/5 rounded px-2 py-1 break-words">
                  {step.output}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Assertions resumen */}
      {assertionResults.length > 0 && (
        <div className="mt-4 pt-3 border-t border-white/10">
          <div className="text-white/60 text-xs uppercase tracking-wider mb-2">
            Assertions
          </div>
          <div className="space-y-1">
            {assertionResults.map((ar, i) => (
              <div
                key={i}
                className={`
                  flex items-start gap-2 text-xs rounded px-2 py-1
                  ${ar.passed ? 'text-emerald-300' : 'text-red-300'}
                `}
              >
                <span className="shrink-0">{ar.passed ? '✅' : '❌'}</span>
                <div className="min-w-0 flex-1">
                  <span className="font-mono">{ar.type}</span>
                  {ar.message && !ar.passed && (
                    <div className="text-white/60 mt-0.5">{ar.message}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TraceView;
