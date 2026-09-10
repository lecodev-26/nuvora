import React from 'react';
import { getRealNichosList, getNicho } from '../data/nichos';

const NichoSelector = ({
  selected,
  onSelect,
  className = '',
  columns = 'grid-cols-2 md:grid-cols-3',
  showFromScratch = true,
}) => {
  const nichos = getRealNichosList();
  const desdeCero = getNicho('desde_cero');

  return (
    <div className={`grid ${columns} gap-3 ${className}`}>
      {/* Opción "Desde cero" (destacada, siempre primero) */}
      {showFromScratch && (
        <button
          type="button"
          onClick={() => onSelect('desde_cero')}
          className={`relative flex flex-col items-center justify-center gap-2 p-4 rounded-2xl border-2 transition-all duration-200 text-center group ${
            selected === 'desde_cero'
              ? 'border-cyan-500/60 bg-cyan-500/10 shadow-glow'
              : 'border-dashed border-white/20 bg-white/[0.03] hover:border-cyan-500/40 hover:bg-cyan-500/5'
          }`}
        >
          {selected === 'desde_cero' && (
            <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-gradient-primary flex items-center justify-center text-xs text-white font-bold">
              ✓
            </div>
          )}
          <span className="text-3xl">{desdeCero.icon}</span>
          <span
            className={`text-sm font-semibold transition-colors ${
              selected === 'desde_cero' ? 'text-cyan-300' : 'text-white/70 group-hover:text-cyan-300'
            }`}
          >
            {desdeCero.name}
          </span>
          <span className="text-[10px] text-white/40 leading-tight line-clamp-2">
            {desdeCero.description}
          </span>
        </button>
      )}

      {/* Nichos con plantilla */}
      {nichos.map((nicho) => {
        const isSelected = selected === nicho.id;

        return (
          <button
            key={nicho.id}
            type="button"
            onClick={() => onSelect(nicho.id)}
            className={`relative flex flex-col items-center justify-center gap-2 p-4 rounded-2xl border transition-all duration-200 text-center group ${
              isSelected
                ? 'border-violet-500/60 bg-violet-500/10 shadow-glow'
                : 'border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10'
            }`}
          >
            {isSelected && (
              <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-gradient-primary flex items-center justify-center text-xs text-white font-bold">
                ✓
              </div>
            )}

            <span className="text-3xl">{nicho.icon}</span>

            <span
              className={`text-sm font-semibold transition-colors ${
                isSelected ? 'text-white' : 'text-white/70 group-hover:text-white'
              }`}
            >
              {nicho.name}
            </span>

            <span className="text-[10px] text-white/40 leading-tight line-clamp-2">
              {nicho.description}
            </span>
          </button>
        );
      })}
    </div>
  );
};

export default NichoSelector;
