import React from 'react';

const InspectorQuestion = ({ node, onUpdate }) => {
  const text = node.config?.text || '';
  const variable = node.config?.variable || '';

  return (
    <div className="space-y-3">
      <label className="block">
        <span className="text-white/60 text-xs uppercase tracking-wider">
          Pregunta
        </span>
        <textarea
          value={text}
          onChange={(e) => onUpdate({ config: { ...node.config, text: e.target.value } })}
          rows={4}
          placeholder="Ej: ¿Cuál es tu nombre?"
          className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-400/60 resize-none"
        />
      </label>

      <label className="block">
        <span className="text-white/60 text-xs uppercase tracking-wider">
          Variable (donde se guarda la respuesta)
        </span>
        <input
          type="text"
          value={variable}
          onChange={(e) => onUpdate({ config: { ...node.config, variable: e.target.value } })}
          placeholder="Ej: name"
          className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white font-mono text-sm focus:outline-none focus:border-violet-400/60"
        />
        <span className="text-white/40 text-xs">
          La respuesta del usuario se guardará en esta variable.
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
          placeholder="Ej: Preguntar nombre"
          className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-400/60"
        />
      </label>
    </div>
  );
};

export default InspectorQuestion;
