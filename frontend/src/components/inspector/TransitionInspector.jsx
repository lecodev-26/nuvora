import React from 'react';

/**
 * TransitionInspector — panel que aparece al seleccionar una transición (edge).
 *
 * Permite:
 *  - Ver from → to
 *  - Editar label (true/false/custom)
 *  - Editar condition (expresión opcional)
 *  - Borrar transición
 */

const SUPPORTED_OPERATORS = ['==', '!=', '>=', '<=', '>', '<'];

function basicValidate(expr) {
  if (!expr || !expr.trim()) return null; // vacío = "else" implícito, válido
  const match = expr.match(/^\s*\S+\s*(==|!=|>=|<=|>|<)\s*.+$/);
  if (!match) {
    return 'Formato inválido. Se esperaba: variable operador valor';
  }
  return null;
}

const TransitionInspector = ({ transition, onUpdate, onDelete }) => {
  if (!transition) return null;

  const { from_node_id, to_node_id, label, condition } = transition;
  const conditionError = basicValidate(condition);

  return (
    <div>
      {/* Cabecera */}
      <div className="flex items-start justify-between gap-3 pb-3 mb-4 border-b border-white/10">
        <div className="min-w-0">
          <div className="text-xs font-bold tracking-widest text-cyan-300">
            TRANSITION
          </div>
          <div className="text-white/60 text-xs font-mono truncate mt-1">
            {from_node_id} <span className="text-cyan-400">→</span> {to_node_id}
          </div>
        </div>

        {onDelete && (
          <button
            type="button"
            onClick={onDelete}
            className="text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded p-1 transition-colors shrink-0"
            title="Eliminar transición"
          >
            🗑
          </button>
        )}
      </div>

      {/* Label */}
      <label className="block mb-3">
        <span className="text-white/60 text-xs uppercase tracking-wider">
          Etiqueta
        </span>
        <input
          type="text"
          value={label || ''}
          onChange={(e) => onUpdate({ label: e.target.value || null })}
          placeholder="Ej: true, false, ok..."
          className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-400/60"
        />
        <span className="text-white/40 text-xs">
          Puede ser "true", "false" o cualquier texto descriptivo.
        </span>
      </label>

      {/* Condition */}
      <label className="block mb-3">
        <span className="text-white/60 text-xs uppercase tracking-wider">
          Condición (opcional)
        </span>
        <input
          type="text"
          value={condition || ''}
          onChange={(e) => onUpdate({ condition: e.target.value || null })}
          placeholder="Ej: age > 18 (vacío = else implícito)"
          className={`mt-2 w-full bg-black/30 border rounded-lg px-3 py-2 text-white font-mono text-sm focus:outline-none ${
            conditionError
              ? 'border-red-500/60 focus:border-red-400'
              : 'border-white/10 focus:border-cyan-400/60'
          }`}
        />
        {conditionError && (
          <span className="text-red-400 text-xs mt-1 block">⚠️ {conditionError}</span>
        )}
      </label>

      {/* Info */}
      <div className="bg-white/5 rounded-lg p-3 text-xs text-white/50 space-y-1">
        <div className="font-semibold text-white/70 mb-1">Operadores:</div>
        <div className="flex flex-wrap gap-1.5">
          {SUPPORTED_OPERATORS.map((op) => (
            <code key={op} className="bg-black/40 rounded px-1.5 py-0.5 font-mono">
              {op}
            </code>
          ))}
        </div>
        <div className="mt-2 text-white/40">
          <strong className="text-white/60">Nota:</strong> si la transición sale de
          un nodo CONDITION, la condición se evalúa. Si sale de otro tipo, la
          transición es lineal (sin evaluación).
        </div>
      </div>
    </div>
  );
};

export default TransitionInspector;
