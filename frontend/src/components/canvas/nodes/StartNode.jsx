import React, { memo } from 'react';
import NodeShell from '../NodeShell';

const StartNode = ({ data, selected }) => {
  return (
    <NodeShell type="start" selected={selected} hasInput={false} hasOutput={true}>
      <div className="text-white/70 italic">
        {data.label || 'Inicio del workflow'}
      </div>
    </NodeShell>
  );
};

export default memo(StartNode);
