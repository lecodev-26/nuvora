import React from 'react';

const InspectorMessage = ({ node, onUpdate }) => {
  const text = node.config?.text || '';

  return (
    <div className="space-y-3">
      <label className="block">
        <span className="text-white/60 text-xs uppercase tracking-wider">
          Mensaje
        </span>
        <textarea
          value={text}
          onChange={(e) => onUpdate({ config: { ...node.config, text: e.target.value } })}
          rows={5}
          placeholder="Escribe el mensaje... Usa {{variable}} para interpolar."
          className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-400/60 resize-none"
        />
        <span className="text-white/40 text-xs">
          Soporta interpolación: {'{{name}}'}, {'{{age}}'}, etc.
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
          placeholder="Ej: Saludo inicial"
          className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-400/60"
        />
      </label>
    </div>
  );
};

export default InspectorMessage;
