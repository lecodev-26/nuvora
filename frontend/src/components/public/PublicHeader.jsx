import React from 'react';

/**
 * PublicHeader — Cabecera de la página pública del bot.
 *
 * Props:
 *   - name: nombre del bot
 *   - businessName: nombre del negocio (opcional)
 *   - avatarUrl: URL del avatar (opcional)
 *   - primaryColor: color de acento (opcional, default gradient Nuvora)
 */

const PublicHeader = ({ name, businessName, avatarUrl, primaryColor }) => {
  // Si hay color custom, usarlo como fondo del header
  const headerStyle = primaryColor
    ? { background: `linear-gradient(135deg, ${primaryColor}, ${primaryColor}dd)` }
    : { background: 'linear-gradient(135deg, #00C6FF, #7B5CFF, #FF4ECD)' };

  const displayName = businessName || name || 'Asistente Nuvora';

  return (
    <div
      className="flex items-center gap-3 px-5 py-4 border-b border-white/10"
      style={headerStyle}
    >
      {avatarUrl ? (
        <img
          src={avatarUrl}
          alt={displayName}
          className="w-10 h-10 rounded-xl object-cover border-2 border-white/20"
          onError={(e) => { e.target.style.display = 'none'; }}
        />
      ) : (
        <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center text-white text-lg font-bold">
          {displayName[0]?.toUpperCase() || 'N'}
        </div>
      )}

      <div className="flex-1 min-w-0">
        <div className="text-white font-semibold text-sm truncate">
          {displayName}
        </div>
        <div className="flex items-center gap-1.5 text-xs text-white/80">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          En línea
        </div>
      </div>
    </div>
  );
};

export default PublicHeader;
