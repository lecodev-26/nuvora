import React, { useState, useEffect, useCallback } from 'react';
import Button from '../Button';
import ConfirmModal from '../ui/ConfirmModal';
import TelegramConnectModal from './TelegramConnectModal';
import { telegramService } from '../../services/telegramApi';

/**
 * TelegramPanel — Panel de gestión de la integración Telegram.
 *
 * Props:
 *   - botId: number
 *
 * Estados:
 *   - loading: cargando estado inicial
 *   - status: null (no conectado) | { status, telegram_username, ... }
 *   - showConnect: modal de conexión
 *   - confirmDialog: modal de confirmación (disconnect)
 *
 * UX:
 *   - Desconectado: borde dashed cyan + botón "Conectar Telegram"
 *   - Conectado: borde sólido + badge verde + botones "Probar" / "Desconectar"
 */

const TelegramPanel = ({ botId }) => {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [showConnect, setShowConnect] = useState(false);
  const [testing, setTesting] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState(null);

  const load = useCallback(async () => {
    if (!botId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await telegramService.getStatus(botId);
      setStatus(res.data);  // puede ser null
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error cargando estado');
    } finally {
      setLoading(false);
    }
  }, [botId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleConnect = async (token) => {
    const res = await telegramService.connect(botId, token);
    setStatus(res.data);
    setShowConnect(false);
  };

  const handleTest = async () => {
    setTesting(true);
    setError(null);
    try {
      const res = await telegramService.test(botId);
      // Mostrar feedback rápido
      if (res.data.ok) {
        // Podría ser un toast, de momento alert simple
        alert(`✅ Conexión OK\n\nBot: @${res.data.username || '?'}\nNombre: ${res.data.first_name || '?'}`);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error probando conexión');
    } finally {
      setTesting(false);
    }
  };

  const handleDisconnect = () => {
    setConfirmDialog({
      title: 'Desconectar Telegram',
      message: `¿Desconectar @${status?.telegram_username || '?'}?\n\nEl bot dejará de responder en Telegram inmediatamente. Podrás volver a conectarlo cuando quieras.`,
      confirmText: 'Desconectar',
      danger: true,
      onConfirm: async () => {
        setConfirmDialog(null);
        try {
          await telegramService.disconnect(botId);
          await load();
        } catch (err) {
          setError(err.response?.data?.detail || err.message || 'Error desconectando');
        }
      },
    });
  };

  const formatDate = (iso) => {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleString('es-ES', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  // ============================================================
  // RENDER
  // ============================================================

  if (loading) {
    return (
      <div className="bg-white/5 border border-white/10 rounded-2xl p-6 text-center">
        <p className="text-white/50 text-sm">Cargando estado de Telegram...</p>
      </div>
    );
  }

  const isConnected = status && status.is_active && status.status === 'connected';

  return (
    <div className="space-y-3">
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-300 text-sm">
          ⚠️ {error}
        </div>
      )}

      {!isConnected ? (
        // ------- DESCONECTADO -------
        <div className="bg-white/[0.03] border-2 border-dashed border-white/20 hover:border-cyan-500/40 rounded-2xl p-6 transition-all">
          <div className="flex items-start gap-4">
            <div className="text-4xl">🤖</div>
            <div className="flex-1">
              <p className="text-white font-semibold">Telegram</p>
              <p className="text-white/50 text-xs mt-1">
                Conecta tu bot a Telegram para responder automáticamente a mensajes privados.
              </p>
            </div>
          </div>
          <div className="mt-4">
            <Button
              variant="primary"
              size="md"
              onClick={() => setShowConnect(true)}
            >
              🤖 Conectar Telegram
            </Button>
          </div>
        </div>
      ) : (
        // ------- CONECTADO -------
        <div className="bg-white/5 border border-emerald-500/30 rounded-2xl p-6">
          <div className="flex items-start gap-4">
            <div className="text-4xl">🤖</div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <p className="text-white font-semibold">Telegram</p>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Conectado
                </span>
              </div>
              <p className="text-white/70 text-sm mt-1">
                Bot: <span className="text-cyan-300">@{status.telegram_username || '?'}</span>
              </p>
              {status.created_at && (
                <p className="text-white/40 text-xs mt-0.5">
                  Conectado: {formatDate(status.created_at)}
                </p>
              )}
              {status.last_event_at && (
                <p className="text-white/40 text-xs">
                  Último mensaje: {formatDate(status.last_event_at)}
                </p>
              )}
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={handleTest}
              disabled={testing}
            >
              {testing ? 'Probando...' : '🔍 Probar conexión'}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleDisconnect}
            >
              🔌 Desconectar
            </Button>
          </div>
        </div>
      )}

      {/* Modales */}
      <TelegramConnectModal
        open={showConnect}
        onConnect={handleConnect}
        onClose={() => setShowConnect(false)}
      />

      <ConfirmModal
        open={!!confirmDialog}
        title={confirmDialog?.title || ''}
        message={confirmDialog?.message || ''}
        confirmText={confirmDialog?.confirmText || 'Confirmar'}
        danger={confirmDialog?.danger}
        onConfirm={confirmDialog?.onConfirm || (() => {})}
        onCancel={() => setConfirmDialog(null)}
      />
    </div>
  );
};

export default TelegramPanel;
