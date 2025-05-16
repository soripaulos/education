<template>
  <span class="notification-badge" v-if="count > 0">
    {{ count }}
  </span>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'NotificationBadge',
  setup() {
    const count = ref(0)

    const updateCount = async () => {
      try {
        const response = await frappe.call({
          method: 'education.education.api.notifications.get_unread_count'
        })
        count.value = response.message.count
      } catch (error) {
        console.error('Failed to get notification count:', error)
      }
    }

    onMounted(() => {
      updateCount()
      // Update count every minute
      setInterval(updateCount, 60000)
    })

    return {
      count
    }
  }
}
</script>

<style scoped>
.notification-badge {
  background-color: #dc3545;
  color: white;
  border-radius: 50%;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  position: absolute;
  top: -5px;
  right: -5px;
}
</style> 