'use client';

import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
}

export const Card: React.FC<CardProps> = ({ children, className = '', title, subtitle }) => {
  return (
    <div
      className={`rounded-2xl border border-violet-200/20 bg-gradient-to-br from-violet-900/35 via-indigo-900/30 to-fuchsia-900/25 p-6 shadow-2xl shadow-violet-950/30 backdrop-blur-xl ${className}`}
    >
      {title && (
        <div className="mb-4">
          <h3 className="text-xl font-bold text-white">{title}</h3>
          {subtitle && <p className="mt-1 text-sm text-violet-100/75">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
};
