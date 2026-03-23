'use client';

import React from 'react';

interface AlertProps {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  onClose?: () => void;
}

const typeClasses = {
  success: 'border-emerald-300/40 bg-emerald-500/15 text-emerald-100',
  error: 'border-rose-300/40 bg-rose-500/15 text-rose-100',
  warning: 'border-amber-300/45 bg-amber-500/15 text-amber-100',
  info: 'border-violet-300/40 bg-violet-500/15 text-violet-100',
};

const iconClasses = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ',
};

export const Alert: React.FC<AlertProps> = ({ type, message, onClose }) => {
  return (
    <div className={`mb-4 flex items-start gap-3 rounded-xl border p-4 shadow-lg shadow-violet-950/20 backdrop-blur-sm ${typeClasses[type]}`}>
      <span className="text-xl font-bold">{iconClasses[type]}</span>
      <div className="flex-1">{message}</div>
      {onClose && (
        <button
          onClick={onClose}
          className="text-lg font-bold opacity-60 transition-opacity hover:opacity-100"
        >
          ×
        </button>
      )}
    </div>
  );
};
