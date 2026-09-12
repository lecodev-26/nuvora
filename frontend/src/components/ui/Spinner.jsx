import React from 'react';

/**
 * Spinner — loader consistente en toda la app.
 *
 * Props:
 *  - size: 'sm' | 'md' | 'lg'
 *  - label: string opcional a mostrar debajo
 *  - fullScreen: si true, ocupa toda la pantalla centrado
 */

const SIZES = {
  sm: 'w-4 h-4 border-2',
  md: 'w-8 h-8 border-2',
  lg: 'w-12 h-12 border-3',
};

const Spinner = ({ size = 'md', label, fullScreen = false }) => {
  const spinner = (
    <div className="flex flex-col items-center gap-3">
      <div
        className={`${SIZES[size]} rounded-full border-white/20 border-t-cyan-400 animate-spin`}
      />
      {label && <div className="text-white/50 text-sm">{label}</div>}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="min-h-screen bg-navy flex items-center justify-center">
        {spinner}
      </div>
    );
  }

  return spinner;
};

export default Spinner;
