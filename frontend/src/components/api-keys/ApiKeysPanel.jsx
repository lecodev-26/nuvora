import React, { useState, useEffect, useCallback } from 'react';
import Button from '../Button';
import ApiKeyCreateModal from './ApiKeyCreateModal';
import ConfirmModal from '../ui/ConfirmModal';
import { apiKeysService } from '../../services/apiKeysApi';

/**
 * ApiKeysPanel — Modal con la lista de API Keys + crear + revocar.
 *
 * Props:
 *   - open: boolean
 *   - botId: number
 *   - onClose: () => void
 */

const ApiKeysPanel = ({ open, botId, onClose }) => {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState(null);

  const load = useCallback(async () => {
    if (!botId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiKeysService.list(botId);
      setKeys(res.data.keys || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error cargando API Keys');
    } finally {
      setLoading(false);
    }
  }, [botId]);

  useEffect(() => {
    if (open && botId) load();
  }, [open, botId, load]);

  if (!open) return null;

  const handleCreate = async (name) => {
    const res = await apiKeysService.create(botId, name);
    // Recargar la lista
    await load();
    // Devolver la key creada al modal (que la mostrará UNA VEZ)
    return res.data;
  };

  const handleRevoke = (keyId, keyName) => {
    setConfirmDialog({
      title: 'Revocar API Key',
      message: `¿Revocar "${keyName}"?\n\nLas aplicaciones que usen esta clave dejarán de funcionar inmediatamente. Esta acción no se puede deshacer.`,
      confirmText: 'Revocar',
      danger: true,
      onConfirm: async () => {
        setConfirmDialog(null);
        try {
          await apiKeysService.revoke(botId, keyId);
          await load();
        } catch (err) {
          setError(err.response?.data?.detail || err.message || 'Error revocando');
        }
      },
    });
  };

  const formatDate = (iso) => {
    if (!iso) return '—';
    try {
      const d = new Date(iso);
      return d.toLocaleString('es-ES', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  return (
    <>
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <div
          className="bg-navy border border-white/10 rounded-2xl shadow-card w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
            <div>
              <h2 className="text-white text-lg font-semibold">🔑 API Keys</h2>
              <p className="text-white/40 text-xs">
                Consume tu bot desde aplicaciones externas
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
          <div className="px-6 py-4 overflow-y-auto flex-1 space-y-3">
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-300 text-sm">
                ⚠️ {error}
              </div>
            )}

            {/* Botón crear */}
            <div className="flex justify-end">
              <Button
                variant="primary"
                size="sm"
                onClick={() => setShowCreate(true)}
              >
                + Nueva API Key
              </Button>
            </div>

            {/* Loading */}
            {loading && (
              <div className="text-center text-white/50 py-8 text-sm">
                Cargando...
              </div>
            )}

            {/* Estado vacío */}
            {!loading && keys.length === 0 && (
              <div className="text-center text-white/40 py-8 border border-dashed border-white/10 rounded-lg">
                <div className="text-3xl mb-2">🔑</div>
                <div className="text-sm">
                  Aún no tienes API Keys.
                  <br />
                  Crea una para conectar tu bot a otras apps.
                </div>
              </div>
            )}

            {/* Lista */}
            {!loading && keys.map((k) => (
              <div
                key={k.id}
                className={`
                  border rounded-lg p-3 flex items-center gap-3
                  ${k.is_active ? 'border-white/10 bg-white/5' : 'border-white/5 bg-white/[0.02] opacity-60'}
                `}
              >
                <div className="text-2xl shrink-0">
                  {k.is_active ? '🔑' : '🚫'}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-white text-sm font-medium truncate">
                    {k.name}
                  </div>
                  <div className="text-white/40 text-xs font-mono truncate">
                    {k.key_prefix}...
                  </div>
                  <div className="text-white/40 text-[10px] mt-0.5 flex flex-wrap gap-x-3">
                    <span>Creada: {formatDate(k.created_at)}</span>
                    <span>Último uso: {k.last_used_at ? formatDate(k.last_used_at) : 'nunca'}</span>
                    {k.revoked_at && <span className="text-red-400">Revocada: {formatDate(k.revoked_at)}</span>}
                  </div>
                </div>
                {k.is_active ? (
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleRevoke(k.id, k.name)}
                  >
                    Revocar
                  </Button>
                ) : (
                  <span className="text-red-400 text-xs font-bold">REVOCADA</span>
                )}
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="border-t border-white/10 px-6 py-3 flex justify-between items-center bg-white/5">
            <a
              href="/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400 hover:text-cyan-300 text-xs underline"
            >
              📚 Ver documentación de la API →
            </a>
            <Button variant="ghost" size="sm" onClick={onClose}>
              Cerrar
            </Button>
          </div>
        </div>
      </div>

      {/* Modal crear (se abre encima) */}
      <ApiKeyCreateModal
        open={showCreate}
        onCreate={handleCreate}
        onClose={() => setShowCreate(false)}
      />

      {/* Confirm revocar */}
      <ConfirmModal
        open={!!confirmDialog}
        title={confirmDialog?.title}
        message={confirmDialog?.message}
        confirmText={confirmDialog?.confirmText}
        danger={confirmDialog?.danger}
        onConfirm={confirmDialog?.onConfirm}
        onCancel={() => setConfirmDialog(null)}
      />
    </>
  );
};

export default ApiKeysPanel;
