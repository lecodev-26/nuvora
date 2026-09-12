import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import NodeShell from '../NodeShell';

const HANDLE_CLASS =
  '!w-3 !h-3 !bg-white !border-2 !border-slate-800 !rounded-full hover:!scale-125 transition-transform';

const ConditionNode = ({ data, selected }) => {
  const condition = data.config?.condition;

  return (
    <div className="relative">
      <NodeShell
        type="condition"
        selected={selected}
        hasInput={true}
        hasOutput={false}
        footer={data.label}
      >
        {condition ? (
          <div className="text-white/90 font-mono text-xs break-words">
            if ({condition.length > 40 ? condition.slice(0, 40) + '…' : condition})
          </div>
        ) : (
          <div className="text-white/40 italic">Sin condición</div>
        )}
      </NodeShell>

      {/* Dos puertos de salida: true (izq) y false (der) */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="true"
        className={`${HANDLE_CLASS} !bg-emerald-400`}
        style={{ left: '30%' }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="false"
        className={`${HANDLE_CLASS} !bg-red-400`}
        style={{ left: '70%' }}
      />

      {/* Etiquetas true/false */}
      <div className="absolute -bottom-5 left-0 right-0 flex justify-between px-6 text-[10px]">
        <span className="text-emerald-400 font-bold">true</span>
        <span className="text-red-400 font-bold">false</span>
      </div>
    </div>
  );
};

export default memo(ConditionNode);
