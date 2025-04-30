<template>
  <div class="relative">
    <router-link to="/notifications" class="flex items-center justify-center h-10 w-10 rounded-full hover:bg-gray-100">
      <FeatherIcon name="bell" class="h-5 w-5 text-gray-600" />
      <span 
        v-if="unreadCount > 0" 
        class="absolute -top-1 -right-1 flex items-center justify-center h-5 w-5 text-xs font-medium text-white bg-red-500 rounded-full"
      >
        {{ displayCount }}
      </span>
    </router-link>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import { FeatherIcon } from 'frappe-ui'

const unreadNotificationsCount = createResource({
  url: 'education.education.api.get_unread_notifications_count',
  cache: 'education:unread_notifications_count',
  initialData: 0,
  auto: true,
})

// Auto-refresh count every minute
onMounted(() => {
  const intervalId = setInterval(() => {
    unreadNotificationsCount.reload()
  }, 60000)

  return () => clearInterval(intervalId)
})

const unreadCount = computed(() => {
  return unreadNotificationsCount.data || 0
})

const displayCount = computed(() => {
  return unreadCount.value > 9 ? '9+' : unreadCount.value
})
</script> 