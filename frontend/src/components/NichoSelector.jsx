import React from 'react';
import { getNichosList } from '../data/nichos';

const NichoSelector = ({
  selected,
  onSelect,
  className = '',
  columns = 'grid-cols-2 md:grid-cols-3',
}) => {
  const nichos = getNichosList();

  return (
    <div className={`grid ${columns} gap-3 ${className}`}>
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
            {/* Check de seleccionado */}
            {isSelected && (
              <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-gradient-primary flex items-center justify-center text-xs text-white font-bold">
                ✓
              </div>
            )}

            {/* Icono */}
            <span className="text-3xl">{nicho.icon}</span>

            {/* Nombre */}
            <span
              className={`text-sm font-semibold transition-colors ${
                isSelected ? 'text-white' : 'text-white/70 group-hover:text-white'
              }`}
            >
              {nicho.name}
            </span>

            {/* Descripción */}
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
