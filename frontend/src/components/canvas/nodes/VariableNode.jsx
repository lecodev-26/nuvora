import React, { memo } from 'react';
import NodeShell from '../NodeShell';

const VariableNode = ({ data, selected }) => {
  const name = data.config?.name;
  const value = data.config?.value;

  return (
    <NodeShell
      type="variable"
      selected={selected}
      hasInput={true}
      hasOutput={true}
      footer={data.label}
    >
      {name ? (
        <div className="font-mono text-xs">
          <span className="text-fuchsia-300">{name}</span>
          <span className="text-white/50"> = </span>
          <span className="text-white/90">
            "{value?.length > 30 ? value.slice(0, 30) + '…' : value || ''}"
          </span>
        </div>
      ) : (
        <div className="text-white/40 italic">Sin asignación</div>
      )}
    </NodeShell>
  );
};

export default memo(VariableNode);
