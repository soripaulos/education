<template>
  <div class="min-h-screen bg-gray-50">
    <Sidebar />
    <main class="pt-16">
      <NotificationBanner />
      <router-view class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"></router-view>
    </main>
    <Toasts />
  </div>
</template>

<script setup>
import Sidebar from '@/components/Sidebar.vue'
import { RouterView } from 'vue-router'
import { Toasts } from 'frappe-ui'
import { onMounted } from 'vue'
import { initPushNotifications, setupNotificationClickHandler } from './utils/pushNotifications'
import NotificationBanner from './components/NotificationBanner.vue'

// Initialize push notification handling when the app loads
onMounted(async () => {
  // Initialize push notifications
  await initPushNotifications()
  
  // Set up handler for notification clicks
  setupNotificationClickHandler()
})
</script>

<style>
#app {
  @apply antialiased text-gray-900;
}
</style>
