import React from 'react';
import { getNicho } from '../data/nichos';

const NichoBadge = ({ nichoId, className = '', showName = true }) => {
  const nicho = getNicho(nichoId);

  if (!nicho) return null;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-full bg-violet-500/15 text-violet-300 border border-violet-500/25 ${className}`}
    >
      <span>{nicho.icon}</span>
      {showName && <span>{nicho.name}</span>}
    </span>
  );
};

export default NichoBadge;
