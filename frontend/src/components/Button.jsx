import React from 'react';

const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  disabled = false,
  onClick,
  type = 'button',
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-semibold rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-violet-400/50 disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary: 'bg-gradient-to-r from-cyan-500 via-violet-500 to-magenta-500 text-white hover:opacity-90 hover:shadow-glow active:scale-[0.98]',
    secondary: 'bg-white/10 text-white border border-white/20 hover:bg-white/20 hover:border-white/30 active:scale-[0.98]',
    outline: 'border-2 border-cyan-400 text-cyan-400 hover:bg-cyan-400/10 hover:border-cyan-300 active:scale-[0.98]',
    ghost: 'text-white/70 hover:text-white hover:bg-white/10 active:scale-[0.98]',
    danger: 'bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 active:scale-[0.98]',
    success: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30 active:scale-[0.98]',
  };

  const sizes = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg',
    icon: 'p-3 text-lg',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
