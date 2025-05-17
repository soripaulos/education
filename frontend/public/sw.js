importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

// Get Firebase config from URL parameters
const jsonConfig = new URL(location).searchParams.get("config");
const firebaseApp = firebase.initializeApp(JSON.parse(jsonConfig));
const messaging = firebase.messaging(firebaseApp);

// Handle background messages
messaging.onBackgroundMessage((payload) => {
    const notificationTitle = payload.data.reference_document_type || 'New Notification';
    const notificationOptions = {
        body: payload.data.message || 'You have a new notification',
        icon: '/assets/education/frontend/logo.png',
        data: {
            url: payload.data.click_action || '/student-portal/notifications'
        }
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
}); 