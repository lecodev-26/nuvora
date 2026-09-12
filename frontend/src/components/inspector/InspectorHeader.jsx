import React from 'react';
import { TYPE_STYLES, FALLBACK_STYLE } from '../canvas/NodeShell';

/**
 * InspectorHeader — cabecera común del panel inspector.
 * Muestra: icono + tipo + node_id + botón borrar.
 */
const InspectorHeader = ({ node, onDelete }) => {
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

      {onDelete && (
        <button
          type="button"
          onClick={onDelete}
          className="text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded p-1 transition-colors shrink-0"
          title="Eliminar nodo"
        >
          🗑
        </button>
      )}
    </div>
  );
};

export default InspectorHeader;
