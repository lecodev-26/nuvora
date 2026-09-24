import React from 'react';
import Button from '../Button';

/**
 * CreatorError — Estado de error en Creator Workspace.
 *
 * Props:
 *   - title: string
 *   - description: string (opcional)
 *   - ctaLabel: string (opcional, ej: "Reintentar")
 *   - onCta: () => void (opcional)
 *   - secondaryLabel: string (opcional, ej: "Volver a Mis bots")
 *   - onSecondary: () => void (opcional)
 */
const CreatorError = ({
  title = 'Algo ha ido mal',
  description,
  ctaLabel,
  onCta,
  secondaryLabel,
  onSecondary,
}) => {
  return (
    <div className="flex flex-col items-center justify-center text-center py-12 px-6">
      <div className="text-5xl mb-3">⚠️</div>
      <h3 className="text-white font-semibold text-base md:text-lg">{title}</h3>
      {description && (
        <p className="text-white/50 mt-2 max-w-md text-sm">{description}</p>
      )}
      <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
        {ctaLabel && onCta && (
          <Button variant="primary" size="md" onClick={onCta}>
            {ctaLabel}
          </Button>
        )}
        {secondaryLabel && onSecondary && (
          <Button variant="secondary" size="md" onClick={onSecondary}>
            {secondaryLabel}
          </Button>
        )}
      </div>
    </div>
  );
};

export default CreatorError;
