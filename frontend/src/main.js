import './index.css'

import { createApp } from 'vue'
import router from './router'
import App from './App.vue'
import { createPinia } from 'pinia'
// import '../polyfills'

import {
  Button,
  Card,
  Input,
  setConfig,
  frappeRequest,
  resourcesPlugin,
  toast,
} from 'frappe-ui'

// Import the FrappePushNotification class
import FrappePushNotification from '../public/frappe-push-notification'

// Create a pinia instance
const pinia = createPinia()
const app = createApp(App)

setConfig('resourceFetcher', frappeRequest)

app.use(pinia)
app.use(router)
app.use(resourcesPlugin)

app.component('Button', Button)
app.component('Card', Card)
app.component('Input', Input)

// Register service worker and setup push notifications
async function setupServiceWorker() {
  if ('serviceWorker' in navigator) {
    // Initialize FrappePushNotification
    window.frappePushNotification = new FrappePushNotification("education")
    
    let deferredPrompt;
    let hasShownPrompt = false;

    // Function to show install prompt
    const showInstallPrompt = () => {
      if (deferredPrompt && !hasShownPrompt) {
        toast({
          title: 'Install Student Portal',
          message: 'Get quick access and work offline',
          duration: 10000,
          actions: [
            {
              label: 'Install Now',
              variant: 'solid',
              action() {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => {
                  if (choiceResult.outcome === 'accepted') {
                    toast({
                      title: 'Successfully Installed',
                      message: 'You can now access Student Portal from your home screen',
                      duration: 5000
                    })
                  } else {
                    setTimeout(() => {
                      toast({
                        title: 'Reminder',
                        message: 'Install Student Portal for the best experience',
                        actions: [
                          {
                            label: 'Install',
                            variant: 'solid',
                            action() {
                              showInstallPrompt();
                            }
                          },
                          {
                            label: 'Maybe Later',
                            variant: 'subtle',
                            action() {
                              hasShownPrompt = true;
                            }
                          }
                        ]
                      })
                    }, 60000)
                  }
                  deferredPrompt = null;
                });
              },
            },
            {
              label: 'Not Now',
              variant: 'subtle',
              action() {
                // Do nothing, toast will dismiss
              }
            }
          ],
        })
        hasShownPrompt = true;
      }
    }

    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      
      // Show first prompt after 5 seconds
      setTimeout(showInstallPrompt, 5000);
    });

    // Show prompt when user returns to the app
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible' && !hasShownPrompt) {
        showInstallPrompt();
      }
    });

    try {
      // Configure service worker with Firebase config
      let serviceWorkerURL = '/assets/education/frontend/sw.js'
      
      // Only append config if relay server is available
      if (window.frappe?.boot.push_relay_server_url) {
        try {
          const config = await window.frappePushNotification.fetchWebConfig()
          serviceWorkerURL = `${serviceWorkerURL}?config=${encodeURIComponent(JSON.stringify(config))}`
        } catch (err) {
          console.error('Failed to fetch Firebase config:', err)
        }
      }
      
      // Register the service worker
      const registration = await navigator.serviceWorker.register(serviceWorkerURL, {
        scope: '/assets/education/frontend/',
        type: 'classic'
      })
      
      console.log('SW registered:', registration)
      
      // Initialize push notifications if relay server is configured
      if (window.frappe?.boot.push_relay_server_url) {
        try {
          await window.frappePushNotification.initialize(registration)
          console.log('Push notifications initialized')
        } catch (error) {
          console.error('Failed to initialize push notifications:', error)
        }
      }
      
      toast({
        title: 'Ready for Offline Use',
        message: 'Student Portal can now work without internet',
        duration: 3000
      })

      // Listen for successful login
      window.addEventListener('frappe-login-success', () => {
        registration.active?.postMessage('login_successful')
      })
    } catch (error) {
      console.error('Service worker registration failed:', error)
      toast({
        title: 'Service Worker Error',
        message: 'Some features might not work offline',
        duration: 5000
      })
    }
  }
}

// Start the app when router is ready
router.isReady().then(() => {
  app.mount('#app')
  setupServiceWorker()
})


