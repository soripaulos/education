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

// create a pinia instance
let pinia = createPinia()
let app = createApp(App)

// Set up app
app.use(pinia)
app.use(router)
app.use(resourcesPlugin)

app.component('Button', Button)
app.component('Card', Card)
app.component('Input', Input)
app.component('VFrappeChart', VFrappeChart)

setConfig('resourceFetcher', frappeRequest)

// Import and use PWA store
import { usePwaStore } from './stores/pwa'

// Register service worker
if ('serviceWorker' in navigator) {
  // Initialize PWA store
  const pwaStore = usePwaStore()
  
  // Handle service worker registration
  window.addEventListener('load', () => {
    const swPath = '/assets/education/frontend/sw.js';
    navigator.serviceWorker
      .register(swPath, {
        scope: '/assets/education/frontend/'
      })
      .then(registration => {
        console.log('SW registered:', registration)
        
        // Store registration reference for later use
        pwaStore.setRegistration(registration)
        
        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing
          
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              toast({
                title: 'Update Available',
                message: 'A new version is available. Refresh to update.',
                duration: 10000,
                actions: [
                  {
                    label: 'Update Now',
                    variant: 'solid',
                    action() {
                      pwaStore.applyUpdate()
                    }
                  },
                  {
                    label: 'Later',
                    variant: 'subtle',
                    action() {
                      // Do nothing, toast will dismiss
                    }
                  }
                ]
              })
            }
          })
        })
        
        // Listen for successful login
        window.addEventListener('frappe-login-success', () => {
          registration.active?.postMessage('login_successful')
        })
        
        // Show ready toast
        toast({
          title: 'Ready for Offline Use',
          message: 'Student Portal can now work without internet',
          duration: 3000
        })
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
  
  // Initialize PWA functionality
  pwaStore.init()
  
  // Show install prompt after 5 seconds
  setTimeout(() => {
    pwaStore.showInstallPrompt()
  }, 5000)
}

router.isReady().then(() => {
  app.mount('#app')
})


