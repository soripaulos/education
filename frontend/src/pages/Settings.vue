<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader title="Settings" :show-back-button="true" />
    
    <div class="max-w-3xl mx-auto px-4 py-6">
      <div class="bg-white rounded-lg shadow overflow-hidden">
        <!-- Notification settings -->
        <div class="p-4 border-b">
          <h2 class="text-lg font-medium text-gray-900 mb-4">Notifications</h2>
          
          <div class="space-y-4">
            <div>
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-base font-medium text-gray-900">Push notifications</h3>
                  <p class="text-sm text-gray-500">
                    Receive notifications on your device when important updates happen
                  </p>
                  <p v-if="pushSettingsDisabled" class="mt-1 text-xs text-red-500">
                    Push notifications have been disabled on your site
                  </p>
                </div>
                
                <label class="relative inline-flex items-center cursor-pointer">
                  <input 
                    type="checkbox" 
                    :checked="pushNotificationState"
                    @change="togglePushNotifications"
                    :disabled="pushSettingsDisabled || isLoading"
                    class="sr-only peer"
                  >
                  <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 peer-disabled:opacity-50"></div>
                </label>
              </div>
            </div>
            
            <div v-if="pushNotificationState && !pushSettingsDisabled" class="mt-2">
              <button 
                @click="testNotification"
                class="px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-800"
              >
                Send test notification
              </button>
            </div>
            
            <div>
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-base font-medium text-gray-900">Email notifications</h3>
                  <p class="text-sm text-gray-500">
                    Receive email notifications for important updates
                  </p>
                </div>
                
                <label class="relative inline-flex items-center cursor-pointer">
                  <input 
                    type="checkbox" 
                    :checked="emailNotificationState"
                    @change="toggleEmailNotifications"
                    class="sr-only peer"
                  >
                  <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>
          </div>
        </div>
        
        <!-- App settings -->
        <div class="p-4">
          <h2 class="text-lg font-medium text-gray-900 mb-4">Application</h2>
          
          <div class="space-y-4">
            <div>
              <h3 class="text-base font-medium text-gray-900">App version</h3>
              <p class="text-sm text-gray-500">{{ appVersion }}</p>
            </div>
            
            <button 
              @click="clearCache"
              class="w-full flex items-center justify-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <FeatherIcon name="refresh-cw" class="w-4 h-4 mr-1.5" />
              Clear app cache
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'
import { FeatherIcon } from 'frappe-ui'
import AppHeader from '../components/AppHeader.vue'

// App settings
const appVersion = ref('1.0.0')

// Push notification settings
const pushNotificationState = ref(false)
const emailNotificationState = ref(false)
const isLoading = ref(false)

// Check if push notifications are enabled
const arePushNotificationsEnabled = createResource({
  url: 'education.education.api.are_push_notifications_enabled',
  cache: 'education:push_notifications_enabled',
  auto: true,
})

// Check the current user notification settings
const userNotificationSettings = createResource({
  url: 'frappe.client.get',
  params: {
    doctype: 'User Notification Settings',
    name: 'current'
  },
  auto: true,
  onSuccess(data) {
    if (data) {
      emailNotificationState.value = data.enabled || false
      // Setup push notification state based on browser permissions
      checkPushPermission()
    }
  }
})

const pushSettingsDisabled = computed(() => {
  return !(window.frappe?.boot.push_relay_server_url && arePushNotificationsEnabled.data)
})

function checkPushPermission() {
  // Check current permission
  if ('Notification' in window) {
    pushNotificationState.value = Notification.permission === 'granted'
  }
}

function togglePushNotifications(event) {
  if (pushSettingsDisabled.value) return
  
  const newValue = event.target.checked
  isLoading.value = true
  
  if (newValue) {
    requestPushPermission()
  } else {
    disablePushNotifications()
  }
}

function requestPushPermission() {
  // Show explanation before requesting
  const confirmed = confirm(
    "To receive push notifications about your courses, assignments, and other important updates, you need to allow this site to send notifications. Would you like to enable notifications?"
  )
  
  if (confirmed) {
    if (window.frappePushNotification) {
      // Use Frappe's push notification system if available
      window.frappePushNotification.enableNotification()
        .then(result => {
          if (result.permission_granted) {
            pushNotificationState.value = true
            showToast('Push notifications enabled', 'success')
            
            // Register token with our system
            if (result.token) {
              registerTokenWithServer(result.token)
            }
          } else {
            pushNotificationState.value = false
            showToast('Permission denied for push notifications', 'error')
          }
        })
        .catch(error => {
          console.error('Error enabling push notifications:', error)
          pushNotificationState.value = false
          showToast('Failed to enable push notifications', 'error')
        })
        .finally(() => {
          isLoading.value = false
        })
    } else {
      // Use our custom implementation
      if ('Notification' in window) {
        Notification.requestPermission().then(permission => {
          if (permission === 'granted') {
            pushNotificationState.value = true
            showToast('Push notifications enabled', 'success')
          } else {
            pushNotificationState.value = false
            showToast('Permission denied for push notifications', 'error')
          }
          isLoading.value = false
        })
      } else {
        pushNotificationState.value = false
        showToast('Push notifications not supported in this browser', 'error')
        isLoading.value = false
      }
    }
  } else {
    pushNotificationState.value = false
    isLoading.value = false
  }
}

function registerTokenWithServer(token) {
  // Register token with our backend
  const registerToken = createResource({
    url: 'education.education.api.register_notification_token',
    params: {
      token: token
    },
    onSuccess(data) {
      console.log('Token registered successfully')
    },
    onError(error) {
      console.error('Failed to register token:', error)
    }
  })
  
  registerToken.submit()
}

function disablePushNotifications() {
  // We can't revoke permissions, but we can show a message
  showToast('To disable notifications, use your browser settings', 'info')
  pushNotificationState.value = (Notification.permission === 'granted')
  isLoading.value = false
}

function toggleEmailNotifications(event) {
  const newValue = event.target.checked
  
  const updateSettings = createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'User Notification Settings',
      name: 'current',
      fieldname: 'enabled',
      value: newValue
    },
    onSuccess() {
      emailNotificationState.value = newValue
      showToast('Email notification settings updated', 'success')
    },
    onError() {
      emailNotificationState.value = !newValue // Revert
      showToast('Failed to update email notification settings', 'error')
    }
  })
  
  updateSettings.submit()
}

function clearCache() {
  // Clear local storage cache
  const keys = Object.keys(localStorage)
  for (const key of keys) {
    if (key.startsWith('education:')) {
      localStorage.removeItem(key)
    }
  }
  
  // Reload app
  window.location.reload()
}

function showToast(message, type = 'info') {
  const toast = {
    title: type === 'success' ? 'Success' : type === 'error' ? 'Error' : 'Information',
    text: message,
    icon: type === 'success' ? 'check-circle' : type === 'error' ? 'alert-circle' : 'info',
    position: 'bottom-center',
    iconClasses: type === 'success' ? 'text-green-500' : type === 'error' ? 'text-red-500' : 'text-blue-500',
  }
  
  if (window.frappe?.ui?.Toast) {
    window.frappe.ui.Toast(toast)
  } else {
    alert(message) // Fallback if toast component is not available
  }
}

// Add a function to test notifications
function testNotification() {
  const testNotification = createResource({
    url: 'education.education.api.send_test_notification',
    onSuccess(data) {
      if (data.success) {
        showToast('Test notification sent', 'success')
      } else {
        showToast(data.message || 'Failed to send test notification', 'error')
      }
    },
    onError() {
      showToast('Failed to send test notification', 'error')
    }
  })
  
  testNotification.submit()
}
</script> 