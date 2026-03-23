'use client';

import React, { useRef } from 'react';
import { isValidStudyFile } from '@utils/helpers';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect, disabled = false }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = React.useState(false);

  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && isValidStudyFile(file)) {
      onFileSelect(file);
    } else {
      alert('Please select a valid PDF or image file (PNG, JPG, WEBP, etc.).');
    }
  };

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file && isValidStudyFile(file)) {
      onFileSelect(file);
    } else {
      alert('Please drop a valid PDF or image file (PNG, JPG, WEBP, etc.).');
    }
  };

  return (
    <div
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
        transition-all duration-200
        ${
          disabled
            ? 'cursor-not-allowed border-violet-200/20 bg-white/5 opacity-50'
            : dragActive
            ? 'border-fuchsia-300/70 bg-fuchsia-400/15'
            : 'border-violet-300/30 bg-white/5 hover:border-fuchsia-300/60 hover:bg-white/10'
        }
      `}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,image/*"
        onChange={handleFileChange}
        disabled={disabled}
        className="hidden"
      />

      <div className="flex flex-col items-center gap-3">
        <svg className="h-12 w-12 text-violet-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"
          />
        </svg>

        <div>
          <p className="text-lg font-semibold text-white">Drag and drop your file here</p>
          <p className="text-sm text-violet-100/75">PDF and image files are supported</p>
        </div>
      </div>
    </div>
  );
};
