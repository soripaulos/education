importScripts("https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js");

// Get the Firebase config from the URL.
const config = new URL(location).searchParams.get("config");
const firebaseConfig = JSON.parse(decodeURIComponent(config));

// Initialize the Firebase app in the service worker
firebase.initializeApp(firebaseConfig);

// Retrieve an instance of Firebase Messaging
const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage(function(payload) {
  console.log("Received background message:", payload);

  const notificationTitle = payload.data.title;
  const notificationOptions = {
    body: payload.data.body || "",
    icon: payload.data.notification_icon || "/assets/education/frontend/icons/icon-192x192.png",
    data: {
      url: payload.data.click_action
    }
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

self.addEventListener("notificationclick", function(event) {
  event.notification.close();
  if (event.notification.data && event.notification.data.url) {
    clients.openWindow(event.notification.data.url);
  }
});

// Service worker lifecycle events
self.addEventListener("install", function(event) {
  self.skipWaiting();
  console.log("Service Worker installed");
});

self.addEventListener("activate", function(event) {
  event.waitUntil(clients.claim());
  console.log("Service Worker activated");
}); 