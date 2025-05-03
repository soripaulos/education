<template>
  <div>
    <!-- Offline indicator -->
    <div v-if="pwaStore.offlineMode" class="offline-banner">
      <div class="flex items-center space-x-2 px-4 py-2 bg-red-50 border-b border-red-100 text-red-700">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z" clip-rule="evenodd" />
        </svg>
        <span class="text-sm font-medium">You are currently offline</span>
      </div>
    </div>

    <!-- PWA update notification -->
    <div v-if="pwaStore.isUpdateAvailable" class="update-banner">
      <div class="flex items-center justify-between px-4 py-2 bg-blue-50 border-b border-blue-100 text-blue-700">
        <div class="flex items-center space-x-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
          </svg>
          <span class="text-sm font-medium">A new version is available</span>
        </div>
        <Button variant="subtle" @click="pwaStore.applyUpdate">Update Now</Button>
      </div>
    </div>

    <!-- Install prompt -->
    <div v-if="pwaStore.canInstall" class="install-banner hidden md:block">
      <div class="fixed bottom-4 right-4 p-4 bg-white rounded-lg shadow-lg max-w-sm z-50 border border-gray-100">
        <div class="flex items-start">
          <div class="flex-shrink-0">
            <img src="/favicon.png" class="h-10 w-10" alt="Logo" />
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-gray-900">Install Student Portal</h3>
            <p class="mt-1 text-sm text-gray-500">Install this app on your device for offline access and a better experience.</p>
            <div class="mt-2 flex space-x-2">
              <Button variant="solid" @click="pwaStore.installApp">Install</Button>
              <Button variant="subtle" @click="dismissInstall">Not Now</Button>
            </div>
          </div>
          <button type="button" class="ml-2" @click="dismissInstall">
            <svg class="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- PWA control panel in settings (can be toggled) -->
    <div v-if="showControls" class="pwa-controls p-4 bg-gray-50 rounded-lg mb-4">
      <h3 class="text-lg font-medium text-gray-900 mb-3">App Status</h3>
      
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-700">Offline Mode</p>
            <p class="text-sm text-gray-500">{{ pwaStore.offlineMode ? 'You are offline' : 'You are online' }}</p>
          </div>
          <div class="h-6 w-6 rounded-full" :class="pwaStore.offlineMode ? 'bg-red-500' : 'bg-green-500'"></div>
        </div>
        
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-700">Installation Status</p>
            <p class="text-sm text-gray-500">{{ pwaStore.isInstalled ? 'App is installed' : 'App not installed' }}</p>
          </div>
          <Button v-if="!pwaStore.isInstalled && pwaStore.canInstall" @click="pwaStore.installApp">
            Install App
          </Button>
          <span v-else-if="pwaStore.isInstalled" class="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-md">
            Installed
          </span>
          <span v-else class="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-md">
            Not Available
          </span>
        </div>
        
        <div>
          <Button block @click="pwaStore.clearCache">Clear Cache</Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { usePwaStore } from '../stores/pwa'

const pwaStore = usePwaStore()
const showControls = ref(false)

// Method to dismiss the install banner
const dismissInstall = () => {
  const installBanner = document.querySelector('.install-banner')
  if (installBanner) {
    installBanner.style.display = 'none'
  }
}

// Function to toggle controls visibility
const toggleControls = () => {
  showControls.value = !showControls.value
}

// Export component methods
defineExpose({
  toggleControls
})
</script>

<style scoped>
.offline-banner, .update-banner {
  position: sticky;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
}
</style> 