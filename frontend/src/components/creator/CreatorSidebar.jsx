import React from 'react';
import { NavLink, Link } from 'react-router-dom';

/**
 * CreatorSidebar — Navegación del Creator Workspace.
 *
 * Agrupa las secciones en 3 bloques mentales:
 *   - CREAR:  Configuración, Conocimiento, Flujos
 *   - PROBAR: Training, Tester
 *   - LANZAR: Publicación, Canales
 *
 * Además, arriba: Inicio (Overview).
 *
 * Props:
 *   - botId: number
 *   - botName: string (para mostrar en la cabecera del sidebar)
 *   - botStatus: "ready" | "building" | "error" (opcional)
 */

const SECTION_GROUPS = [
  {
    label: null,
    items: [
      { path: '', icon: '🏠', label: 'Inicio', end: true },
    ],
  },
  {
    label: 'CREAR',
    items: [
      { path: 'config', icon: '⚙️', label: 'Configuración' },
      { path: 'knowledge', icon: '📚', label: 'Conocimiento' },
      { path: 'workflows', icon: '🔀', label: 'Flujos' },
    ],
  },
  {
    label: 'PROBAR',
    items: [
      { path: 'training', icon: '🎓', label: 'Training' },
      { path: 'tester', icon: '🧪', label: 'Tester' },
    ],
  },
  {
    label: 'LANZAR',
    items: [
      { path: 'publication', icon: '🌐', label: 'Publicación' },
      { path: 'channels', icon: '📡', label: 'Canales' },
    ],
  },
];

const CreatorSidebar = ({ botId, botName = 'Mi Bot', botStatus = 'building' }) => {
  const statusConfig = {
    ready: { label: 'Listo', className: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25' },
    building: { label: 'En construcción', className: 'bg-amber-500/15 text-amber-300 border-amber-500/25' },
    error: { label: 'Con errores', className: 'bg-red-500/15 text-red-300 border-red-500/25' },
  };
  const status = statusConfig[botStatus] || statusConfig.building;

  return (
    <aside className="flex flex-col h-full w-64 bg-white/[0.02] border-r border-white/10">
      {/* Cabecera del sidebar */}
      <div className="p-4 border-b border-white/5">
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-1.5 text-white/50 hover:text-white text-xs mb-3 transition"
        >
          <span>←</span>
          <span>Mis bots</span>
        </Link>
        <div className="flex items-center gap-2">
          <span className="text-2xl">🤖</span>
          <div className="min-w-0 flex-1">
            <p className="text-white font-semibold text-sm truncate">{botName}</p>
            <span className={`inline-flex items-center px-2 py-0.5 mt-1 text-[10px] font-medium rounded-full border ${status.className}`}>
              {status.label}
            </span>
          </div>
        </div>
      </div>

      {/* Navegación */}
      <nav className="flex-1 overflow-y-auto p-3">
        {SECTION_GROUPS.map((group, gi) => (
          <div key={gi} className={gi > 0 ? 'mt-4' : ''}>
            {group.label && (
              <p className="px-3 py-1 text-[10px] font-semibold tracking-wider text-white/40 uppercase">
                {group.label}
              </p>
            )}
            <div className="space-y-0.5 mt-1">
              {group.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={`/bots/${botId}${item.path ? '/' + item.path : ''}`}
                  end={item.end}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                      isActive
                        ? 'bg-gradient-primary/10 text-white border border-cyan-500/20'
                        : 'text-white/60 hover:text-white hover:bg-white/5'
                    }`
                  }
                >
                  <span className="text-base">{item.icon}</span>
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-white/5">
        <Link
          to="/dashboard"
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-white/40 hover:text-white/70 hover:bg-white/5 transition"
        >
          <span>🏠</span>
          <span>Volver a Mis bots</span>
        </Link>
      </div>
    </aside>
  );
};

export default CreatorSidebar;
