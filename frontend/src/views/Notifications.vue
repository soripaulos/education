<template>
  <div class="notifications-page">
    <div class="notifications-header">
      <h1>Notifications</h1>
      <div class="notifications-actions">
        <button 
          v-if="!notificationsEnabled" 
          @click="enableNotifications"
          class="btn btn-primary"
        >
          Enable Notifications
        </button>
        <button 
          v-else 
          @click="disableNotifications"
          class="btn btn-secondary"
        >
          Disable Notifications
        </button>
      </div>
    </div>

    <div class="notifications-list">
      <div v-if="loading" class="loading-state">
        Loading notifications...
      </div>
      <div v-else-if="notifications.length === 0" class="empty-state">
        No notifications yet
      </div>
      <div v-else class="notification-items">
        <div 
          v-for="notification in notifications" 
          :key="notification.name"
          class="notification-item"
          :class="{ unread: !notification.read }"
          @click="handleNotificationClick(notification)"
        >
          <div class="notification-content">
            <div class="notification-message" v-html="notification.message"></div>
            <div class="notification-meta">
              <span class="notification-time">
                {{ formatDate(notification.creation) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { formatDate } from '@/utils/date'

export default {
  name: 'Notifications',
  setup() {
    const router = useRouter()
    const loading = ref(true)
    const notificationsEnabled = ref(false)
    const notifications = ref([])

    const fetchNotifications = async () => {
      try {
        const response = await frappe.call({
          method: 'frappe.client.get_list',
          args: {
            doctype: 'PWA Notification',
            fields: ['name', 'message', 'read', 'creation', 'reference_document_type', 'reference_document_name'],
            filters: [['to_user', '=', frappe.session.user]],
            order_by: 'creation desc'
          }
        })
        notifications.value = response.message || []
      } catch (error) {
        console.error('Failed to fetch notifications:', error)
      } finally {
        loading.value = false
      }
    }

    const enableNotifications = async () => {
      try {
        if (window.frappePushNotification) {
          await window.frappePushNotification.enableNotification()
          notificationsEnabled.value = true
        } else {
          console.error('Push notification service not initialized')
        }
      } catch (error) {
        console.error('Failed to enable notifications:', error)
      }
    }

    const disableNotifications = async () => {
      try {
        if (window.frappePushNotification) {
          await window.frappePushNotification.disableNotification()
          notificationsEnabled.value = false
        } else {
          console.error('Push notification service not initialized')
        }
      } catch (error) {
        console.error('Failed to disable notifications:', error)
      }
    }

    const handleNotificationClick = async (notification) => {
      if (!notification.read) {
        await frappe.call({
          method: 'education.education.api.notifications.mark_as_read',
          args: {
            notification_name: notification.name
          }
        })
        notification.read = 1
      }

      if (notification.reference_document_type && notification.reference_document_name) {
        // Handle navigation based on document type
        if (notification.reference_document_type === 'Course') {
          router.push({
            name: 'Course',
            params: { id: notification.reference_document_name }
          })
        } else if (notification.reference_document_type === 'Assignment') {
          router.push({
            name: 'Assignment',
            params: { id: notification.reference_document_name }
          })
        } else {
          // Generic fallback for other document types
          router.push({
            path: `/app/${notification.reference_document_type.toLowerCase()}/${notification.reference_document_name}`
          })
        }
      }
    }

    const checkNotificationPermission = async () => {
      if (window.frappePushNotification) {
        notificationsEnabled.value = await window.frappePushNotification.isNotificationEnabled()
      }
    }

    onMounted(() => {
      fetchNotifications()
      checkNotificationPermission()
    })

    return {
      loading,
      notifications,
      notificationsEnabled,
      enableNotifications,
      disableNotifications,
      handleNotificationClick,
      formatDate
    }
  }
}
</script>

<style scoped>
.notifications-page {
  padding: 1rem;
}

.notifications-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.notification-item {
  padding: 1rem;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}

.notification-item.unread {
  background-color: #f8f9fa;
}

.notification-message {
  margin-bottom: 0.5rem;
}

.notification-meta {
  font-size: 0.875rem;
  color: #6c757d;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 2rem;
  color: #6c757d;
}
</style> 