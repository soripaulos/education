<template>
  <div>
    <OfflineIndicator ref="offlineIndicator" />
    <div class="flex h-screen w-screen">
      <div class="h-full border-r bg-gray-50">
        <Sidebar />
      </div>
      <div class="flex-1 flex flex-col h-full overflow-auto">
        <Navbar />
        <router-view class="flex-1 overflow-auto" />
      </div>
    </div>
  </div>
  <Toasts />
</template>

<script setup>
import Sidebar from '@/components/Sidebar.vue'
import Navbar from '@/components/Navbar.vue'
import OfflineIndicator from '@/components/OfflineIndicator.vue'
import { RouterView } from 'vue-router'
import { Toasts } from 'frappe-ui'
import { ref } from 'vue'

// Reference to the offline indicator component
const offlineIndicator = ref(null)

// Expose the offline indicator to be accessible from other components
defineExpose({
  togglePwaControls: () => {
    offlineIndicator.value?.toggleControls()
  }
})
</script>
