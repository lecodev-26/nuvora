import React from 'react';
import TelegramPanel from './TelegramPanel';

/**
 * ChannelsPanel — Modal con la visión completa de canales del bot.
 *
 * Props:
 *   - open: boolean
 *   - bot: { id, name, is_published, public_slug, public_id } | null
 *   - onClose: () => void
 *
 * Muestra todos los canales disponibles:
 *   - Web (publicación universal)
 *   - API (Nuvora API v1)
 *   - Telegram (14.11)
 *   - WhatsApp, Discord (futuros, placeholder)
 */

const ChannelsPanel = ({ open, bot, onClose }) => {
  if (!open) return null;

  const isPublished = bot?.is_published;
  const publicUrl = bot?.public_slug
    ? `/b/${bot.public_slug}`
    : (bot?.public_id ? `/b/${bot.public_id}` : null);

  const handleOpenPublic = () => {
    if (publicUrl) {
      window.open(publicUrl, '_blank');
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-navy border border-white/10 rounded-2xl shadow-card w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 flex-shrink-0">
          <div>
            <h2 className="text-white text-lg font-semibold">
              📡 Canales
            </h2>
            <p className="text-white/50 text-xs mt-0.5">
              {bot?.name ? `Bot: ${bot.name}` : 'Sin bot seleccionado'}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-white/50 hover:text-white text-xl transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4 overflow-y-auto flex-1">
          {!bot ? (
            <p className="text-white/50 text-center py-8">
              Selecciona un bot primero.
            </p>
          ) : (
            <>
              {/* WEB */}
              <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                <div className="flex items-start gap-4">
                  <div className="text-3xl">🌐</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-white font-semibold">Web</p>
                      {isPublished ? (
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
                    <p className="text-white/60 text-xs mt-1">
                      Página pública y widget embebible.
                    </p>
                  </div>
                  {isPublished && publicUrl && (
                    <button
                      onClick={handleOpenPublic}
                      className="text-cyan-400 hover:text-cyan-300 text-xs underline whitespace-nowrap"
                    >
                      Ver publicado →
                    </button>
                  )}
                </div>
              </div>

              {/* API */}
              <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                <div className="flex items-start gap-4">
                  <div className="text-3xl">🔌</div>
                  <div className="flex-1">
                    <p className="text-white font-semibold">API</p>
                    <p className="text-white/60 text-xs mt-1">
                      Nuvora API v1 para integraciones externas.
                      Las claves se gestionan desde <strong>🔑 API Keys</strong>.
                    </p>
                  </div>
                </div>
              </div>

              {/* TELEGRAM (componente completo) */}
              <div>
                <div className="flex items-center gap-2 mb-2 px-1">
                  <span className="text-white font-medium text-sm">🤖 Telegram</span>
                </div>
                <TelegramPanel botId={bot.id} />
              </div>

              {/* WHATSAPP / DISCORD (placeholders) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-white/[0.02] border border-dashed border-white/10 rounded-2xl p-4 opacity-50">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl grayscale">💬</div>
                    <div>
                      <p className="text-white/70 text-sm font-medium">WhatsApp</p>
                      <p className="text-white/40 text-[10px]">Próximamente</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white/[0.02] border border-dashed border-white/10 rounded-2xl p-4 opacity-50">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl grayscale">🎮</div>
                    <div>
                      <p className="text-white/70 text-sm font-medium">Discord</p>
                      <p className="text-white/40 text-[10px]">Próximamente</p>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 px-6 py-3 flex justify-end bg-white/5 flex-shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm bg-white/10 hover:bg-white/20 rounded-lg text-white/80 transition"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChannelsPanel;
