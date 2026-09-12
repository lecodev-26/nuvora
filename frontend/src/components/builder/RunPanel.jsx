import React, { useState, useMemo, useEffect } from 'react';
import { workflowService } from '../../services/workflowApi';
import Button from '../Button';

/**
 * RunPanel — Modal de ejecución del workflow.
 *
 * Props:
 *   - open: boolean
 *   - onClose: () => void
 *   - botId: number
 *   - workflowId: number
 *   - nodes, transitions: estado actual (para detectar variables)
 *   - dirty: boolean  — si hay cambios sin guardar, avisar
 *
 * Flujo:
 *   1. Detecta variables requeridas ({{var}} + question.variable)
 *   2. Usuario rellena inputs
 *   3. POST /workflows/{botId}/{workflowId}/run
 *   4. Muestra resultado (status, outputs, variables, steps)
 */

// Regex de interpolación (mismo que backend 14.5.6)
const VAR_RE = /\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}/g;

function extractVariables(nodes) {
  const vars = new Set();

  for (const n of nodes) {
    const cfg = n.config || {};

    // QUESTION define su variable
    if (n.type === 'question' && cfg.variable) {
      vars.add(cfg.variable);
    }

    // Interpolaciones {{var}} en textos
    const texts = [cfg.text, cfg.value];
    for (const t of texts) {
      if (typeof t !== 'string') continue;
      let m;
      while ((m = VAR_RE.exec(t)) !== null) {
        vars.add(m[1]);
      }
      VAR_RE.lastIndex = 0; // reset (por seguridad)
    }
  }

  return Array.from(vars).sort();
}

const STATUS_COLORS = {
  completed: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  waiting_input: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  failed: 'text-red-400 bg-red-500/10 border-red-500/30',
  running: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
};

const STATUS_LABELS = {
  completed: '✅ Completado',
  waiting_input: '⏸ Esperando entrada',
  failed: '❌ Falló',
  running: '▶ Ejecutando',
};

const RunPanel = ({ open, onClose, botId, workflowId, nodes, dirty }) => {
  const [vars, setVars] = useState({});
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const detectedVars = useMemo(() => extractVariables(nodes), [nodes]);

  // Reiniciar al abrir
  useEffect(() => {
    if (open) {
      setResult(null);
      setError(null);
      // Pre-rellenar vars detectadas con string vacío
      setVars((prev) => {
        const next = {};
        for (const v of detectedVars) {
          next[v] = prev[v] ?? '';
        }
        return next;
      });
    }
  }, [open, detectedVars]);

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    setResult(null);

    try {
      const res = await workflowService.run(botId, workflowId, vars, 100);
      setResult(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        Array.isArray(detail)
          ? detail.map((e) => e.msg || JSON.stringify(e)).join(', ')
          : detail || err.message || 'Error ejecutando workflow'
      );
    } finally {
      setRunning(false);
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-navy border border-white/10 rounded-2xl shadow-card w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div>
            <h2 className="text-white text-lg font-semibold">▶ Probar workflow</h2>
            <p className="text-white/50 text-xs mt-0.5">
              Ejecuta el workflow guardado con variables iniciales.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-white/50 hover:text-white transition-colors text-xl"
          >
            ✕
          </button>
        </div>

        {/* Aviso si hay cambios sin guardar */}
        {dirty && (
          <div className="bg-amber-500/10 border-b border-amber-500/30 px-6 py-2 text-amber-300 text-xs">
            ⚠️ Tienes cambios sin guardar. El workflow se ejecutará con la última
            versión GUARDADA en el servidor.
          </div>
        )}

        {/* Body */}
        <div className="px-6 py-4 overflow-y-auto flex-1 space-y-4">
          {/* Variables */}
          <div>
            <h3 className="text-white/70 text-xs uppercase tracking-wider mb-2">
              Variables iniciales
            </h3>

            {detectedVars.length === 0 ? (
              <p className="text-white/40 text-sm italic">
                Este workflow no requiere variables iniciales.
              </p>
            ) : (
              <div className="space-y-2">
                {detectedVars.map((v) => (
                  <div key={v} className="flex items-center gap-3">
                    <label className="text-white/60 font-mono text-xs w-32 truncate">
                      {v}
                    </label>
                    <input
                      type="text"
                      value={vars[v] ?? ''}
                      onChange={(e) =>
                        setVars((prev) => ({ ...prev, [v]: e.target.value }))
                      }
                      placeholder={`valor para ${v}`}
                      className="flex-1 bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-cyan-400/60"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Ejecutar */}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" size="sm" onClick={onClose}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleRun}
              disabled={running}
            >
              {running ? 'Ejecutando...' : '▶ Ejecutar'}
            </Button>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-300 text-sm">
              ⚠️ {error}
            </div>
          )}

          {/* Resultado */}
          {result && (
            <div className="space-y-3">
              <div
                className={`inline-flex px-3 py-1 rounded-lg border text-sm font-semibold ${
                  STATUS_COLORS[result.status] || STATUS_COLORS.failed
                }`}
              >
                {STATUS_LABELS[result.status] || result.status}
              </div>

              {/* Outputs */}
              <div>
                <h3 className="text-white/70 text-xs uppercase tracking-wider mb-2">
                  Outputs ({result.outputs?.length || 0})
                </h3>
                {result.outputs && result.outputs.length > 0 ? (
                  <div className="space-y-1.5">
                    {result.outputs.map((o, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-3 bg-white/5 rounded-lg px-3 py-2"
                      >
                        <span className="text-white/40 font-mono text-xs shrink-0 mt-0.5">
                          {o.node_id}
                        </span>
                        <span className="text-white/90 text-sm break-words">
                          {o.text || <em className="text-white/40">(vacío)</em>}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-white/40 text-sm italic">Sin outputs generados.</p>
                )}
              </div>

              {/* Variables finales */}
              {result.variables && Object.keys(result.variables).length > 0 && (
                <div>
                  <h3 className="text-white/70 text-xs uppercase tracking-wider mb-2">
                    Variables finales
                  </h3>
                  <pre className="bg-black/30 rounded-lg p-3 text-white/80 text-xs font-mono overflow-x-auto">
                    {JSON.stringify(result.variables, null, 2)}
                  </pre>
                </div>
              )}

              {/* Info */}
              <div className="text-white/40 text-xs pt-2 border-t border-white/10 flex flex-wrap gap-4">
                <div>
                  <span className="text-white/30">steps_used:</span>{' '}
                  <span className="font-mono">{result.steps_used}</span>
                </div>
                <div>
                  <span className="text-white/30">current_node_id:</span>{' '}
                  <span className="font-mono">{result.current_node_id || '—'}</span>
                </div>
                {result.error && (
                  <div className="text-red-300">
                    <span className="text-white/30">error:</span> {result.error}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RunPanel;
