<template>
  <header class="bg-white shadow-sm border-b">
    <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
      <!-- Left side: Back button and title -->
      <div class="flex items-center space-x-3">
        <button 
          v-if="showBackButton" 
          @click="goBack" 
          class="p-1.5 text-gray-500 rounded-full hover:bg-gray-100"
        >
          <FeatherIcon name="arrow-left" class="w-5 h-5" />
        </button>
        
        <h1 class="text-lg font-medium text-gray-900">{{ title }}</h1>
      </div>
      
      <!-- Right side: Notification bell and optional actions -->
      <div class="flex items-center space-x-2">
        <slot name="actions"></slot>
        <NotificationBell v-if="showNotifications" />
      </div>
    </div>
  </header>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { FeatherIcon } from 'frappe-ui'
import NotificationBell from './NotificationBell.vue'

const router = useRouter()

defineProps({
  title: {
    type: String,
    required: true
  },
  showBackButton: {
    type: Boolean,
    default: false
  },
  showNotifications: {
    type: Boolean,
    default: true
  }
})

function goBack() {
  router.back()
}
</script> 