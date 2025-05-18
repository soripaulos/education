<template>
  <div class="notification-settings p-4 border rounded-md shadow-sm">
    <h3 class="text-lg font-medium mb-3">Push Notifications</h3>
    <div class="flex items-center justify-between">
      <label for="notification-toggle" class="mr-2 text-gray-700">
        Enable Push Notifications
      </label>
      <div :class="['toggle-switch', { 'active': notificationsEnabled }]" @click="toggleNotifications">
        <div class="toggle-knob"></div>
      </div>
    </div>
    <p v-if="statusMessage" :class="['mt-2 text-sm', statusType === 'error' ? 'text-red-500' : 'text-green-500']">
      {{ statusMessage }}
    </p>
     <p class="mt-2 text-xs text-gray-500">
      Receive updates and important announcements directly on your device.
    </p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { toast } from 'frappe-ui'; // Assuming frappe-ui toast is available

const notificationsEnabled = ref(false);
const statusMessage = ref('');
const statusType = ref(''); // 'success' or 'error'

const getPushManager = () => {
  // Access the global instance initialized in main.js
  return window.educationPushNotification;
};

onMounted(async () => {
  const attemptInitialization = () => {
    const pushManager = getPushManager(); // window.educationPushNotification
    if (pushManager && typeof pushManager.isNotificationEnabled === 'function') {
      notificationsEnabled.value = pushManager.isNotificationEnabled();
      if (pushManager.initialized) { // Check if it was fully initialized
        statusMessage.value = 'Push notification system ready.';
        statusType.value = 'success';
      } else {
        // This case might occur if it's on window but initialize() failed internally due to no config
        statusMessage.value = 'Push notification system found but not fully initialized. Check console for errors in main.js.';
        statusType.value = 'error';
         console.warn('educationPushNotification manager IS ON WINDOW but NOT INITIALIZED.');
      }
      return true; // Successfully found and processed
    }
    return false; // Not found or not ready
  };

  if (!attemptInitialization()) {
    // If not found immediately, wait a bit and try once more,
    // as SW registration and async setup in main.js might take a moment.
    setTimeout(() => {
      if (!attemptInitialization()) {
        statusMessage.value = 'Push notification system not available or failed to initialize. Please check browser console for errors (especially in main.js or FrappePushNotification setup).';
        statusType.value = 'error';
        console.warn('educationPushNotification manager not found after delay. System may not have initialized correctly in main.js.');
      }
    }, 2000); // Wait 2 seconds
  }
});

const toggleNotifications = async () => {
  const pushManager = getPushManager();
  if (!pushManager) {
    toast({ title: 'Error', message: 'Push notification system not initialized.', type: 'error' });
    statusMessage.value = 'Push notification system not initialized.';
    statusType.value = 'error';
    return;
  }

  statusMessage.value = ''; // Clear previous status

  if (!notificationsEnabled.value) { // Current state is false, so user wants to enable
    try {
      toast({ title: 'Enabling Notifications...', message: 'Please grant permission if prompted.' });
      const result = await pushManager.enableNotification();
      if (result.permission_granted) {
        notificationsEnabled.value = true;
        statusMessage.value = 'Push notifications enabled successfully!';
        statusType.value = 'success';
        toast({ title: 'Success', message: 'Push notifications enabled!', type: 'success' });
      } else {
        notificationsEnabled.value = false; // Ensure toggle reflects actual state
        statusMessage.value = 'Permission denied or failed to enable notifications.';
        statusType.value = 'error';
        toast({ title: 'Failed', message: 'Could not enable push notifications. Permission might have been denied.', type: 'warning' });
      }
    } catch (error) {
      notificationsEnabled.value = false; // Ensure toggle reflects actual state
      console.error('Error enabling notifications:', error);
      statusMessage.value = `Error: ${error.message || 'Failed to enable notifications.'}`;
      statusType.value = 'error';
      toast({ title: 'Error', message: `Failed to enable: ${error.message}`, type: 'error' });
    }
  } else { // Current state is true, so user wants to disable
    try {
      toast({ title: 'Disabling Notifications...', message: 'Please wait.' });
      await pushManager.disableNotification();
      notificationsEnabled.value = false;
      statusMessage.value = 'Push notifications disabled.';
      statusType.value = 'success';
      toast({ title: 'Success', message: 'Push notifications disabled.', type: 'info' });
    } catch (error) {
      // notificationsEnabled.value might still be true if disable failed, UX decision here
      console.error('Error disabling notifications:', error);
      statusMessage.value = `Error: ${error.message || 'Failed to disable notifications.'}`;
      statusType.value = 'error';
      toast({ title: 'Error', message: `Failed to disable: ${error.message}`, type: 'error' });
    }
  }
};
</script>

<style scoped>
.toggle-switch {
  width: 50px;
  height: 28px;
  background-color: #ccc;
  border-radius: 14px;
  position: relative;
  cursor: pointer;
  transition: background-color 0.2s;
}

.toggle-switch.active {
  background-color: #4F46E5; /* Indigo, or your theme color */
}

.toggle-knob {
  width: 24px;
  height: 24px;
  background-color: white;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
}

.toggle-switch.active .toggle-knob {
  transform: translateX(22px);
}
</style> 