frappe.ready(function() {
  // Only register service worker if it's supported
  if ('serviceWorker' in navigator && 'PushManager' in window) {
    registerServiceWorker();
  } else {
    console.log('Push notifications are not supported in this browser');
  }
});

// Function to register the service worker
async function registerServiceWorker() {
  try {
    const registration = await navigator.serviceWorker.register('/assets/education/sw.js');
    console.log('Education Service Worker registered with scope:', registration.scope);
    
    await setupPushNotifications(registration);
  } catch (error) {
    console.error('Service Worker registration failed:', error);
  }
}

// Function to set up push notifications
async function setupPushNotifications(registration) {
  // Check if push notifications are enabled in the backend
  const response = await frappe.call({
    method: 'education.education.api.are_push_notifications_enabled',
    args: {}
  });
  
  if (!response.message) {
    console.log('Push notifications are disabled on the server');
    return;
  }
  
  // We only set up the UI for notifications, without Firebase
  // Firebase initialization happens through the Core Frappe system
  
  // Add notification permission button if needed
  if (Notification.permission !== 'granted') {
    addPermissionButton();
  }
}

// Add a button to request notification permission
function addPermissionButton() {
  // Only add the button on certain pages like the dashboard
  if (window.location.pathname.includes('/me') || 
      window.location.pathname.includes('/dashboard') ||
      window.location.pathname.includes('/notifications')) {
    
    const button = document.createElement('button');
    button.textContent = 'Enable Notifications';
    button.className = 'btn btn-primary btn-sm mt-3';
    button.onclick = requestNotificationPermission;
    
    // Add to the page in a suitable location
    const targetElement = document.querySelector('.page-content') || document.body;
    targetElement.prepend(button);
  }
}

// Function to request notification permission
async function requestNotificationPermission() {
  try {
    const permission = await Notification.requestPermission();
    
    if (permission === 'granted') {
      frappe.show_alert({
        message: 'Notifications enabled!',
        indicator: 'green'
      });
      
      // Reload the page to make sure service worker is properly registered
      setTimeout(() => window.location.reload(), 1000);
    } else {
      frappe.show_alert({
        message: 'Notification permission denied.',
        indicator: 'red'
      });
    }
  } catch (error) {
    console.error('Error requesting notification permission:', error);
  }
} 