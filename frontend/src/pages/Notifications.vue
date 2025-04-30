<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader title="Notifications" :show-back-button="true" />
    
    <div class="max-w-3xl mx-auto px-4 py-6">
      <!-- Header with count and buttons -->
      <div class="flex items-center justify-between mb-6">
        <div class="text-lg font-medium text-gray-900" v-if="unreadNotificationsCount.data">
          {{ unreadNotificationsCount.data }} Unread
        </div>
        <div class="flex gap-2">
          <button 
            v-if="notifications.data?.length && unreadNotificationsCount.data"
            @click="markAllAsRead" 
            class="flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
          >
            <FeatherIcon name="check-circle" class="w-4 h-4 mr-1.5" />
            Mark all as read
          </button>
          
          <div class="relative" ref="dropdownRef">
            <button 
              v-if="notifications.data?.length"
              @click="toggleDropdown" 
              class="flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
            >
              <FeatherIcon name="more-horizontal" class="w-4 h-4 mr-1.5" />
              More actions
            </button>
            
            <div 
              v-if="showDropdown" 
              class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10"
            >
              <button 
                @click="deleteAllRead"
                class="w-full flex items-center px-4 py-2 text-sm text-left text-gray-700 hover:bg-gray-100"
              >
                <FeatherIcon name="trash-2" class="w-4 h-4 mr-2 text-gray-500" />
                Delete read notifications
              </button>
              <button 
                @click="deleteAll"
                class="w-full flex items-center px-4 py-2 text-sm text-left text-gray-700 hover:bg-gray-100"
              >
                <FeatherIcon name="trash" class="w-4 h-4 mr-2 text-gray-500" />
                Delete all notifications
              </button>
              <button 
                @click="exportNotifications"
                class="w-full flex items-center px-4 py-2 text-sm text-left text-gray-700 hover:bg-gray-100"
              >
                <FeatherIcon name="download" class="w-4 h-4 mr-2 text-gray-500" />
                Export notifications
              </button>
            </div>
          </div>
          
          <button 
            v-if="arePushNotificationsEnabled.data"
            @click="navigateToSettings" 
            class="flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
          >
            <FeatherIcon name="settings" class="w-4 h-4 mr-1.5" />
            Settings
          </button>
        </div>
      </div>
      
      <!-- Notification list -->
      <div class="bg-white rounded-lg shadow overflow-hidden" v-if="notifications.data?.length">
        <div 
          v-for="notification in notifications.data" 
          :key="notification.name"
          :class="[
            'flex items-start p-4 border-b border-gray-200 relative',
            notification.read ? 'bg-white' : 'bg-blue-50'
          ]"
        >
          <div 
            v-if="!notification.read" 
            class="absolute top-1/2 left-0 transform -translate-y-1/2 w-1 h-1/2 bg-blue-500 rounded-r-full"
          ></div>
          
          <UserAvatar :user-id="notification.from_user" class="mr-3 mt-0.5" />
          
          <div class="flex-1 min-w-0" @click="markAsRead(notification.name)">
            <div class="text-sm" v-html="notification.message"></div>
            <div class="mt-1 text-xs text-gray-500">
              {{ formatDate(notification.creation) }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- Empty state -->
      <div v-else class="text-center py-12">
        <FeatherIcon name="bell" class="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900">No notifications</h3>
        <p class="mt-1 text-sm text-gray-500">You don't have any notifications yet.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { createResource, createListResource } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { FeatherIcon } from 'frappe-ui'
import AppHeader from '../components/AppHeader.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { onMounted, ref, onUnmounted } from 'vue'

const router = useRouter()

// Resources
const unreadNotificationsCount = createResource({
  url: 'education.education.api.get_unread_notifications_count',
  cache: 'education:unread_notifications_count',
  initialData: 0,
  auto: true,
})

const notifications = createListResource({
  doctype: 'Student Notification',
  fields: [
    'name',
    'from_user',
    'message',
    'read',
    'creation',
    'reference_document_type',
    'reference_document_name',
  ],
  orderBy: 'creation desc',
  auto: true,
  cache: 'education:notifications',
  onSuccess() {
    unreadNotificationsCount.reload()
  },
})

const arePushNotificationsEnabled = createResource({
  url: 'education.education.api.are_push_notifications_enabled',
  cache: 'education:push_notifications_enabled',
  auto: true,
})

// Methods
function markAsRead(name) {
  const setValue = createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'Student Notification',
      name: name,
      fieldname: 'read',
      value: 1
    },
    onSuccess() {
      notifications.reload()
      unreadNotificationsCount.reload()
    }
  })
  
  setValue.submit()
}

function markAllAsRead() {
  const markAll = createResource({
    url: 'education.education.api.mark_all_notifications_as_read',
    onSuccess() {
      notifications.reload()
      unreadNotificationsCount.reload()
    }
  })
  
  markAll.submit()
}

function navigateToSettings() {
  router.push('/settings')
}

function formatDate(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  
  // For today's notifications, show the time
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
  }
  
  // For recent notifications (within 7 days), show the day
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))
  if (diffDays < 7) {
    return date.toLocaleDateString(undefined, { weekday: 'long' })
  }
  
  // For older notifications, show the date
  return date.toLocaleDateString()
}

function getItemRoute(item) {
  // Education-specific document types
  switch (item.reference_document_type) {
    case "Course":
      return {
        name: "CourseDetail",
        params: { id: item.reference_document_name }
      };
    case "Program":
      return {
        name: "ProgramDetail",
        params: { id: item.reference_document_name }
      };
    case "Student": 
      return {
        name: "StudentProfile",
        params: { id: item.reference_document_name }
      };
    case "Fee":
    case "Fees":
      return {
        name: "FeeDetail",
        params: { id: item.reference_document_name }
      };
    case "Assignment":
      return {
        name: "AssignmentDetail",
        params: { id: item.reference_document_name }
      };
    case "Examination":
    case "Exam":
      return {
        name: "ExamDetail",
        params: { id: item.reference_document_name }
      };
    case "Quiz":
    case "QuizActivity":
      return {
        name: "QuizDetail",
        params: { id: item.reference_document_name }
      };
    case "Student Attendance":
    case "Attendance":
      return {
        name: "Attendance"
      };
    case "Course Enrollment":
    case "Program Enrollment":
      return {
        name: "CourseDetail",
        params: { id: item.reference_document_name.split("-")[0].trim() }
      };
    default:
      // Default to home page if we don't know how to handle this type
      return { name: "Home" };
  }
}

// Add these new refs and functions
const dropdownRef = ref(null)
const showDropdown = ref(false)

// Toggle dropdown menu
function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

// Close dropdown when clicking outside
function handleClickOutside(event) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    showDropdown.value = false
  }
}

// Delete all read notifications
function deleteAllRead() {
  if (!confirm('Are you sure you want to delete all read notifications?')) return
  
  const deleteResource = createResource({
    url: 'education.education.api.delete_read_notifications',
    onSuccess() {
      notifications.reload()
      showDropdown.value = false
    }
  })
  
  deleteResource.submit()
}

// Delete all notifications
function deleteAll() {
  if (!confirm('Are you sure you want to delete ALL notifications?')) return
  
  const deleteResource = createResource({
    url: 'education.education.api.delete_all_notifications',
    onSuccess() {
      notifications.reload()
      unreadNotificationsCount.reload()
      showDropdown.value = false
    }
  })
  
  deleteResource.submit()
}

// Export notifications as CSV
function exportNotifications() {
  window.location.href = '/api/method/education.education.api.export_notifications'
  showDropdown.value = false
}

// Listen for clicks outside dropdown
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

// Clean up event listener
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script> 