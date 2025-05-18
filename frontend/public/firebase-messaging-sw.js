// Firebase messaging service worker for background notifications
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-messaging-compat.js');

// This service worker handles only Firebase push notification functions
// The main PWA service worker (sw.js) handles offline caching and PWA functionality

// Default Firebase configuration (this will be overridden by messaging from main.js)
const firebaseConfig = {
  apiKey: "AIzaSyDummyKeyF1rebase123456",
  authDomain: "education-portal-placeholder.firebaseapp.com",
  projectId: "education-portal-placeholder",
  storageBucket: "education-portal-placeholder.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:a1b2c3d4e5f6a7b8c9d0e1"
};

// Initialize Firebase with the default config
firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// Listen for messages when the app is in the background
messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Received background message: ', payload);

  // Customize notification here
  const notificationTitle = payload.data?.title || 'New Notification';
  const notificationOptions = {
    body: payload.data?.body || '',
    icon: payload.data?.icon || '/assets/education/frontend/pwa-icons/icon-192x192.png',
    data: {
      url: payload.data?.click_action || payload.data?.link || '/',
    },
  };

  if (notificationOptions.data.url && notificationOptions.data.url !== '/' && 
      !self.navigator.userAgent.toLowerCase().includes("chrome")) {
    notificationOptions.actions = [
      { action: "open_url", title: "View Details" },
    ];
  }

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click event
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  console.log('[firebase-messaging-sw.js] Notification clicked: ', event.notification);
  
  const urlToOpen = event.notification.data?.url || '/';
  
  if ((event.action === 'open_url' || !event.action) && urlToOpen) {
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
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