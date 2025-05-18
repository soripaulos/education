<template>
  <div class="p-4 border rounded-lg shadow-sm bg-white">
    <h2 class="text-lg font-semibold mb-3">Push Notifications</h2>
    <div v.if="notificationStore.permissionStatus === 'denied'" class="text-red-600 mb-3">
      Notification permission has been denied. Please enable it in your browser settings.
    </div>
    <div v.else-if="!isPushSupported" class="text-yellow-600 mb-3">
      Push notifications are not fully supported by your browser or the VAPID key is missing.
    </div>
    <div v.else class="flex items-center justify-between">
      <span>Enable Push Notifications</span>
      <ToggleSwitch 
        :modelValue="notificationStore.isSubscribed"
        @update:modelValue="handleToggle"
        :disabled="notificationStore.permissionStatus === 'denied' || isLoading"
      />
    </div>
    <p v.if="isLoading" class="text-sm text-gray-500 mt-2">Processing...</p>
    <p v.if="notificationStore.error" class="text-sm text-red-500 mt-2">Error: {{ notificationStore.error }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useNotificationStore } from '@/stores/notifications';
import { ToggleSwitch } from 'frappe-ui'; // Assuming frappe-ui has a ToggleSwitch

const notificationStore = useNotificationStore();
const isLoading = ref(false);

const isPushSupported = computed(() => {
  return ('serviceWorker' in navigator) && ('PushManager' in window) && notificationStore.VAPID_PUBLIC_KEY;
});

onMounted(async () => {
  // Initialize will fetch VAPID key and check current subscription state
  if (isPushSupported.value) {
    isLoading.value = true;
    await notificationStore.initialize();
    isLoading.value = false;
  }
});

async function handleToggle(value) {
  isLoading.value = true;
  if (value) {
    if (notificationStore.permissionStatus === 'default') {
      await notificationStore.requestPermissionAndSubscribe();
    } else if (notificationStore.permissionStatus === 'granted') {
      await notificationStore.subscribe();
    }
  } else {
    await notificationStore.unsubscribe();
  }
  isLoading.value = false;
}
</script> 