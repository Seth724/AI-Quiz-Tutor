import '@/globals.css';
import type { AppProps } from 'next/app';
import { ClerkProvider } from '@clerk/nextjs';
import { useEffect } from 'react';

export default function App({ Component, pageProps }: AppProps) {
  useEffect(() => {
    const isProduction = process.env.NODE_ENV === 'production';
    const enablePwaInDev = process.env.NEXT_PUBLIC_PWA_DEV === 'true';
    if (!isProduction && !enablePwaInDev) {
      return;
    }

    if (!('serviceWorker' in navigator)) {
      return;
    }

    const register = async () => {
      try {
        await navigator.serviceWorker.register('/sw.js');
        console.log('✅ Service worker registered');
      } catch (error) {
        console.warn('Service worker registration failed:', error);
      }
    };

    void register();
  }, []);

  return (
    <ClerkProvider {...pageProps}>
      <Component {...pageProps} />
    </ClerkProvider>
  );
}
