import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { toast } from 'frappe-ui'

export const usePwaStore = defineStore('pwa', () => {
  const isOnline = ref(navigator.onLine)
  const isUpdateAvailable = ref(false)
  const isInstalled = ref(false)
  const deferredPrompt = ref(null)
  const hasShownInstallPrompt = ref(false)
  
  // Registration reference
  const registration = ref(null)
  
  // Status computed properties
  const offlineMode = computed(() => !isOnline.value)
  const canInstall = computed(() => deferredPrompt.value !== null && !isInstalled.value)
  
  // Check if app is already installed
  const checkIfInstalled = () => {
    // Check if standalone or fullscreen display mode
    if (window.matchMedia('(display-mode: standalone)').matches || 
        window.matchMedia('(display-mode: fullscreen)').matches ||
        window.navigator.standalone === true) {
      isInstalled.value = true
    }
  }
  
  // Initialize PWA functionality
  const init = () => {
    // Set up online/offline detection
    window.addEventListener('online', () => {
      isOnline.value = true
      toast({
        title: 'Online Status',
        message: 'You are back online!',
        duration: 3000
      })
    })
    
    window.addEventListener('offline', () => {
      isOnline.value = false
      toast({
        title: 'Offline Mode',
        message: 'You are currently offline. Some features may be limited.',
        duration: 5000
      })
    })
    
    // Listen for beforeinstallprompt to capture install prompt
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault()
      deferredPrompt.value = e
    })
    
    // Listen for app installed event
    window.addEventListener('appinstalled', () => {
      isInstalled.value = true
      deferredPrompt.value = null
      toast({
        title: 'Installation Complete',
        message: 'The Student Portal has been successfully installed!',
        duration: 3000
      })
    })
    
    // Check if already installed
    checkIfInstalled()
    
    // Listen for service worker updates
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        isUpdateAvailable.value = true
      })
    }
  }
  
  // Show install prompt
  const showInstallPrompt = () => {
    if (deferredPrompt.value && !hasShownInstallPrompt.value) {
      toast({
        title: 'Install Student Portal',
        message: 'Get quick access and work offline',
        duration: 10000,
        actions: [
          {
            label: 'Install Now',
            variant: 'solid',
            action() {
              installApp()
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
      hasShownInstallPrompt.value = true
    }
  }
  
  // Install the PWA
  const installApp = async () => {
    if (deferredPrompt.value) {
      deferredPrompt.value.prompt()
      const choiceResult = await deferredPrompt.value.userChoice
      
      if (choiceResult.outcome === 'accepted') {
        toast({
          title: 'Successfully Installed',
          message: 'You can now access Student Portal from your home screen',
          duration: 5000
        })
        isInstalled.value = true
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
                  showInstallPrompt()
                }
              },
              {
                label: 'Maybe Later',
                variant: 'subtle',
                action() {
                  hasShownInstallPrompt.value = true
                }
              }
            ]
          })
        }, 60000)
      }
      
      deferredPrompt.value = null
    }
  }
  
  // Clear the cache
  const clearCache = async () => {
    if (registration.value && registration.value.active) {
      registration.value.active.postMessage('clear_cache')
      toast({
        title: 'Cache Cleared',
        message: 'Refreshing data from server...',
        duration: 3000
      })
    }
  }
  
  // Set registration reference
  const setRegistration = (reg) => {
    registration.value = reg
  }
  
  // Reload on update
  const applyUpdate = () => {
    if (registration.value && registration.value.waiting) {
      registration.value.waiting.postMessage({ type: 'SKIP_WAITING' })
    } else {
      window.location.reload()
    }
  }
  
  return {
    // State
    isOnline,
    isUpdateAvailable,
    isInstalled,
    deferredPrompt,
    offlineMode,
    canInstall,
    
    // Actions
    init,
    showInstallPrompt,
    installApp,
    clearCache,
    setRegistration,
    applyUpdate
  }
}) 