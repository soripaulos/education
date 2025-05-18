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

// Import your FrappePushNotification class
import FrappePushNotification from './utils/frappe-push-notification.js'

// Import PWA registration helper from vite-plugin-pwa
import { registerSW } from 'virtual:pwa-register'

// PWA auto-update and registration logic
const updateSW = registerSW({
  onNeedRefresh() {
    toast({ 
      title: 'Update Available', 
      message: 'New content is available, please refresh.', 
      actions: [{ label: 'Refresh', variant: 'solid', action: () => updateSW(true) }]
    })
  },
  onOfflineReady() {
    toast({ title: 'App Ready Offline', message: 'The app has been installed and is ready to work offline.' })
  },
  async onRegisteredSW(swUrl, registration) {
    console.log(`Service Worker at ${swUrl} registered with scope: ${registration.scope}`)
    try {
      // Use "hrms" to align with shared backend/FCM config as per user request
      const pushManager = new FrappePushNotification("hrms")
      console.log("[Main.js] FrappePushNotification instance created for 'hrms'");
      
      const firebaseConfig = await pushManager.fetchWebConfig()
      console.log("[Main.js] Firebase config fetched in main.js:", firebaseConfig ? JSON.stringify(firebaseConfig) : 'null or undefined');

      // Get Firebase Messaging Service Worker Registration
      const firebaseMessagingSW = await navigator.serviceWorker.register('/firebase-messaging-sw.js');
      console.log("[Main.js] Firebase Messaging service worker registered:", firebaseMessagingSW.scope);

      // Initialize the push manager for client-side operations (enable/disable notifications)
      console.log("[Main.js] Attempting to initialize pushManager...");
      await pushManager.initialize(registration) 
      console.log("[Main.js] pushManager.initialize() completed.");
      window.educationPushNotification = pushManager // Make it global for NotificationSettings.vue
      console.log("[Main.js] window.educationPushNotification is SET.");

    } catch (error) {
      console.error('[Main.js] Error in onRegisteredSW during FrappePushNotification setup:', error);
      toast({ title: 'Push Notification Setup Error', message: `Could not fully initialize push notifications: ${error.message}`, type: 'error' })
    }
  },
  onRegisterError(error) {
    console.error('Service Worker registration error from vite-plugin-pwa:', error)
    toast({ title: 'PWA Registration Error', message: 'Failed to register service worker. Offline features and notifications might not work.', type: 'error' })
  }
})

// PWA Install Prompt Logic (can be kept as it's separate from SW registration for push/offline)
if ('serviceWorker' in navigator) { 
    let deferredPrompt
    let hasShownPrompt = false

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
                            deferredPrompt.prompt()
                            deferredPrompt.userChoice.then((choiceResult) => {
                                if (choiceResult.outcome === 'accepted') {
                                    toast({
                                        title: 'Successfully Installed',
                                        message: 'You can now access Student Portal from your home screen',
                                        duration: 5000
                                    })
                                }
                                deferredPrompt = null
                                hasShownPrompt = true // Mark as shown to prevent re-prompting too soon
                            })
                        },
                    },
                    {
                        label: 'Not Now',
                        variant: 'subtle',
                        action() {
                            hasShownPrompt = true // User dismissed, consider it shown
                        }
                    }
                ],
            })
        }
    }

    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault()
        deferredPrompt = e
        // Optionally delay the first prompt a bit
        setTimeout(showInstallPrompt, 5000) 
    })

    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible' && deferredPrompt && !hasShownPrompt) {
            showInstallPrompt()
        }
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


