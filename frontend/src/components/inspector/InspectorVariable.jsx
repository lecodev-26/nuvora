import React from 'react';

const InspectorVariable = ({ node, onUpdate }) => {
  const name = node.config?.name || '';
  const value = node.config?.value || '';

  return (
    <div className="space-y-3">
      <label className="block">
        <span className="text-white/60 text-xs uppercase tracking-wider">
          Nombre de la variable
        </span>
        <input
          type="text"
          value={name}
          onChange={(e) => onUpdate({ config: { ...node.config, name: e.target.value } })}
          placeholder="Ej: greeting"
          className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white font-mono text-sm focus:outline-none focus:border-fuchsia-400/60"
        />
      </label>

      <label className="block">
        <span className="text-white/60 text-xs uppercase tracking-wider">
          Valor
        </span>
        <input
          type="text"
          value={value}
          onChange={(e) => onUpdate({ config: { ...node.config, value: e.target.value } })}
          placeholder="Ej: Hola {{name}}"
          className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-fuchsia-400/60"
        />
        <span className="text-white/40 text-xs">
          Soporta interpolación: {'{{name}}'}, etc.
        </span>
      </label>

      <label className="block">
        <span className="text-white/60 text-xs uppercase tracking-wider">
          Nombre (opcional)
        </span>
        <input
          type="text"
          value={node.name || ''}
          onChange={(e) => onUpdate({ name: e.target.value })}
          placeholder="Ej: Guardar saludo"
          className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-fuchsia-400/60"
        />
      </label>
    </div>
  );
};

export default InspectorVariable;
