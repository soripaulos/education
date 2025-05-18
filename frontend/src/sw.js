// Service worker for PWA
self.addEventListener('fetch', (event) => {
  // Intercept navigation requests
  if (event.request.mode === 'navigate') {
    const url = new URL(event.request.url)
    
    // Handle login-related redirects
    if (url.pathname === '/login' || url.pathname === '/app' || url.pathname === '/home') {
      event.respondWith(
        fetch(event.request)
          .then(response => {
            // If response is a redirect or successful login
            if (response.redirected || response.ok) {
              return Response.redirect('/student-portal', 302)
            }
            return response
          })
          .catch(() => {
            return Response.redirect('/student-portal', 302)
          })
      )
      return
    }
  }
})

// Handle installation
self.addEventListener('install', (event) => {
  self.skipWaiting()
})

// Handle activation
self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      clients.claim(),
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        )
      })
    ])
  )
})

// Handle messages from the client
self.addEventListener('message', (event) => {
  if (event.data === 'login_successful') {
    // Notify all clients to redirect
    self.clients.matchAll().then(clients => {
      clients.forEach(client => {
        client.navigate('/student-portal')
      })
    })
  }
})

self.addEventListener('push', event => {
  const data = event.data.json();
  const title = data.title || 'New Notification';
  const options = {
    body: data.body || 'You have a new message.',
    icon: data.icon || '/assets/education/frontend/pwa-icons/icon-192x192.png', // Adjusted path based on manifest
    badge: data.badge || '/assets/education/frontend/pwa-icons/badge-72x72.png', // Placeholder, adjust as needed
    data: {
      url: data.url || '/' // URL to open on notification click
    }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windowClients => {
      const targetUrl = new URL(event.notification.data.url, self.location.origin);

      // Check if a window/tab matching the targeted URL already exists.
      const existingClient = windowClients.find(client => {
        const clientUrl = new URL(client.url);
        return clientUrl.pathname === targetUrl.pathname && clientUrl.origin === targetUrl.origin;
      });

      if (existingClient) {
        return existingClient.focus();
      } else {
        // If no such window/tab exists, open a new one.
        return clients.openWindow(event.notification.data.url || '/');
      }
    })
  );
}); 