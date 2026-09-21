import React, { useState } from 'react';
import Button from '../Button';

/**
 * ApiKeyCreateModal — Modal para crear una API Key.
 *
 * Props:
 *   - open: boolean
 *   - onCreate: (name) => Promise<{key, ...}>  (devuelve la key creada)
 *   - onClose: () => void
 *
 * Tras crear, muestra la key completa UNA SOLA VEZ.
 */

const ApiKeyCreateModal = ({ open, onCreate, onClose }) => {
  const [name, setName] = useState('');
  const [creating, setCreating] = useState(false);
  const [createdKey, setCreatedKey] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  // Reset al abrir
  React.useEffect(() => {
    if (open) {
      setName('');
      setCreatedKey(null);
      setError(null);
      setCopied(false);
    }
  }, [open]);

  if (!open) return null;

  const handleCreate = async () => {
    if (!name.trim()) {
      setError('El nombre es obligatorio');
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const result = await onCreate(name.trim());
      setCreatedKey(result);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = Array.isArray(detail)
        ? detail.map((e) => e.msg || JSON.stringify(e)).join(', ')
        : (typeof detail === 'string' ? detail : (detail?.message || err.message)) ||
          'Error creando la API Key';
      setError(msg);
    } finally {
      setCreating(false);
    }
  };

  const handleCopy = () => {
    if (!createdKey?.key) return;
    navigator.clipboard?.writeText(createdKey.key).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleClose = () => {
    // Si ya se creó la key, avisar (no se puede volver a ver)
    if (createdKey) {
      setCreatedKey(null);
    }
    onClose();
  };

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
      onClick={handleClose}
    >
      <div
        className="bg-navy border border-white/10 rounded-2xl shadow-card w-full max-w-md overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <h2 className="text-white text-lg font-semibold">
            🔑 {createdKey ? 'API Key creada' : 'Nueva API Key'}
          </h2>
          <button
            type="button"
            onClick={handleClose}
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

          {!createdKey ? (
            <>
              <p className="text-white/70 text-sm">
                Dale un nombre para identificarla (ej: "Mi web", "Bot Telegram").
              </p>

              <label className="block">
                <span className="text-white/60 text-xs uppercase tracking-wider">
                  Nombre
                </span>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Mi integración"
                  maxLength={100}
                  autoFocus
                  className="mt-2 w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-400/60"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleCreate();
                  }}
                />
              </label>
            </>
          ) : (
            <>
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 text-amber-300 text-xs">
                ⚠️ <strong>Guarda esta clave. No volverá a mostrarse.</strong>
                <br />
                Si la pierdes, tendrás que revocarla y crear otra.
              </div>

              <div>
                <span className="text-white/60 text-xs uppercase tracking-wider">
                  Tu API Key
                </span>
                <div className="mt-2 flex gap-2">
                  <input
                    type="text"
                    readOnly
                    value={createdKey.key}
                    className="flex-1 bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white text-xs font-mono break-all"
                    onClick={(e) => e.target.select()}
                  />
                </div>
                <button
                  type="button"
                  onClick={handleCopy}
                  className="mt-2 text-cyan-400 hover:text-cyan-300 text-xs underline"
                >
                  {copied ? '✓ Copiado' : '📋 Copiar al portapapeles'}
                </button>
              </div>

              <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-3 text-xs text-white/70">
                💡 <strong>¿Cómo usarla?</strong> Pásala como header:
                <pre className="mt-2 bg-black/40 rounded p-2 text-[10px] overflow-x-auto">
{`Authorization: Bearer ${createdKey.key_prefix}...`}
                </pre>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 px-6 py-3 flex justify-end gap-2 bg-white/5">
          {!createdKey ? (
            <>
              <Button variant="secondary" size="sm" onClick={handleClose}>
                Cancelar
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleCreate}
                disabled={creating}
              >
                {creating ? 'Creando...' : 'Crear API Key'}
              </Button>
            </>
          ) : (
            <Button variant="primary" size="sm" onClick={handleClose}>
              Hecho
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ApiKeyCreateModal;
