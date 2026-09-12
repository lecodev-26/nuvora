import React from 'react';

/**
 * InspectorCondition — editor de condición.
 * El backend valida con validate_condition_expression.
 * Aquí solo hacemos una validación local "ligera" para UX.
 */

const SUPPORTED_OPERATORS = ['==', '!=', '>=', '<=', '>', '<'];

function basicValidate(expr) {
  if (!expr || !expr.trim()) return 'La condición no puede estar vacía';
  const match = expr.match(/^\s*\S+\s*(==|!=|>=|<=|>|<)\s*.+$/);
  if (!match) {
    return 'Formato inválido. Se esperaba: variable operador valor (ej: age > 18)';
  }
  return null;
}

const InspectorCondition = ({ node, onUpdate }) => {
  const condition = node.config?.condition || '';
  const error = condition ? basicValidate(condition) : null;

  return (
    <div className="space-y-3">
      <label className="block">
        <span className="text-white/60 text-xs uppercase tracking-wider">
          Condición
        </span>
        <input
          type="text"
          value={condition}
          onChange={(e) => onUpdate({ config: { ...node.config, condition: e.target.value } })}
          placeholder="Ej: age > 18"
          className={`mt-2 w-full bg-black/30 border rounded-lg px-3 py-2 text-white font-mono text-sm focus:outline-none ${
            error
              ? 'border-red-500/60 focus:border-red-400'
              : 'border-white/10 focus:border-amber-400/60'
          }`}
        />
        {error && (
          <span className="text-red-400 text-xs mt-1 block">⚠️ {error}</span>
        )}
      </label>

      <div className="bg-white/5 rounded-lg p-3 text-xs text-white/50 space-y-1">
        <div className="font-semibold text-white/70 mb-1">Operadores soportados:</div>
        <div className="flex flex-wrap gap-1.5">
          {SUPPORTED_OPERATORS.map((op) => (
            <code key={op} className="bg-black/40 rounded px-1.5 py-0.5 font-mono">
              {op}
            </code>
          ))}
        </div>
        <div className="mt-2 text-white/40">
          Ejemplos: <code className="text-white/60">age &gt; 18</code>,{' '}
          <code className="text-white/60">name == "Manuel"</code>,{' '}
          <code className="text-white/60">status != "cancelled"</code>
        </div>
      </div>

      <label className="block">
        <span className="text-white/60 text-xs uppercase tracking-wider">
          Nombre (opcional)
        </span>
        <input
          type="text"
          value={node.name || ''}
          onChange={(e) => onUpdate({ name: e.target.value })}
          placeholder="Ej: Comprobar edad"
          className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-amber-400/60"
        />
      </label>
    </div>
  );
};

export default InspectorCondition;
