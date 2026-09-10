import React from 'react';

const Card = ({
  children,
  className = '',
  hover = false,
  glass = false,
  padding = 'p-6',
  ...props
}) => {
  const baseStyles = 'rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm transition-all duration-300';

  const hoverStyles = hover ? 'hover:border-violet-500/40 hover:shadow-glow hover:-translate-y-1' : '';
  const glassStyles = glass ? 'bg-white/5 backdrop-blur-xl border-white/10' : '';

  return (
    <div
      className={`${baseStyles} ${hoverStyles} ${glassStyles} ${padding} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
