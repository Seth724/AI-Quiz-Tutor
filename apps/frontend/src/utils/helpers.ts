export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

export const APP_TIMEZONE = 'Asia/Colombo';

export const formatDate = (date: string | Date): string => {
  const d = new Date(date);
  if (Number.isNaN(d.getTime())) {
    return '';
  }

  return d.toLocaleString('en-US', {
    timeZone: APP_TIMEZONE,
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatMonthYear = (date: string | Date): string => {
  const d = new Date(date);
  if (Number.isNaN(d.getTime())) {
    return '';
  }

  return d.toLocaleDateString('en-US', {
    timeZone: APP_TIMEZONE,
    month: 'long',
    year: 'numeric',
  });
};

export const truncateText = (text: string, length: number = 100): string => {
  return text.length > length ? text.substring(0, length) + '...' : text;
};

const SUPPORTED_STUDY_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff', '.heic', '.heif'];

const SUPPORTED_STUDY_MIME_PREFIXES = ['image/'];

export const isValidStudyFile = (file: File): boolean => {
  const fileName = (file.name || '').toLowerCase();
  const fileType = (file.type || '').toLowerCase();

  if (fileType === 'application/pdf') {
    return true;
  }

  if (SUPPORTED_STUDY_MIME_PREFIXES.some((prefix) => fileType.startsWith(prefix))) {
    return true;
  }

  return SUPPORTED_STUDY_EXTENSIONS.some((extension) => fileName.endsWith(extension));
};

export const isValidPdf = (file: File): boolean => {
  return isValidStudyFile(file);
};

const formatValidationItem = (item: any): string => {
  if (typeof item === 'string') {
    return item;
  }

  if (item && typeof item === 'object') {
    const loc = Array.isArray(item.loc) ? item.loc.join('.') : '';
    const msg = typeof item.msg === 'string' ? item.msg : '';
    if (loc && msg) {
      return `${loc}: ${msg}`;
    }
    if (msg) {
      return msg;
    }
    try {
      return JSON.stringify(item);
    } catch {
      return String(item);
    }
  }

  return String(item ?? '');
};

export const getErrorMessage = (error: any): string => {
  if (typeof error === 'string') {
    return error;
  }

  if (Array.isArray(error?.message)) {
    return error.message.map(formatValidationItem).join(' | ');
  }

  if (typeof error?.message === 'string') {
    return error.message;
  }

  if (Array.isArray(error?.detail)) {
    return error.detail.map(formatValidationItem).join(' | ');
  }

  if (typeof error?.detail === 'string') {
    return error.detail;
  }

  if (error?.detail && typeof error.detail === 'object') {
    try {
      return JSON.stringify(error.detail);
    } catch {
      return String(error.detail);
    }
  }

  return 'An unknown error occurred';
};
