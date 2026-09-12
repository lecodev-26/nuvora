import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';

/**
 * CustomNode — Nodo visual genérico para el Workflow Builder.
 *
 * Por ahora hay UN solo componente que se adapta según `data.type`.
 * En 14.6.5 se reemplazará por 7 nodos específicos.
 *
 * Props (inyectadas por React Flow):
 *  - data: { type, node_id, name, config, label, preview }
 *  - selected: boolean
 */

const TYPE_STYLES = {
  start: {
    label: 'START',
    icon: '▶',
    bg: 'bg-emerald-500/20',
    border: 'border-emerald-400',
    text: 'text-emerald-300',
    glow: 'shadow-[0_0_20px_rgba(16,185,129,0.3)]',
  },
  message: {
    label: 'MESSAGE',
    icon: '💬',
    bg: 'bg-cyan-500/20',
    border: 'border-cyan-400',
    text: 'text-cyan-300',
    glow: 'shadow-[0_0_20px_rgba(0,198,255,0.3)]',
  },
  question: {
    label: 'QUESTION',
    icon: '❓',
    bg: 'bg-violet-500/20',
    border: 'border-violet-400',
    text: 'text-violet-300',
    glow: 'shadow-[0_0_20px_rgba(123,92,255,0.3)]',
  },
  condition: {
    label: 'CONDITION',
    icon: '◆',
    bg: 'bg-amber-500/20',
    border: 'border-amber-400',
    text: 'text-amber-300',
    glow: 'shadow-[0_0_20px_rgba(245,158,11,0.3)]',
  },
  variable: {
    label: 'VARIABLE',
    icon: '𝑥',
    bg: 'bg-fuchsia-500/20',
    border: 'border-fuchsia-400',
    text: 'text-fuchsia-300',
    glow: 'shadow-[0_0_20px_rgba(217,70,239,0.3)]',
  },
  response: {
    label: 'RESPONSE',
    icon: '↩',
    bg: 'bg-blue-500/20',
    border: 'border-blue-400',
    text: 'text-blue-300',
    glow: 'shadow-[0_0_20px_rgba(59,130,246,0.3)]',
  },
  end: {
    label: 'END',
    icon: '■',
    bg: 'bg-red-500/20',
    border: 'border-red-400',
    text: 'text-red-300',
    glow: 'shadow-[0_0_20px_rgba(239,68,68,0.3)]',
  },
};

const FALLBACK_STYLE = {
  label: 'UNKNOWN',
  icon: '?',
  bg: 'bg-slate-500/20',
  border: 'border-slate-400',
  text: 'text-slate-300',
  glow: 'shadow-[0_0_20px_rgba(100,116,139,0.3)]',
};

const CustomNode = ({ data, selected }) => {
  const style = TYPE_STYLES[data.type] || FALLBACK_STYLE;

  return (
    <div
      className={`
        min-w-[180px] max-w-[240px] rounded-xl border-2 px-4 py-3
        backdrop-blur-sm transition-all duration-200
        ${style.bg} ${style.border} ${style.glow}
        ${selected ? 'ring-2 ring-white/60 scale-[1.02]' : ''}
      `}
    >
      {/* Puerto de entrada (no START) */}
      {data.type !== 'start' && (
        <Handle
          type="target"
          position={Position.Top}
          className="!w-3 !h-3 !bg-white/80 !border-2 !border-slate-700"
        />
      )}

      {/* Cabecera */}
      <div className="flex items-center gap-2 mb-1">
        <span className={`text-lg ${style.text}`}>{style.icon}</span>
        <span className={`text-xs font-bold tracking-wider ${style.text}`}>
          {style.label}
        </span>
      </div>

      {/* Cuerpo */}
      <div className="text-white/90 text-sm">
        {data.label || <span className="text-white/40 italic">Sin nombre</span>}
      </div>

      {/* Preview de config */}
      {data.preview && (
        <div className="mt-2 text-xs text-white/60 truncate">
          {data.preview}
        </div>
      )}

      {/* Puerto de salida (no END) */}
      {data.type !== 'end' && (
        <Handle
          type="source"
          position={Position.Bottom}
          className="!w-3 !h-3 !bg-white/80 !border-2 !border-slate-700"
        />
      )}

      {/* Puerto extra para CONDITION (true/false) */}
      {data.type === 'condition' && (
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            id="true"
            style={{ left: '30%' }}
            className="!w-3 !h-3 !bg-emerald-400 !border-2 !border-slate-700"
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="false"
            style={{ left: '70%' }}
            className="!w-3 !h-3 !bg-red-400 !border-2 !border-slate-700"
          />
        </>
      )}
    </div>
  );
};

export default memo(CustomNode);
