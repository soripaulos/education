// Firebase Push Notification imports
import { initializeApp } from "firebase/app";
import { getMessaging, onBackgroundMessage } from "firebase/messaging/sw";

// Required line for workbox injectManifest - this will be replaced by the workbox precache manifest
self.__WB_MANIFEST;

let swFirebaseApp;
let swMessaging;

function initializeFirebaseMessaging(config) {
  if (!swFirebaseApp && config && Object.keys(config).length > 0) {
    try {
      swFirebaseApp = initializeApp(config);
      swMessaging = getMessaging(swFirebaseApp);
      console.log("[src/sw.js] Firebase Messaging initialized with config:", config);

      onBackgroundMessage(swMessaging, (payload) => {
        console.log("[src/sw.js] Received background message: ", payload);
        const notificationTitle = payload.data?.title || "New Notification";
        const notificationOptions = {
          body: payload.data?.body || "",
          icon: payload.data?.icon || payload.data?.notification_icon || "/assets/education/frontend/pwa-icons/icon-192x192.png",
          data: {
            url: payload.data?.click_action || payload.data?.link || "/",
          },
        };
        if (notificationOptions.data.url && notificationOptions.data.url !== '/' && !self.navigator.userAgent.toLowerCase().includes("chrome")) {
            notificationOptions.actions = [
                { action: "open_url", title: "View Details" },
            ];
        }
        self.registration.showNotification(notificationTitle, notificationOptions);
      });
    } catch (e) {
      console.error("[src/sw.js] Error initializing Firebase Messaging: ", e);
      swFirebaseApp = null; // Reset on error
      swMessaging = null;
    }
  }
}

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  console.log("[src/sw.js] Notification clicked: ", event.notification);
  const urlToOpen = event.notification.data?.url || "/";
  if ((event.action === "open_url" || !event.action) && urlToOpen) {
    event.waitUntil(
      clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
        for (const client of clientList) {
          if (new URL(client.url).pathname === new URL(urlToOpen, self.location.origin).pathname && 'focus' in client) {
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
    );
  }
});

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
  console.log("[src/sw.js] Installed.");
  self.skipWaiting()
})

// Handle activation
self.addEventListener('activate', (event) => {
  console.log("[src/sw.js] Activated.");
  event.waitUntil(
    Promise.all([
      clients.claim(),
      // It's generally better to let vite-plugin-pwa/Workbox manage cache cleanup
      // if it's generating the main SW structure.
      // caches.keys().then((cacheNames) => {
      //   return Promise.all(
      //     cacheNames.map((cacheName) => caches.delete(cacheName))
      //   )
      // })
    ])
  )
})

// Handle messages from the client
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SET_FIREBASE_CONFIG') {
    console.log("[src/sw.js] Received SET_FIREBASE_CONFIG message.");
    initializeFirebaseMessaging(event.data.firebaseConfig);
  } else if (event.data === 'login_successful') {
    console.log("[src/sw.js] Received login_successful message.");
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(clients => {
      clients.forEach(client => {
        // Ensure client.navigate is available and client is of type 'window'
        if (client.navigate && typeof client.navigate === 'function') {
            client.navigate('/student-portal');
        }
      })
    })
  }
}) 