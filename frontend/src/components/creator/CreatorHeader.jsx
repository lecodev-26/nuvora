import React from 'react';
import { Link } from 'react-router-dom';

/**
 * CreatorHeader — Cabecera del Creator Workspace.
 *
 * Props:
 *   - botName: string (nombre del bot)
 *   - botStatus: "ready" | "building" | "error" (opcional)
 *   - onMenuClick: () => void (para abrir el drawer en móvil)
 *   - children: ReactNode (acciones opcionales a la derecha)
 *
 * Muestra:
 *   - Botón "← Mis bots"
 *   - Nombre del bot
 *   - Estado (badge)
 *   - Botón hamburguesa (móvil)
 */
const CreatorHeader = ({
  botName = 'Mi Bot',
  botStatus = 'building',
  onMenuClick,
  children,
}) => {
  const statusConfig = {
    ready: {
      label: 'Listo',
      className: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25',
      dotClass: 'bg-emerald-400',
    },
    building: {
      label: 'En construcción',
      className: 'bg-amber-500/15 text-amber-300 border-amber-500/25',
      dotClass: 'bg-amber-400',
    },
    error: {
      label: 'Con errores',
      className: 'bg-red-500/15 text-red-300 border-red-500/25',
      dotClass: 'bg-red-400',
    },
  };

  const status = statusConfig[botStatus] || statusConfig.building;

  return (
    <header className="sticky top-0 z-30 bg-navy/95 backdrop-blur border-b border-white/10">
      <div className="flex items-center gap-3 px-4 md:px-6 py-3">
        {/* Botón hamburguesa (solo móvil) */}
        {onMenuClick && (
          <button
            type="button"
            onClick={onMenuClick}
            className="md:hidden text-white/70 hover:text-white p-2 -ml-2 rounded-lg hover:bg-white/5 transition"
            aria-label="Abrir menú"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
        )}

        {/* Breadcrumb: ← Mis bots */}
        <Link
          to="/dashboard"
          className="hidden md:inline-flex items-center gap-1.5 text-white/50 hover:text-white text-sm transition"
        >
          <span>←</span>
          <span>Mis bots</span>
        </Link>

        {/* Separador desktop */}
        <span className="hidden md:inline text-white/20">/</span>

        {/* Nombre del bot */}
        <h1 className="text-white font-semibold text-sm md:text-base truncate flex-1">
          {botName}
        </h1>

        {/* Badge de estado */}
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-medium rounded-full border ${status.className}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${status.dotClass}`} />
          {status.label}
        </span>

        {/* Acciones adicionales */}
        {children && <div className="flex items-center gap-2">{children}</div>}
      </div>
    </header>
  );
};

export default CreatorHeader;
