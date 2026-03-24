const CACHE_NAME = 'quiz-tutor-v3';
const STATIC_ASSETS = [
  '/',
  '/manifest.webmanifest',
  '/offline.html',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/apple-touch-icon.png',
];

function isAuthNavigation(url) {
  if (url.pathname.startsWith('/sign-in') || url.pathname.startsWith('/sign-up')) {
    return true;
  }

  // Clerk appends auth handshake params during redirect completion.
  if (url.searchParams.has('__clerk_db_jwt') || url.searchParams.has('__clerk_handshake')) {
    return true;
  }

  return false;
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => Promise.allSettled(STATIC_ASSETS.map((asset) => cache.add(asset))))
      .catch(() => undefined)
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== 'GET') {
    return;
  }

  if (url.origin !== self.location.origin) {
    return;
  }

  if (url.pathname.startsWith('/api/')) {
    return;
  }

  if (request.mode === 'navigate') {
    if (isAuthNavigation(url)) {
      event.respondWith(fetch(request));
      return;
    }

    event.respondWith(
      fetch(request)
        .then((response) => response)
        .catch(async () => {
          const cachedPage = await caches.match(request);
          if (cachedPage) {
            return cachedPage;
          }
          const offlinePage = await caches.match('/offline.html');
          if (offlinePage) {
            return offlinePage;
          }

          return new Response('Offline. Please reconnect and retry.', {
            status: 503,
            headers: { 'Content-Type': 'text/plain; charset=utf-8' },
          });
        })
    );
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      const networkFetch = fetch(request)
        .then((response) => {
          // Cache only successful, same-origin static responses.
          if (response.ok && response.type === 'basic') {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
          }
          return response;
        })
        .catch(() => cached);

      return cached || networkFetch;
    })
  );
});
