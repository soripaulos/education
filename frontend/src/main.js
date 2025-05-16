import './index.css'

import { createApp } from 'vue'
import router from './router'
import App from './App.vue'
import { createPinia } from 'pinia'
// import '../polyfills'
import FrappePushNotification from "../public/frappe-push-notification.js"

import {
  Button,
  Card,
  Input,
  setConfig,
  frappeRequest,
  resourcesPlugin,
  toast,
} from 'frappe-ui'

import { VFrappeChart } from 'vue-frappe-chart'

// Initialize push notification service
const registerPushNotification = async () => {
  try {
    window.frappePushNotification = new FrappePushNotification("education")
  
    if ("serviceWorker" in navigator) {
      let serviceWorkerURL = "/assets/education/frontend/static/sw.js"
      
      const config = await window.frappePushNotification.fetchWebConfig()
      serviceWorkerURL = `${serviceWorkerURL}?config=${encodeURIComponent(
        JSON.stringify(config)
      )}`
      
      const registration = await navigator.serviceWorker.register(serviceWorkerURL, {
        scope: "/assets/education/frontend/"
      })
      
      await window.frappePushNotification.initialize(registration)
      console.log("Frappe Push Notification initialized")
    }
  } catch (error) {
    console.error("Failed to initialize push notifications:", error)
  }
}

// Register service worker
if ('serviceWorker' in navigator) {
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

  // Handle service worker registration
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/assets/education/frontend/static/sw.js', {
        scope: '/assets/education/frontend/'
      })
      .then(registration => {
        console.log('SW registered:', registration)
        
        toast({
          title: 'Ready for Offline Use',
          message: 'Student Portal can now work without internet',
          duration: 3000
        })

        // Listen for successful login
        window.addEventListener('frappe-login-success', () => {
          registration.active?.postMessage('login_successful')
        })
        
        // Initialize push notifications after service worker is registered
        registerPushNotification()
      })
      .catch(error => {
        console.log('SW registration failed:', error)
        toast({
          title: 'Service Worker Error',
          message: 'Some features might not work offline',
          duration: 5000
        })
      })
  })
}

// create a pinia instance
let pinia = createPinia()

let app = createApp(App)

setConfig('resourceFetcher', frappeRequest)

app.use(pinia)
app.use(router)
app.use(resourcesPlugin)

app.component('Button', Button)
app.component('Card', Card)
app.component('Input', Input)
app.component('VFrappeChart', VFrappeChart)

router.isReady().then(() => {
  app.mount('#app')
})


