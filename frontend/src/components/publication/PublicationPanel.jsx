import React, { useState, useEffect, useCallback } from 'react';
import { publicationApi } from '../../services/publicationApi';
import Button from '../Button';

/**
 * PublicationPanel — Modal con estado de publicación + acciones.
 *
 * Props:
 *   - open: boolean
 *   - botId: number
 *   - onClose: () => void
 *   - onPublished: () => void  (callback cuando se publica/despublica)
 */

const PublicationPanel = ({ open, botId, onClose, onPublished }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [showConfigForm, setShowConfigForm] = useState(false);

  // Form de config
  const [welcomeMessage, setWelcomeMessage] = useState('');
  const [placeholder, setPlaceholder] = useState('');
  const [primaryColor, setPrimaryColor] = useState('');
  const [showBranding, setShowBranding] = useState(true);

  // ============================================================
  // CARGA
  // ============================================================
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await publicationApi.getPublication(botId);
      setData(res.data);
      // Cargar valores del form
      const cfg = res.data.config || {};
      setWelcomeMessage(cfg.welcome_message || '');
      setPlaceholder(cfg.placeholder || '');
      setPrimaryColor(cfg.primary_color || '');
      setShowBranding(cfg.show_branding !== false);
    } catch (err) {
      setError(
        err.response?.data?.detail || err.message || 'Error cargando estado'
      );
    } finally {
      setLoading(false);
    }
  }, [botId]);

  useEffect(() => {
    if (open && botId) {
      load();
      setShowConfigForm(false);
      setCopied(false);
    }
  }, [open, botId, load]);

  if (!open) return null;

  // ============================================================
  // ACCIONES
  // ============================================================
  const handlePublish = async () => {
    setActionLoading(true);
    setError(null);
    try {
      await publicationApi.publish(botId);
      await load();
      onPublished?.();
    } catch (err) {
      setError(
        err.response?.data?.detail || err.message || 'Error publicando'
      );
    } finally {
      setActionLoading(false);
    }
  };

  const handleUnpublish = async () => {
    setActionLoading(true);
    setError(null);
    try {
      await publicationApi.unpublish(botId);
      await load();
      onPublished?.();
    } catch (err) {
      setError(
        err.response?.data?.detail || err.message || 'Error despublicando'
      );
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    setActionLoading(true);
    setError(null);
    try {
      const config = {
        welcome_message: welcomeMessage.trim() || null,
        placeholder: placeholder.trim() || null,
        primary_color: primaryColor.trim() || null,
        show_branding: showBranding,
      };
      await publicationApi.updatePublication(botId, config);
      await load();
      setShowConfigForm(false);
    } catch (err) {
      setError(
        err.response?.data?.detail || err.message || 'Error guardando config'
      );
    } finally {
      setActionLoading(false);
    }
  };

  const handleCopyUrl = () => {
    if (!data?.public_url) return;
    navigator.clipboard?.writeText(data.public_url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  // ============================================================
  // RENDER
  // ============================================================
  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-navy border border-white/10 rounded-2xl shadow-card w-full max-w-lg overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <h2 className="text-white text-lg font-semibold">
            🚀 Publicación
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-white/50 hover:text-white text-xl transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-4">
          {loading && (
            <div className="text-center text-white/50 py-8">
              Cargando...
            </div>
          )}

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-300 text-sm">
              ⚠️ {error}
            </div>
          )}

          {!loading && data && (
            <>
              {/* Estado */}
              <div className="flex items-center gap-3 bg-white/5 rounded-lg p-3">
                <div className={`w-2.5 h-2.5 rounded-full ${data.is_published ? 'bg-emerald-400' : 'bg-white/30'}`} />
                <div className="flex-1">
                  <div className="text-white text-sm font-medium">
                    {data.is_published ? '🟢 Publicado' : '⚪ No publicado'}
                  </div>
                  {data.published_at && (
                    <div className="text-white/40 text-xs">
                      Última publicación: {new Date(data.published_at).toLocaleString()}
                    </div>
                  )}
                </div>
              </div>

              {/* URL pública (si publicado) */}
              {data.is_published && data.public_url && (
                <div>
                  <label className="text-white/60 text-xs uppercase tracking-wider">
                    URL pública
                  </label>
                  <div className="mt-1 flex gap-2">
                    <input
                      type="text"
                      readOnly
                      value={data.public_url}
                      className="flex-1 bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm font-mono"
                    />
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={handleCopyUrl}
                    >
                      {copied ? '✓ Copiado' : '📋 Copiar'}
                    </Button>
                  </div>
                  <div className="mt-2 flex gap-2">
                    <a
                      href={data.public_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400 hover:text-cyan-300 text-xs underline"
                    >
                      Ver bot en nueva pestaña →
                    </a>
                  </div>
                </div>
              )}

              {/* Acciones */}
              {!data.is_published && (
                <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-3 text-xs text-white/70">
                  Al publicar, el workflow activo debe ser válido. Se generará
                  una URL pública y podrás compartir el bot con quien quieras.
                </div>
              )}

              {/* Botón Publicar / Despublicar */}
              <div className="flex flex-col gap-2">
                {!data.is_published ? (
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handlePublish}
                    disabled={actionLoading}
                    className="w-full"
                  >
                    {actionLoading ? 'Publicando...' : '🚀 Publicar bot'}
                  </Button>
                ) : (
                  <>
                    <Button
                      variant="secondary"
                      size="md"
                      onClick={() => setShowConfigForm(!showConfigForm)}
                      className="w-full"
                    >
                      {showConfigForm ? '↑ Ocultar config' : '✎ Editar apariencia'}
                    </Button>
                    <Button
                      variant="danger"
                      size="md"
                      onClick={handleUnpublish}
                      disabled={actionLoading}
                      className="w-full"
                    >
                      {actionLoading ? 'Despublicando...' : 'Despublicar'}
                    </Button>
                  </>
                )}
              </div>

              {/* Form de config */}
              {showConfigForm && data.is_published && (
                <div className="bg-white/5 rounded-lg p-4 space-y-3 border border-white/10">
                  <div className="text-white/70 text-xs uppercase tracking-wider">
                    Apariencia
                  </div>

                  <label className="block">
                    <span className="text-white/50 text-xs">Mensaje de bienvenida</span>
                    <input
                      type="text"
                      value={welcomeMessage}
                      onChange={(e) => setWelcomeMessage(e.target.value)}
                      placeholder="¡Hola! ¿En qué puedo ayudarte?"
                      maxLength={500}
                      className="mt-1 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-cyan-400/60"
                    />
                  </label>

                  <label className="block">
                    <span className="text-white/50 text-xs">Placeholder del input</span>
                    <input
                      type="text"
                      value={placeholder}
                      onChange={(e) => setPlaceholder(e.target.value)}
                      placeholder="Escribe un mensaje..."
                      maxLength={100}
                      className="mt-1 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-cyan-400/60"
                    />
                  </label>

                  <label className="block">
                    <span className="text-white/50 text-xs">Color principal (#RRGGBB)</span>
                    <div className="mt-1 flex gap-2">
                      <input
                        type="text"
                        value={primaryColor}
                        onChange={(e) => setPrimaryColor(e.target.value)}
                        placeholder="#7B5CFF"
                        maxLength={7}
                        className="flex-1 bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white text-sm font-mono focus:outline-none focus:border-cyan-400/60"
                      />
                      {primaryColor && /^#[0-9A-Fa-f]{6}$/.test(primaryColor) && (
                        <div
                          className="w-10 rounded-lg border border-white/10"
                          style={{ backgroundColor: primaryColor }}
                        />
                      )}
                    </div>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={showBranding}
                      onChange={(e) => setShowBranding(e.target.checked)}
                      className="w-4 h-4 cursor-pointer accent-cyan-400"
                    />
                    <span className="text-white/70 text-sm">
                      Mostrar "Powered by Nuvora"
                    </span>
                  </label>

                  <div className="flex justify-end gap-2 pt-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setShowConfigForm(false)}
                    >
                      Cancelar
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={handleSaveConfig}
                      disabled={actionLoading}
                    >
                      {actionLoading ? 'Guardando...' : 'Guardar'}
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 px-6 py-3 flex justify-end bg-white/5">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  );
};

export default PublicationPanel;
