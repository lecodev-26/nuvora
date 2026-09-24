import React from 'react';
import Button from '../Button';

/**
 * EmptyState — Estado vacío reutilizable en toda la app.
 *
 * Props:
 *   - icon: emoji o string
 *   - title: string
 *   - description: string (opcional)
 *   - ctaLabel: string (opcional)
 *   - onCta: () => void (opcional)
 *   - variant: "default" | "compact"
 */
const EmptyState = ({
  icon = '📭',
  title,
  description,
  ctaLabel,
  onCta,
  variant = 'default',
}) => {
  const isCompact = variant === 'compact';

  return (
    <div
      className={`flex flex-col items-center justify-center text-center ${
        isCompact ? 'py-6 px-4' : 'py-12 px-6'
      }`}
    >
      <div className={`${isCompact ? 'text-3xl' : 'text-5xl'} mb-3 opacity-80`}>
        {icon}
      </div>
      <h3 className={`text-white font-semibold ${isCompact ? 'text-sm' : 'text-base md:text-lg'}`}>
        {title}
      </h3>
      {description && (
        <p className={`text-white/50 mt-2 max-w-md ${isCompact ? 'text-xs' : 'text-sm'}`}>
          {description}
        </p>
      )}
      {ctaLabel && onCta && (
        <div className="mt-4">
          <Button variant="primary" size={isCompact ? 'sm' : 'md'} onClick={onCta}>
            {ctaLabel}
          </Button>
        </div>
      )}
    </div>
  );
};

export default EmptyState;
