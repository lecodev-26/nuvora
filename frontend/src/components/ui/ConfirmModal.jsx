import React from 'react';
import Button from '../Button';

/**
 * ConfirmModal — Modal de confirmación reutilizable.
 *
 * Props:
 *  - open: boolean
 *  - title: string
 *  - message: string
 *  - confirmText: string (default: 'Confirmar')
 *  - cancelText: string (default: 'Cancelar')
 *  - danger: boolean (si true, botón rojo)
 *  - onConfirm: () => void
 *  - onCancel: () => void
 */

const ConfirmModal = ({
  open,
  title = 'Confirmar',
  message,
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  danger = false,
  onConfirm,
  onCancel,
}) => {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
      onClick={onCancel}
    >
      <div
        className="bg-navy border border-white/10 rounded-2xl shadow-card w-full max-w-md overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-5">
          <h2 className="text-white text-lg font-semibold mb-2">{title}</h2>
          {message && (
            <p className="text-white/70 text-sm whitespace-pre-line">{message}</p>
          )}
        </div>

        <div className="px-6 py-4 bg-white/5 border-t border-white/10 flex items-center justify-end gap-2">
          <Button variant="secondary" size="sm" onClick={onCancel}>
            {cancelText}
          </Button>
          <Button
            variant={danger ? 'danger' : 'primary'}
            size="sm"
            onClick={onConfirm}
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;
