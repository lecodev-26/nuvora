import React from 'react';
import { TYPE_STYLES, FALLBACK_STYLE } from '../canvas/NodeShell';

/**
 * InspectorHeader — cabecera común del panel inspector.
 * Muestra: icono + tipo + node_id + acciones (duplicar, borrar).
 */
const InspectorHeader = ({ node, onDelete, onDuplicate }) => {
  const style = TYPE_STYLES[node.type] || FALLBACK_STYLE;

  return (
    <div className="flex items-start justify-between gap-3 pb-3 mb-4 border-b border-white/10">
      <div className="flex items-start gap-3 min-w-0">
        <span className={`text-2xl ${style.accent} leading-none mt-0.5`}>
          {style.icon}
        </span>
        <div className="min-w-0">
          <div className={`text-xs font-bold tracking-widest ${style.accent}`}>
            {style.label}
          </div>
          <div className="text-white/50 text-xs font-mono truncate">
            {node.node_id}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-1 shrink-0">
        {onDuplicate && (
          <button
            type="button"
            onClick={onDuplicate}
            className="text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10 rounded p-1 transition-colors"
            title="Duplicar nodo"
          >
            ⧉
          </button>
        )}
        {onDelete && (
          <button
            type="button"
            onClick={onDelete}
            className="text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded p-1 transition-colors"
            title="Eliminar nodo"
          >
            🗑
          </button>
        )}
      </div>
    </div>
  );
};

export default InspectorHeader;
