// Service worker for PWA
const CACHE_NAME = 'education-portal-v1';
const ASSETS_TO_CACHE = [
  '/student-portal',
  '/student-portal/',
  '/assets/education/frontend/index.html',
  '/assets/education/frontend/main.js',
  '/assets/education/frontend/favicon.png',
  // CSS files will be cached on the fly
];

// Install event - cache basic assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      clients.claim(),
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => cacheName !== CACHE_NAME)
            .map((cacheName) => caches.delete(cacheName))
        );
      })
    ])
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;
  
  const url = new URL(event.request.url);
  
  // Handle API requests differently - prefer network
  if (url.pathname.startsWith('/api/')) {
    // For API calls, try network first, then fallback to cached response if available
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Clone the response for caching
          const responseToCache = response.clone();
          
          // Only cache successful responses
          if (response.ok) {
            caches.open(CACHE_NAME)
              .then(cache => cache.put(event.request, responseToCache));
          }
          
          return response;
        })
        .catch(() => {
          // If network fails, try to get from cache
          return caches.match(event.request);
        })
    );
    return;
  }
  
  // Handle navigation requests - important for SPA
  if (event.request.mode === 'navigate') {
    // For navigation, check cache first, then network
    event.respondWith(
      caches.match('/student-portal')
        .then(response => {
          return response || fetch(event.request)
            .then(fetchResponse => {
              // Cache the navigation response for offline use
              return caches.open(CACHE_NAME).then(cache => {
                cache.put('/student-portal', fetchResponse.clone());
                return fetchResponse;
              });
            })
            .catch(() => {
              // If both cache and network fail, return a fallback offline page
              return caches.match('/student-portal');
            });
        })
    );
    return;
  }
  
  // For everything else (scripts, styles, images)
  // Try the cache first, then fetch from network and update cache
  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        // Return cached response if available
        if (cachedResponse) {
          // Fetch from network in the background to update cache
          fetch(event.request)
            .then(response => {
              if (response.ok) {
                caches.open(CACHE_NAME)
                  .then(cache => cache.put(event.request, response));
              }
            })
            .catch(() => console.log('Failed to update cache for:', event.request.url));
          
          return cachedResponse;
        }
        
        // If not in cache, fetch from network
        return fetch(event.request)
          .then(response => {
            // Return the response immediately
            const responseToCache = response.clone();
            
            // Update cache in the background
            if (response.ok) {
              caches.open(CACHE_NAME)
                .then(cache => cache.put(event.request, responseToCache));
            }
            
            return response;
          })
          .catch(error => {
            console.error('Fetch failed:', error);
            // Optionally return a fallback for certain asset types
            // For now, just propagate the error
            throw error;
          });
      })
  );
});

// Handle messages from the client
self.addEventListener('message', (event) => {
  if (event.data === 'login_successful') {
    // Notify all clients to redirect
    self.clients.matchAll().then(clients => {
      clients.forEach(client => {
        client.navigate('/student-portal');
      });
    });
  }
  
  // Check for cache refresh command
  if (event.data === 'clear_cache') {
    caches.delete(CACHE_NAME).then(() => {
      console.log('Cache cleared successfully');
      self.clients.matchAll().then(clients => {
        clients.forEach(client => {
          client.postMessage('cache_cleared');
        });
      });
    });
  }
}); 