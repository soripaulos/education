import { precacheAndRoute } from 'workbox-precaching'

// Use with workbox-build or workbox-webpack-plugin
precacheAndRoute(self.__WB_MANIFEST || [])

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

// Handle push notifications
self.addEventListener('push', (event) => {
  let payload = {}
  try {
    payload = event.data.json()
  } catch (error) {
    console.error('Error parsing push notification payload:', error)
    payload = {
      title: 'New Notification',
      body: event.data ? event.data.text() : 'No details available',
    }
  }

  const options = {
    body: payload.body || '',
    icon: payload.icon || '/apple-touch-icon.png',
    badge: '/badge-icon.png',
    data: payload.data || {},
    actions: payload.actions || [],
  }

  event.waitUntil(
    self.registration.showNotification(payload.title || 'Education Portal', options)
  )
})

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close()

  // Handle click on notification body
  if (event.action === '') {
    const urlToOpen = event.notification.data.url || '/'
    
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then((clientList) => {
        // If a window client is already open, use it
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.postMessage({ 
              type: 'NOTIFICATION_CLICK', 
              url: urlToOpen 
            })
            return client.focus()
          }
        }
        
        // Otherwise open a new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen)
        }
      })
    )
  } else {
    // Handle click on notification action
    const action = event.action
    if (action) {
      event.waitUntil(
        clients.matchAll({ type: 'window' }).then((clientList) => {
          for (const client of clientList) {
            if (client.url.includes(self.location.origin) && 'focus' in client) {
              client.postMessage({ 
                type: 'NOTIFICATION_ACTION', 
                action: action 
              })
              return client.focus()
            }
          }
          
          if (clients.openWindow) {
            return clients.openWindow(action)
          }
        })
      )
    }
  }
})

// Skip waiting and become active service worker
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
}) 