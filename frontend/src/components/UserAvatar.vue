<template>
  <div class="relative">
    <div
      v-if="!avatarUrl && !loading"
      class="flex items-center justify-center rounded-full bg-gray-200"
      :class="sizeClasses[size]"
    >
      <span class="text-gray-500 font-medium" :class="textClasses[size]">
        {{ userInitials }}
      </span>
    </div>
    <img
      v-if="avatarUrl"
      :src="avatarUrl"
      class="rounded-full object-cover"
      :class="sizeClasses[size]"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { createResource } from 'frappe-ui'

const props = defineProps({
  userId: {
    type: String,
    required: true,
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value),
  },
})

const sizeClasses = {
  sm: 'h-8 w-8',
  md: 'h-10 w-10',
  lg: 'h-12 w-12',
}

const textClasses = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
}

const loading = ref(true)
const avatarUrl = ref(null)
const userInitials = ref('')

// Create a resource to fetch user information
const userInfo = createResource({
  url: 'frappe.client.get',
  params: {
    doctype: 'User',
    name: props.userId,
    fields: ['full_name', 'user_image'],
  },
  auto: false,
  onSuccess(data) {
    if (data?.user_image) {
      avatarUrl.value = data.user_image
    } else {
      const fullName = data?.full_name || ''
      const nameParts = fullName.split(' ')
      
      if (nameParts.length >= 2) {
        userInitials.value = `${nameParts[0][0]}${nameParts[1][0]}`
      } else if (nameParts.length === 1 && nameParts[0]) {
        userInitials.value = nameParts[0][0]
      } else {
        userInitials.value = props.userId ? props.userId[0].toUpperCase() : '?'
      }
    }
    loading.value = false
  },
  onError() {
    userInitials.value = props.userId ? props.userId[0].toUpperCase() : '?'
    loading.value = false
  },
})

// Fetch user info when component is mounted
onMounted(() => {
  if (props.userId) {
    userInfo.submit()
  }
})

// Watch for changes in userId
watch(() => props.userId, (newVal) => {
  if (newVal) {
    loading.value = true
    avatarUrl.value = null
    userInitials.value = ''
    userInfo.params.name = newVal
    userInfo.submit()
  }
})
</script> 