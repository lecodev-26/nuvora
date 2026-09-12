import React, { useState } from 'react';
import { TYPE_STYLES } from '../canvas/NodeShell';

/**
 * NodePalette — Paleta flotante para añadir nodos.
 *
 * Props:
 *  - onAdd: (type) => void      — se llama al click en un tipo
 *
 * Responsabilidad:
 *  - Mostrar los 7 tipos con su icono/label/color
 *  - Emitir el evento "add" con el tipo elegido
 *
 * La generación del node_id y la posición se hace en el padre
 * (WorkflowBuilder) para centralizar las reglas.
 */

const TYPES_ORDER = [
  'start',
  'message',
  'question',
  'condition',
  'variable',
  'response',
  'end',
];

const NodePalette = ({ onAdd }) => {
  const [open, setOpen] = useState(false);

  return (
    <div className="absolute bottom-6 left-6 z-10">
      {/* Botón toggle */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="mb-2 bg-gradient-to-r from-cyan-500 via-violet-500 to-magenta-500 text-white font-semibold rounded-xl px-4 py-2 shadow-glow hover:opacity-90 active:scale-[0.98] transition"
      >
        {open ? '✕ Cerrar paleta' : '＋ Añadir nodo'}
      </button>

      {/* Paleta */}
      {open && (
        <div className="bg-navy/95 backdrop-blur-md border border-white/10 rounded-2xl p-3 shadow-card w-64">
          <div className="text-white/60 text-xs uppercase tracking-wider mb-2 px-1">
            Tipo de nodo
          </div>

          <div className="grid grid-cols-2 gap-2">
            {TYPES_ORDER.map((type) => {
              const style = TYPE_STYLES[type];
              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => {
                    onAdd(type);
                    // Mantener abierto por si quiere añadir varios
                  }}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${style.border} ${style.bg} hover:scale-[1.02] active:scale-[0.98] transition-all`}
                >
                  <span className={`text-lg ${style.accent}`}>{style.icon}</span>
                  <span className={`text-xs font-bold tracking-wide ${style.accent}`}>
                    {style.label}
                  </span>
                </button>
              );
            })}
          </div>

          <div className="mt-3 text-[10px] text-white/40 px-1 leading-relaxed">
            El ID se genera automáticamente. Puedes editarlo en el panel
            derecho tras seleccionar el nodo.
          </div>
        </div>
      )}
    </div>
  );
};

export default NodePalette;
