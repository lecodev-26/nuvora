import React from 'react';

const Badge = ({
  children,
  variant = 'default',
  className = '',
  ...props
}) => {
  const baseStyles = 'inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-full';

  const variants = {
    default: 'bg-white/10 text-white/80',
    active: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
    trial: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
    expired: 'bg-red-500/20 text-red-400 border border-red-500/30',
    primary: 'bg-violet-500/20 text-violet-400 border border-violet-500/30',
    cyan: 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30',
    magenta: 'bg-magenta-500/20 text-magenta-400 border border-magenta-500/30',
  };

  const statusDot = {
    active: 'w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse',
    trial: 'w-1.5 h-1.5 rounded-full bg-amber-400',
    expired: 'w-1.5 h-1.5 rounded-full bg-red-400',
    default: '',
  };

  return (
    <span
      className={`${baseStyles} ${variants[variant]} ${className}`}
      {...props}
    >
      {variant !== 'default' && variant !== 'primary' && variant !== 'cyan' && variant !== 'magenta' && (
        <span className={statusDot[variant] || statusDot.default} />
      )}
      {children}
    </span>
  );
};

export default Badge;
