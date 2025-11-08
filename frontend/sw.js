/**
 * Service Worker for CodeMind PWA
 */

const CACHE_NAME = 'codemind-v1';
const RUNTIME_CACHE = 'codemind-runtime-v1';

// Files to cache on install
const STATIC_CACHE_FILES = [
  '/',
  '/index.html',
  '/login.html',
  '/register.html',
  '/dashboard.html',
  '/editor.html',
  '/css/style.css',
  '/css/landing.css',
  '/css/auth.css',
  '/css/editor.css',
  '/js/app.js',
  '/js/api.js',
  '/js/auth.js',
  '/js/editor.js',
  '/js/ai-assistant.js',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];

// Install event - cache static files
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching static files');
        return cache.addAll(STATIC_CACHE_FILES);
      })
      .catch((error) => {
        console.error('[Service Worker] Cache install failed:', error);
      })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // API requests - network first, then cache
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone the response
          const responseClone = response.clone();
          
          // Cache successful API responses
          if (response.status === 200) {
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          
          return response;
        })
        .catch(() => {
          // If network fails, try cache
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Return offline response for API calls
            return new Response(
              JSON.stringify({ error: 'Offline - No cached data available' }),
              {
                status: 503,
                statusText: 'Service Unavailable',
                headers: { 'Content-Type': 'application/json' }
              }
            );
          });
        })
    );
    return;
  }

  // Static files - cache first, then network
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }

        return fetch(request)
          .then((response) => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clone the response
            const responseToCache = response.clone();

            caches.open(RUNTIME_CACHE)
              .then((cache) => {
                cache.put(request, responseToCache);
              });

            return response;
          })
          .catch(() => {
            // If both cache and network fail, return offline page
            if (request.headers.get('accept').includes('text/html')) {
              return caches.match('/index.html');
            }
          });
      })
  );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync:', event.tag);
  if (event.tag === 'sync-feedback') {
    event.waitUntil(syncFeedback());
  }
});

// Push notifications (for future use)
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push notification received');
  const options = {
    body: event.data ? event.data.text() : 'New update available',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    tag: 'codemind-notification',
    requireInteraction: true
  };

  event.waitUntil(
    self.registration.showNotification('CodeMind', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification clicked');
  event.notification.close();
  event.waitUntil(
    clients.openWindow('/')
  );
});

// Helper function for syncing feedback (placeholder)
async function syncFeedback() {
  // This would sync any pending feedback when back online
  console.log('[Service Worker] Syncing feedback...');
}

