<template>
  <div 
    v-if="isVisible && banner.message" 
    :class="[
      'fixed w-full top-0 z-50 px-4 py-3 flex items-center justify-between shadow-md',
      bannerColorClass
    ]"
  >
    <div class="flex items-center">
      <FeatherIcon 
        :name="banner.icon || 'info'" 
        class="w-5 h-5 mr-3" 
        :class="textColorClass" 
      />
      <div>
        <div class="font-medium" :class="textColorClass">
          {{ banner.title || 'Notification' }}
        </div>
        <div class="text-sm" :class="textColorClass" v-html="banner.message"></div>
      </div>
    </div>
    
    <div class="flex items-center space-x-2">
      <button 
        v-if="banner.actionText && banner.actionUrl"
        @click="handleAction"
        class="px-3 py-1 rounded-md text-sm font-medium"
        :class="actionButtonClass"
      >
        {{ banner.actionText }}
      </button>
      
      <button 
        @click="dismiss" 
        class="p-1 rounded-full hover:bg-opacity-10"
        :class="dismissButtonClass"
      >
        <FeatherIcon name="x" class="w-5 h-5" :class="textColorClass" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { FeatherIcon } from 'frappe-ui'

const router = useRouter()
const isVisible = ref(false)
const banner = ref({
  type: 'info',
  title: '',
  message: '',
  icon: 'info',
  actionText: '',
  actionUrl: '',
  dismissable: true,
  autoDismiss: 0, // seconds, 0 = no auto dismiss
})

// Banner style classes based on type
const bannerColorClass = computed(() => {
  switch (banner.value.type) {
    case 'success':
      return 'bg-green-100'
    case 'warning':
      return 'bg-yellow-100'
    case 'error':
      return 'bg-red-100'
    case 'info':
    default:
      return 'bg-blue-100'
  }
})

const textColorClass = computed(() => {
  switch (banner.value.type) {
    case 'success':
      return 'text-green-700'
    case 'warning':
      return 'text-yellow-700'
    case 'error':
      return 'text-red-700'
    case 'info':
    default:
      return 'text-blue-700'
  }
})

const actionButtonClass = computed(() => {
  switch (banner.value.type) {
    case 'success':
      return 'bg-green-700 text-white hover:bg-green-800'
    case 'warning':
      return 'bg-yellow-700 text-white hover:bg-yellow-800'
    case 'error':
      return 'bg-red-700 text-white hover:bg-red-800'
    case 'info':
    default:
      return 'bg-blue-700 text-white hover:bg-blue-800'
  }
})

const dismissButtonClass = computed(() => {
  switch (banner.value.type) {
    case 'success':
      return 'hover:bg-green-200'
    case 'warning':
      return 'hover:bg-yellow-200'
    case 'error':
      return 'hover:bg-red-200'
    case 'info':
    default:
      return 'hover:bg-blue-200'
  }
})

// Load active banner on component mount
onMounted(() => {
  loadBanner()
})

// Fetch active banner from server
const loadBanner = () => {
  const bannerResource = createResource({
    url: 'education.education.api.get_active_banner',
    onSuccess(data) {
      if (data && data.message) {
        banner.value = {
          type: data.type || 'info',
          title: data.title || 'Notification',
          message: data.message,
          icon: data.icon || 'info',
          actionText: data.action_text || '',
          actionUrl: data.action_url || '',
          dismissable: data.dismissable !== false,
          autoDismiss: data.auto_dismiss || 0,
        }
        isVisible.value = true
        
        // Set up auto-dismiss if configured
        if (banner.value.autoDismiss > 0) {
          setTimeout(() => {
            dismiss()
          }, banner.value.autoDismiss * 1000)
        }
      }
    }
  })
  
  bannerResource.submit()
}

// Auto-dismiss after specified time
watch(() => banner.value.autoDismiss, (newVal) => {
  if (newVal > 0 && isVisible.value) {
    setTimeout(() => {
      dismiss()
    }, newVal * 1000)
  }
})

// Handle action button click
function handleAction() {
  if (banner.value.actionUrl) {
    // Check if it's an internal route or external URL
    if (banner.value.actionUrl.startsWith('http')) {
      window.open(banner.value.actionUrl, '_blank')
    } else {
      router.push(banner.value.actionUrl)
    }
  }
  
  if (banner.value.dismissable) {
    dismiss()
  }
}

// Dismiss the banner
function dismiss() {
  isVisible.value = false
  
  // If we have a banner ID, mark it as dismissed for this user
  if (banner.value.id) {
    const dismissResource = createResource({
      url: 'education.education.api.dismiss_banner',
      params: {
        banner_id: banner.value.id
      }
    })
    
    dismissResource.submit()
  }
}
</script> 