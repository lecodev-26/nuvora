import React, { useState } from 'react';
import { Outlet, useParams, useNavigate } from 'react-router-dom';
import CreatorSidebar from './CreatorSidebar';
import CreatorHeader from './CreatorHeader';

/**
 * CreatorLayout — Shell del Creator Workspace.
 *
 * Estructura:
 *   ┌──────────────────────────────────────────┐
 *   │ CreatorHeader (sticky)                    │
 *   ├─────────────┬────────────────────────────┤
 *   │ Sidebar     │ Outlet (página activa)     │
 *   │ (md+)       │                            │
 *   └─────────────┴────────────────────────────┘
 *
 * Comportamiento responsive:
 *   - Desktop (md+): sidebar fijo a la izquierda
 *   - Móvil: sidebar oculto por defecto, se abre como drawer
 *
 * Props:
 *   - botName: opcional (para mostrar nombre en header/sidebar)
 *   - botStatus: opcional ("ready" | "building" | "error")
 *
 * Uso:
 *   <Route path="/bots/:botId" element={<CreatorLayout />}>
 *     <Route index element={<CreatorOverview />} />
 *     <Route path="config" element={<CreatorConfig />} />
 *     ...
 *   </Route>
 */
const CreatorLayout = ({
  botName = 'Mi Bot',
  botStatus = 'building',
}) => {
  const { botId } = useParams();
  const navigate = useNavigate();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const closeDrawer = () => setDrawerOpen(false);

  return (
    <div className="min-h-screen bg-navy text-white flex flex-col">
      {/* Header sticky */}
      <CreatorHeader
        botName={botName}
        botStatus={botStatus}
        onMenuClick={() => setDrawerOpen(true)}
      />

      {/* Contenedor principal */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar desktop */}
        <div className="hidden md:flex flex-shrink-0">
          <CreatorSidebar
            botId={botId}
            botName={botName}
            botStatus={botStatus}
          />
        </div>

        {/* Main */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-6xl mx-auto px-4 md:px-6 py-6">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Drawer móvil */}
      {drawerOpen && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 md:hidden"
          onClick={closeDrawer}
        >
          <div
            className="absolute top-0 left-0 h-full w-72 bg-navy border-r border-white/10"
            onClick={(e) => e.stopPropagation()}
          >
            <CreatorSidebar
              botId={botId}
              botName={botName}
              botStatus={botStatus}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default CreatorLayout;
