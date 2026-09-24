import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { useBot } from '../context/BotContext';
import { botService } from '../services/api';
import Button from '../components/Button';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Spinner from '../components/ui/Spinner';
import NichoBadge from '../components/NichoBadge';

const LOGO_URL = '/logo.png';

/**
 * BotsList — Selector de bots del usuario.
 *
 * Es el nuevo /dashboard.
 *
 * Funcionalidad:
 *   - Listar bots del usuario
 *   - Crear bot (→ /onboarding)
 *   - Entrar a Creator Workspace (→ /bots/:botId)
 *   - Logout
 *
 * NO incluye (ahora vive en Creator Mode):
 *   - Analíticas, memorias, chat de prueba, publicación, canales, API keys
 */
const BotsList = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { bots, setBots, setSelectedBot } = useBot();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await botService.list();
        setBots(res.data || []);
      } catch (err) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : 'Error cargando tus bots');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [setBots]);

  const handleEnterBot = (bot) => {
    setSelectedBot(bot);
    navigate(`/bots/${bot.id}`);
  };

  return (
    <div className="min-h-screen bg-navy text-white">
      {/* Header */}
      <header className="border-b border-white/10 bg-navy/95 backdrop-blur sticky top-0 z-20">
        <div className="max-w-6xl mx-auto px-4 md:px-6 py-3 flex items-center justify-between">
          <Link to="/dashboard" className="flex items-center gap-2.5">
            <img src={LOGO_URL} alt="Nuvora" className="h-8 w-8 rounded-lg object-cover" />
            <span className="text-white font-semibold">Nuvora</span>
          </Link>

          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 text-sm">
              <div className="w-7 h-7 rounded-full bg-gradient-primary flex items-center justify-center text-xs font-bold">
                {user?.full_name?.[0] || 'U'}
              </div>
              <span className="text-white/70">{user?.full_name || user?.email}</span>
            </div>
            <Button variant="ghost" size="sm" onClick={logout}>
              Cerrar sesión
            </Button>
          </div>
        </div>
      </header>

      {/* Contenido */}
      <main className="max-w-6xl mx-auto px-4 md:px-6 py-8">
        {/* Título + CTA crear */}
        <div className="flex items-start justify-between gap-4 mb-6 flex-wrap">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-white">Mis bots</h1>
            <p className="text-white/50 text-sm mt-1">
              Elige un bot para trabajar en él, o crea uno nuevo.
            </p>
          </div>
          <Button
            variant="primary"
            size="md"
            onClick={() => navigate('/onboarding')}
          >
            + Crear bot
          </Button>
        </div>

        {/* Error */}
        {error && (
          <Card className="border-red-500/30 bg-red-500/5 mb-6">
            <p className="text-red-300 text-sm">⚠️ {error}</p>
          </Card>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Spinner />
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && bots.length === 0 && (
          <Card className="text-center py-12">
            <div className="text-5xl mb-3">🤖</div>
            <h2 className="text-white font-semibold text-lg mb-2">
              Todavía no tienes bots
            </h2>
            <p className="text-white/50 text-sm mb-5 max-w-md mx-auto">
              Crea tu primer bot para empezar a construir tu asistente.
            </p>
            <Button
              variant="primary"
              size="md"
              onClick={() => navigate('/onboarding')}
            >
              Crear mi primer bot
            </Button>
          </Card>
        )}

        {/* Lista de bots */}
        {!loading && bots.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {bots.map((bot) => (
              <Card
                key={bot.id}
                hover
                className="cursor-pointer flex flex-col"
                onClick={() => handleEnterBot(bot)}
              >
                <div className="flex items-start gap-3 mb-3">
                  <span className="text-3xl flex-shrink-0">🤖</span>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-white font-semibold truncate">
                      {bot.name || 'Sin nombre'}
                    </h3>
                    {bot.business_name && (
                      <p className="text-white/50 text-xs mt-0.5 truncate">
                        {bot.business_name}
                      </p>
                    )}
                  </div>
                </div>

                {/* Badges */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {bot.nicho_id && (
                    <NichoBadge nichoId={bot.nicho_id} />
                  )}
                  {bot.is_published ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      Publicado
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded-full bg-white/10 text-white/50 border border-white/10">
                      No publicado
                    </span>
                  )}
                </div>

                {/* Footer */}
                <div className="mt-auto pt-3 border-t border-white/5">
                  <span className="text-cyan-400 text-xs group-hover:text-cyan-300">
                    Abrir Creator Mode →
                  </span>
                </div>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default BotsList;
