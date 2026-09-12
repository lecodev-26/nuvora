import React, { memo } from 'react';
import NodeShell from '../NodeShell';

const EndNode = ({ data, selected }) => {
  return (
    <NodeShell type="end" selected={selected} hasInput={true} hasOutput={false}>
      <div className="text-white/70 italic">
        {data.label || 'Fin del workflow'}
      </div>
    </NodeShell>
  );
};

export default memo(EndNode);
