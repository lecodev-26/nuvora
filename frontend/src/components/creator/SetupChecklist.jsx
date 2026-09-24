import React from 'react';
import Card from '../Card';

/**
 * SetupChecklist — Checklist determinista del bot.
 *
 * NO guarda estado. Se calcula del status del endpoint.
 *
 * Props:
 *   - status: { configuration, workflow, publication } del endpoint
 *   - onGoTo: (section: string) => void
 */
const SetupChecklist = ({ status, onGoTo }) => {
  if (!status) return null;

  const steps = [
    {
      key: 'config',
      label: 'Crea tu bot',
      done: status.configuration?.ok === true,
      section: 'config',
    },
    {
      key: 'workflow',
      label: 'Crea un workflow',
      done: status.workflow?.ok === true,
      section: 'workflows',
    },
    {
      key: 'publish',
      label: 'Publica tu bot',
      done: status.publication?.ok === true,
      section: 'publication',
    },
    {
      key: 'channels',
      label: 'Conecta canales adicionales',
      done: status.channels?.api || status.channels?.telegram,
      section: 'channels',
      optional: true,
    },
  ];

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-white font-semibold">Checklist</h2>
        <span className="text-xs text-white/40">Opcionales incluidos</span>
      </div>

      <ul className="space-y-1">
        {steps.map((step) => (
          <li key={step.key}>
            <button
              type="button"
              onClick={() => onGoTo?.(step.section)}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/5 transition text-left group"
            >
              <span
                className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold border ${
                  step.done
                    ? 'bg-emerald-500/20 border-emerald-500/30 text-emerald-300'
                    : 'bg-white/5 border-white/15 text-white/30'
                }`}
              >
                {step.done ? '✓' : '○'}
              </span>
              <span
                className={`text-sm flex-1 ${
                  step.done ? 'text-white/80' : 'text-white/60'
                }`}
              >
                {step.label}
              </span>
              {step.optional && (
                <span className="text-[10px] text-white/30 border border-white/10 rounded-full px-2 py-0.5">
                  opcional
                </span>
              )}
              <span className="text-white/20 group-hover:text-cyan-400 transition text-xs">
                →
              </span>
            </button>
          </li>
        ))}
      </ul>
    </Card>
  );
};

export default SetupChecklist;
