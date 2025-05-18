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

import { VFrappeChart } from 'vue-frappe-chart'

// Register service worker
// Ensure FrappePushNotification is loaded, e.g., via script tag in index.html
if ('serviceWorker' in navigator && window.FrappePushNotification) {
  const registerServiceWorker = async () => {
    try {
      // Use "hrms" as the project name to potentially reuse existing HRMS Firebase setup
      const pushNotification = new window.FrappePushNotification("hrms");
      
      // The SW file is in /public, so its path from root is /sw.js
      let serviceWorkerURL = '/sw.js'; 
      serviceWorkerURL = await pushNotification.appendConfigToServiceWorkerURL(serviceWorkerURL);

      const registration = await navigator.serviceWorker.register(serviceWorkerURL, { 
        scope: '/' // Root scope is common for PWAs
      });
      console.log('SW registered with Firebase config:', registration);
      
      // Initialize the push notification client with the SW registration
      await pushNotification.initialize(registration);
      // Make it globally accessible for other parts of the app (e.g., settings toggle)
      window.educationPushNotification = pushNotification; 

      toast({
        title: 'Ready for Offline Use & Notifications',
        message: 'Student Portal can now work offline and receive notifications.',
        duration: 3000
      });

      // Listen for successful login (existing logic can be kept if needed)
      window.addEventListener('frappe-login-success', () => {
        registration.active?.postMessage('login_successful');
      });

    } catch (error) {
      console.error('SW registration or Push Notification init failed:', error);
      toast({
        title: 'Service Worker Error',
        message: error.message || 'Offline features or notifications might not work as expected.',
        duration: 7000 
      });
    }
  };

  window.addEventListener('load', registerServiceWorker);

  // Retain existing beforeinstallprompt logic for PWA installation
  let deferredPrompt;
  let hasShownPrompt = false;

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
    setTimeout(showInstallPrompt, 5000);
  });

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && !hasShownPrompt) {
      showInstallPrompt();
    }
  });

} else if ('serviceWorker' in navigator) {
    // Fallback if FrappePushNotification is not available but service workers are.
    // This attempts to register the sw.js for basic offline capabilities (precaching).
    console.warn("FrappePushNotification class not found. Push notifications will not be initialized. Attempting basic SW registration for offline caching.");
     window.addEventListener('load', () => {
        navigator.serviceWorker
        .register('/sw.js', { // Path to the copied sw.js in public folder
            scope: '/' // General scope
        })
        .then(registration => {
            console.log('SW registered (basic offline):', registration)
            toast({
                title: 'Ready for Offline Use',
                message: 'Student Portal can now work without internet (notifications may not be available).',
                duration: 3000
            })
            // Optional: If your sw.js has other postMessage handlers
            // window.addEventListener('frappe-login-success', () => {
            //     registration.active?.postMessage('login_successful')
            // })
        })
        .catch(error => {
            console.error('SW registration failed (basic offline):', error)
            toast({
                title: 'Service Worker Error',
                message: 'Offline features may not work correctly.',
                duration: 5000
            });
        })
    });

    // Also retain beforeinstallprompt for PWA install, even in this fallback
    let deferredPrompt;
    let hasShownPrompt = false;
    const showInstallPrompt = () => {
      if (deferredPrompt && !hasShownPrompt) {
        // Simplified toast as push specific parts are not available
        toast({ title: 'Install Student Portal', message: 'Get quick access and work offline', duration: 10000, 
            actions: [ { label: 'Install Now', variant: 'solid', action() { deferredPrompt.prompt(); /* ... */ } }, { label: 'Not Now', variant: 'subtle' } ]
        });
        hasShownPrompt = true;
      }
    }
    window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); deferredPrompt = e; setTimeout(showInstallPrompt, 5000); });
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible' && !hasShownPrompt) { showInstallPrompt(); } });
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


