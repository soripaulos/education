// Basic Service Worker for Education module
self.addEventListener('install', function(event) {
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  clients.claim();
  console.log('Education Service Worker activated');
});

// Handle push notifications
self.addEventListener('push', function(event) {
  try {
    let data = event.data.json();
    
    const title = data.title || data.reference_document_type || 'New Notification';
    const options = {
      body: data.message || data.body || 'You have a new notification',
      icon: '/assets/education/images/education-logo.png',
      data: {
        url: data.click_action || '/notifications'
      }
    };
    
    event.waitUntil(
      self.registration.showNotification(title, options)
    );
  } catch (error) {
    console.error('Error showing notification:', error);
  }
});

// Handle notification click
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  
  event.waitUntil(
    clients.matchAll({
      type: 'window'
    }).then(function(clientList) {
      // Check if there's an existing window and navigate it
      for (var i = 0; i < clientList.length; i++) {
        var client = clientList[i];
        if (client.url === event.notification.data.url && 'focus' in client) {
          return client.focus();
        }
      }
      
      // If no window is open, open a new one
      if (clients.openWindow) {
        return clients.openWindow(event.notification.data.url);
      }
    })
  );
}); 