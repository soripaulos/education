// Check if browser is Chrome
function isChrome() {
  return navigator.userAgent.toLowerCase().includes('chrome')
}

// Show a notification
export const showNotification = (payload) => {
  // Use global Frappe Push Notification if available
  const registration = window.frappePushNotification?.serviceWorkerRegistration
  if (!registration) return

  const notificationTitle = payload?.data?.title || 'Education Portal'
  const notificationOptions = {
    body: payload?.data?.body || '',
  }
  
  if (payload?.data?.icon) {
    notificationOptions.icon = payload.data.icon
  }
  
  if (isChrome()) {
    notificationOptions.data = {
      url: payload?.data?.click_action || '/',
    }
  } else {
    if (payload?.data?.click_action) {
      notificationOptions.actions = [
        {
          action: payload.data.click_action,
          title: 'View Details',
        },
      ]
    }
  }

  registration.showNotification(notificationTitle, notificationOptions)
}

// Register service worker for notifications
export const registerServiceWorker = async () => {
  if (!('serviceWorker' in navigator)) {
    console.warn('Service workers are not supported in this browser')
    return null
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
    })
    
    // Wait for the service worker to be ready
    await navigator.serviceWorker.ready
    
    // Update service worker if needed
    if (registration.waiting) {
      registration.waiting.postMessage({ type: 'SKIP_WAITING' })
    }
    
    return registration
  } catch (error) {
    console.error('Service worker registration failed:', error)
    return null
  }
}

// Initialize push notifications
export const initPushNotifications = async () => {
  // If Frappe Push Notification is available, use it
  if (window.frappePushNotification) {
    console.log('Using Frappe Push Notification')
    
    // Check if notification permission is granted
    if (Notification.permission === 'granted') {
      try {
        // Enable using Frappe's system
        const result = await window.frappePushNotification.enableNotification()
        return result.permission_granted
      } catch (error) {
        console.error('Error enabling Frappe push notifications:', error)
      }
    } else if (Notification.permission === 'denied') {
      console.warn('Notification permission has been denied')
      return false
    } else {
      try {
        // Request permission using Frappe's system
        const result = await window.frappePushNotification.enableNotification()
        return result.permission_granted
      } catch (error) {
        console.error('Error requesting notification permission:', error)
        return false
      }
    }
  } 
  
  // Fall back to our own implementation
  console.log('Using custom push notification implementation')
  
  // Check if push notifications are supported
  if (!('PushManager' in window)) {
    console.warn('Push notifications are not supported in this browser')
    return false
  }
  
  try {
    // Register service worker
    const registration = await registerServiceWorker()
    if (!registration) return false
    
    // Check if notification permission is granted
    if (Notification.permission === 'granted') {
      return true
    } else if (Notification.permission === 'denied') {
      console.warn('Notification permission has been denied')
      return false
    }
    
    // Request permission
    const permission = await Notification.requestPermission()
    return permission === 'granted'
  } catch (error) {
    console.error('Error initializing push notifications:', error)
    return false
  }
}

// Handle notification clicks
export const setupNotificationClickHandler = () => {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', (event) => {
      // Handle notification click
      if (event.data?.type === 'NOTIFICATION_CLICK' && event.data?.url) {
        window.location.href = event.data.url
      }
      
      // Handle notification action
      if (event.data?.type === 'NOTIFICATION_ACTION' && event.data?.action) {
        window.location.href = event.data.action
      }
    })
  }
} 