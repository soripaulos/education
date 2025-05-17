<template>
  <div class="min-h-screen bg-gray-50">
    <Sidebar />
    <main class="pt-16">
      <router-view class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"></router-view>
    </main>
    <Toasts />
  </div>
</template>

<script setup>
import Sidebar from '@/components/Sidebar.vue'
import { RouterView } from 'vue-router'
import { Toasts, toast } from 'frappe-ui'
import { onMounted } from 'vue'

onMounted(() => {
  // Setup handler for foreground push notifications
  if (window.frappePushNotification) {
    window.frappePushNotification.onMessage = (payload) => {
      console.log('Received foreground message:', payload)
      
      // Display toast notification
      toast({
        title: payload.data.reference_document_type || 'New Notification',
        message: payload.data.message || 'You have a new notification',
        duration: 5000,
        actions: [
          {
            label: 'View',
            variant: 'primary',
            action() {
              window.location.href = '/student-portal/notifications'
            }
          }
        ]
      })
    }
  }
})
</script>

<style>
#app {
  @apply antialiased text-gray-900;
}
</style>
