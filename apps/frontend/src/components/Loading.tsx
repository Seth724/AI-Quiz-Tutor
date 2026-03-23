'use client';

import React from 'react';

interface LoadingProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
}

const sizeClasses = {
  small: 'w-6 h-6',
  medium: 'w-12 h-12',
  large: 'w-16 h-16',
};

export const Loading: React.FC<LoadingProps> = ({ message = 'Loading...', size = 'medium' }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-4">
      <svg
        className={`${sizeClasses[size]} animate-spin text-violet-300`}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
      </svg>
      {message && <p className="font-medium text-violet-100/85">{message}</p>}
    </div>
  );
};
