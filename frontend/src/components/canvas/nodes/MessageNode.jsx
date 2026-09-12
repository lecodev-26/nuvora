import React, { memo } from 'react';
import NodeShell from '../NodeShell';

const MessageNode = ({ data, selected }) => {
  const text = data.config?.text;

  return (
    <NodeShell
      type="message"
      selected={selected}
      hasInput={true}
      hasOutput={true}
      footer={data.label}
    >
      {text ? (
        <div className="text-white/90 break-words">
          "{text.length > 60 ? text.slice(0, 60) + '…' : text}"
        </div>
      ) : (
        <div className="text-white/40 italic">Sin texto</div>
      )}
    </NodeShell>
  );
};

export default memo(MessageNode);
