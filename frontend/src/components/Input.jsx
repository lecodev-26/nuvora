import React from 'react';

const Input = ({
  label,
  type = 'text',
  placeholder,
  value,
  onChange,
  className = '',
  error,
  required = false,
  iconLeft,
  iconRight,
  ...props
}) => {
  const baseStyles = 'w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-transparent transition-all duration-200';

  const errorStyles = error ? 'border-red-500/50 focus:ring-red-500/50' : '';

  const iconStyles = iconLeft ? 'pl-12' : '';
  const iconRightStyles = iconRight ? 'pr-12' : '';

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-white/70 mb-2">
          {label}
          {required && <span className="text-magenta-400 ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        {iconLeft && (
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40">
            {iconLeft}
          </span>
        )}
        <input
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          className={`${baseStyles} ${errorStyles} ${iconStyles} ${iconRightStyles}`}
          {...props}
        />
        {iconRight && (
          <span className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40">
            {iconRight}
          </span>
        )}
      </div>
      {error && (
        <p className="mt-1 text-sm text-red-400">{error}</p>
      )}
    </div>
  );
};

export default Input;
