import React from 'react';

const Layout = ({
  children,
  className = '',
  maxWidth = 'max-w-7xl',
  padding = 'px-4 md:px-8 py-8',
  ...props
}) => {
  return (
    <div className={`min-h-screen bg-navy text-white ${className}`} {...props}>
      <div className={`mx-auto ${maxWidth} ${padding}`}>
        {children}
      </div>
    </div>
  );
};

export default Layout;
