import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';

/**
 * NodeShell — Wrapper común para todos los nodos del Workflow Builder.
 *
 * Responsabilidades:
 *  - Estilo (colores, bordes, glow por tipo)
 *  - Header con icono + label
 *  - Estado `selected`
 *  - Puertos de entrada/salida configurables
 *
 * Cada nodo específico (StartNode, MessageNode, etc.) usa este shell
 * y renderiza su propio contenido como children.
 */

export const TYPE_STYLES = {
  start: {
    label: 'START',
    icon: '▶',
    accent: 'text-emerald-300',
    border: 'border-emerald-400/60',
    bg: 'bg-emerald-500/10',
    glow: 'shadow-[0_0_20px_rgba(16,185,129,0.25)]',
  },
  message: {
    label: 'MESSAGE',
    icon: '💬',
    accent: 'text-cyan-300',
    border: 'border-cyan-400/60',
    bg: 'bg-cyan-500/10',
    glow: 'shadow-[0_0_20px_rgba(0,198,255,0.25)]',
  },
  question: {
    label: 'QUESTION',
    icon: '❓',
    accent: 'text-violet-300',
    border: 'border-violet-400/60',
    bg: 'bg-violet-500/10',
    glow: 'shadow-[0_0_20px_rgba(123,92,255,0.25)]',
  },
  condition: {
    label: 'CONDITION',
    icon: '◆',
    accent: 'text-amber-300',
    border: 'border-amber-400/60',
    bg: 'bg-amber-500/10',
    glow: 'shadow-[0_0_20px_rgba(245,158,11,0.25)]',
  },
  variable: {
    label: 'VARIABLE',
    icon: '𝑥',
    accent: 'text-fuchsia-300',
    border: 'border-fuchsia-400/60',
    bg: 'bg-fuchsia-500/10',
    glow: 'shadow-[0_0_20px_rgba(217,70,239,0.25)]',
  },
  response: {
    label: 'RESPONSE',
    icon: '↩',
    accent: 'text-blue-300',
    border: 'border-blue-400/60',
    bg: 'bg-blue-500/10',
    glow: 'shadow-[0_0_20px_rgba(59,130,246,0.25)]',
  },
  end: {
    label: 'END',
    icon: '■',
    accent: 'text-red-300',
    border: 'border-red-400/60',
    bg: 'bg-red-500/10',
    glow: 'shadow-[0_0_20px_rgba(239,68,68,0.25)]',
  },
};

export const FALLBACK_STYLE = {
  label: 'UNKNOWN',
  icon: '?',
  accent: 'text-slate-300',
  border: 'border-slate-400/60',
  bg: 'bg-slate-500/10',
  glow: '',
};

const HANDLE_CLASS =
  '!w-3 !h-3 !bg-white !border-2 !border-slate-800 !rounded-full hover:!scale-125 transition-transform';

const NodeShell = ({
  type,
  children,
  selected = false,
  hasError = false,
  hasInput = true,
  hasOutput = true,
  inputId,
  outputId,
  footer,
}) => {
  const style = TYPE_STYLES[type] || FALLBACK_STYLE;

  return (
    <div
      className={`
        min-w-[200px] max-w-[260px] rounded-xl border-2 backdrop-blur-sm
        transition-all duration-200
        ${style.bg}
        ${hasError ? '!border-red-500 !shadow-[0_0_24px_rgba(239,68,68,0.5)]' : style.border}
        ${selected ? `ring-2 ring-white/70 ${style.glow} scale-[1.02]` : ''}
      `}
    >
      {/* Puerto de entrada */}
      {hasInput && (
        <Handle
          type="target"
          position={Position.Top}
          id={inputId}
          className={HANDLE_CLASS}
        />
      )}

      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-white/10">
        <span className={`text-base ${style.accent}`}>{style.icon}</span>
        <span className={`text-[10px] font-bold tracking-widest ${style.accent}`}>
          {style.label}
        </span>
        {hasError && (
          <span className="ml-auto text-red-400 text-xs" title="Este nodo tiene errores">
            ⚠️
          </span>
        )}
      </div>

      {/* Body */}
      <div className="px-3 py-2 text-white/90 text-sm">
        {children}
      </div>

      {/* Footer */}
      {footer && (
        <div className="px-3 pb-2 text-xs text-white/50">
          {footer}
        </div>
      )}

      {/* Puerto de salida */}
      {hasOutput && (
        <Handle
          type="source"
          position={Position.Bottom}
          id={outputId}
          className={HANDLE_CLASS}
        />
      )}
    </div>
  );
};

export default memo(NodeShell);
