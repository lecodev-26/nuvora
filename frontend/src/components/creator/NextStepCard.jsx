import React from 'react';
import Card from '../Card';
import Button from '../Button';

/**
 * NextStepCard — Card con el siguiente paso recomendado.
 *
 * Determinista. Sin IA. Sin puntuación.
 * Se calcula del campo `next_step` del endpoint.
 *
 * Props:
 *   - nextStep: "configuration" | "workflow" | "publication" | null
 *   - onGoTo: (section: string) => void
 */
const NextStepCard = ({ nextStep, onGoTo }) => {
  const configs = {
    configuration: {
      icon: '⚙️',
      title: 'Completa la configuración',
      description: 'Dale un nombre y personalidad a tu bot para empezar.',
      cta: 'Configurar bot',
      section: 'config',
    },
    workflow: {
      icon: '🔀',
      title: 'Crea o activa un workflow',
      description: 'El workflow define cómo responde tu bot a los mensajes.',
      cta: 'Ir a Flujos',
      section: 'workflows',
    },
    publication: {
      icon: '🌐',
      title: 'Publica tu bot',
      description: 'Tu bot está listo. Publícalo para obtener una URL pública.',
      cta: 'Publicar bot',
      section: 'publication',
    },
  };

  // Si no hay next_step → bot listo
  if (!nextStep) {
    return (
      <Card className="border-emerald-500/30 bg-emerald-500/5">
        <div className="flex items-start gap-3">
          <span className="text-3xl flex-shrink-0">🎉</span>
          <div className="flex-1">
            <h3 className="text-white font-semibold">Tu bot está funcionando</h3>
            <p className="text-white/60 text-sm mt-1">
              Todo está configurado. Puedes seguir mejorándolo o conectarlo a más canales.
            </p>
            <div className="mt-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onGoTo?.('channels')}
              >
                📡 Ver canales
              </Button>
            </div>
          </div>
        </div>
      </Card>
    );
  }

  const config = configs[nextStep];
  if (!config) return null;

  return (
    <Card className="border-cyan-500/30 bg-cyan-500/[0.03]">
      <div className="flex items-start gap-3">
        <span className="text-3xl flex-shrink-0">{config.icon}</span>
        <div className="flex-1">
          <p className="text-[10px] font-semibold tracking-wider text-cyan-300/70 uppercase">
            Siguiente paso
          </p>
          <h3 className="text-white font-semibold mt-0.5">{config.title}</h3>
          <p className="text-white/60 text-sm mt-1">{config.description}</p>
          <div className="mt-3">
            <Button
              variant="primary"
              size="sm"
              onClick={() => onGoTo?.(config.section)}
            >
              {config.cta}
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default NextStepCard;
