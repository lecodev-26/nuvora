import React from 'react';

/**
 * PublicFooter — Pie con "Powered by Nuvora".
 * Solo se muestra si show_branding=True en la config.
 */

const PublicFooter = () => {
  return (
    <div className="px-4 py-2 border-t border-white/5 flex items-center justify-center">
      <a
        href="/"
        target="_blank"
        rel="noopener noreferrer"
        className="text-white/40 hover:text-white/60 text-xs transition-colors flex items-center gap-1"
      >
        ✨ Powered by <span className="font-semibold">Nuvora</span>
      </a>
    </div>
  );
};

export default PublicFooter;
