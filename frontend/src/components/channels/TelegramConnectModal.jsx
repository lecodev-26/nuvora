import React, { useState } from 'react';
import Button from '../Button';

/**
 * TelegramConnectModal — Modal para conectar un bot con Telegram.
 *
 * Props:
 *   - open: boolean
 *   - onConnect: (token) => Promise<{status, telegram_username, ...}>
 *   - onClose: () => void
 *
 * Flujo:
 *   1. Muestra instrucciones de BotFather.
 *   2. Usuario pega el token.
 *   3. Click "Conectar" → onConnect(token) → backend hace getMe + setWebhook.
 *   4. Si todo OK, cierra el modal.
 *   5. Si falla, muestra error inline.
 */

const TelegramConnectModal = ({ open, onConnect, onClose }) => {
  const [token, setToken] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState(null);

  // Reset al abrir
  React.useEffect(() => {
    if (open) {
      setToken('');
      setError(null);
    }
  }, [open]);

  if (!open) return null;

  const handleConnect = async () => {
    const trimmed = token.trim();
    if (!trimmed) {
      setError('El token es obligatorio');
      return;
    }
    if (trimmed.length < 10) {
      setError('El token parece demasiado corto');
      return;
    }

    setConnecting(true);
    setError(null);
    try {
      await onConnect(trimmed);
      // Si todo OK, el padre cierra el modal
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = Array.isArray(detail)
        ? detail.map((e) => e.msg || JSON.stringify(e)).join(', ')
        : (typeof detail === 'string' ? detail : (detail?.message || err.message)) ||
          'Error conectando con Telegram';
      setError(msg);
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-navy border border-white/10 rounded-2xl shadow-card w-full max-w-lg overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <h2 className="text-white text-lg font-semibold">
            🤖 Conectar Telegram
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
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-300 text-sm">
              ⚠️ {error}
            </div>
          )}

          {/* Instrucciones */}
          <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-4 text-sm">
            <p className="text-white font-medium mb-2">
              📋 Cómo crear tu bot en Telegram
            </p>
            <ol className="text-white/70 text-xs space-y-1 list-decimal list-inside">
              <li>Abre Telegram y busca <code className="text-cyan-300">@BotFather</code></li>
              <li>Envíale <code className="text-cyan-300">/newbot</code></li>
              <li>Dale un nombre (ej: "Mi Restaurante Bot")</li>
              <li>Dale un username (debe acabar en "bot", ej: <code className="text-cyan-300">mirestaurante_bot</code>)</li>
              <li>BotFather te dará un token así: <code className="text-cyan-300">1234567890:ABC...</code></li>
              <li>Cópialo y pégalo aquí abajo</li>
            </ol>
          </div>

          {/* Input de token */}
          <label className="block">
            <span className="text-white/60 text-xs uppercase tracking-wider">
              Token del bot
            </span>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
              autoFocus
              className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm font-mono focus:outline-none focus:border-cyan-400/60"
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleConnect();
              }}
            />
            <p className="mt-2 text-white/40 text-[11px]">
              🔒 El token se cifra antes de guardarse. Nunca se mostrará de nuevo.
            </p>
          </label>
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 px-6 py-3 flex justify-end gap-2 bg-white/5">
          <Button variant="secondary" size="sm" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleConnect}
            disabled={connecting}
          >
            {connecting ? 'Conectando...' : 'Conectar Telegram'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default TelegramConnectModal;
