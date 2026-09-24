import React from 'react';
import Card from '../Card';

/**
 * BotOverviewCard — Card principal del bot en Creator Overview.
 *
 * Props:
 *   - bot: { id, name, description, nicho_id, business_name }
 *   - status: { ready, next_step } (opcional)
 *   - nichoName: nombre humano del nicho (opcional)
 */
const BotOverviewCard = ({ bot, status, nichoName }) => {
  if (!bot) return null;

  const isReady = status?.ready === true;

  return (
    <Card className="relative overflow-hidden">
      {/* Borde superior con gradiente sutil */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent" />

      <div className="flex items-start gap-4">
        <div className="text-4xl flex-shrink-0">🤖</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div className="min-w-0 flex-1">
              <h1 className="text-xl md:text-2xl font-bold text-white truncate">
                {bot.name || 'Sin nombre'}
              </h1>
              {bot.description && (
                <p className="text-white/60 text-sm mt-1 line-clamp-2">
                  {bot.description}
                </p>
              )}
            </div>
            {/* Badge de estado */}
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 text-[11px] font-medium rounded-full border flex-shrink-0 ${
                isReady
                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25'
                  : 'bg-amber-500/15 text-amber-300 border-amber-500/25'
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${isReady ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              {isReady ? 'Listo' : 'En construcción'}
            </span>
          </div>

          {/* Metadata: nicho + negocio */}
          <div className="flex flex-wrap items-center gap-3 mt-3 text-xs text-white/50">
            {nichoName && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300">
                🏷️ {nichoName}
              </span>
            )}
            {bot.business_name && (
              <span className="inline-flex items-center gap-1.5">
                🏢 {bot.business_name}
              </span>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};

export default BotOverviewCard;
