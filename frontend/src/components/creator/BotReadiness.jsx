import React from 'react';
import Card from '../Card';

/**
 * BotReadiness — Estado booleano del bot (READY / NOT_READY).
 *
 * NO usa puntuaciones (ni 82%, ni 5/7).
 * Solo muestra la fórmula:
 *   READY = config + workflow + publicación
 *
 * Props:
 *   - status: { configuration, workflow, publication, ready } del endpoint
 *   - onGoTo: (section: string) => void (para CTA de cada falta)
 */
const BotReadiness = ({ status, onGoTo }) => {
  if (!status) return null;

  const items = [
    {
      key: 'configuration',
      icon: '⚙️',
      label: 'Configuración',
      ok: status.configuration?.ok === true,
      cta: 'Ir a Configuración',
      action: () => onGoTo?.('config'),
    },
    {
      key: 'workflow',
      icon: '🔀',
      label: 'Workflow activo',
      ok: status.workflow?.ok === true,
      cta: 'Ir a Flujos',
      action: () => onGoTo?.('workflows'),
    },
    {
      key: 'publication',
      icon: '🌐',
      label: 'Publicado',
      ok: status.publication?.ok === true,
      cta: 'Publicar',
      action: () => onGoTo?.('publication'),
    },
  ];

  const okCount = items.filter((i) => i.ok).length;
  const total = items.length;
  const isReady = status.ready === true;

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-white font-semibold">Progreso</h2>
        <span className={`text-xs font-medium ${isReady ? 'text-emerald-300' : 'text-amber-300'}`}>
          {okCount} de {total}
        </span>
      </div>

      <ul className="space-y-2">
        {items.map((item) => (
          <li
            key={item.key}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg border transition ${
              item.ok
                ? 'bg-emerald-500/5 border-emerald-500/20'
                : 'bg-white/[0.02] border-white/10'
            }`}
          >
            <span
              className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                item.ok
                  ? 'bg-emerald-500/20 text-emerald-300'
                  : 'bg-white/10 text-white/40'
              }`}
            >
              {item.ok ? '✓' : ''}
            </span>
            <span className="text-sm flex-shrink-0">{item.icon}</span>
            <span className={`text-sm flex-1 ${item.ok ? 'text-white/80' : 'text-white/60'}`}>
              {item.label}
            </span>
            {!item.ok && onGoTo && (
              <button
                type="button"
                onClick={item.action}
                className="text-[11px] text-cyan-300 hover:text-cyan-200 underline"
              >
                {item.cta}
              </button>
            )}
          </li>
        ))}
      </ul>
    </Card>
  );
};

export default BotReadiness;
