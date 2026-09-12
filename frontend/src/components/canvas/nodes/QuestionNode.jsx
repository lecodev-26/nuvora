import React, { memo } from 'react';
import NodeShell from '../NodeShell';

const QuestionNode = ({ data, selected }) => {
  const text = data.config?.text;
  const variable = data.config?.variable;

  return (
    <NodeShell
      type="question"
      selected={selected}
      hasInput={true}
      hasOutput={true}
      footer={variable ? `→ ${variable}` : null}
    >
      {text ? (
        <div className="text-white/90 break-words">
          {text.length > 60 ? text.slice(0, 60) + '…' : text}
        </div>
      ) : (
        <div className="text-white/40 italic">Sin pregunta</div>
      )}
    </NodeShell>
  );
};

export default memo(QuestionNode);
