<template>
    <div class="p-4">
        <h1 class="text-2xl font-bold mb-6">Settings</h1>

        <div class="space-y-6">
            <!-- Push Notifications Section -->
            <div class="bg-white p-6 rounded-lg shadow">
                <h2 class="text-lg font-medium mb-4">Push Notifications</h2>
                
                <div v-if="!window.frappe?.boot.push_relay_server_url" class="text-yellow-600 mb-4">
                    Push notifications are not configured for this site.
                </div>

                <div v-else class="flex items-center justify-between">
                    <div>
                        <h3 class="font-medium">Enable Push Notifications</h3>
                        <p class="text-sm text-gray-600 mt-1">
                            Receive notifications even when the app is closed
                        </p>
                    </div>
                    <div class="flex items-center">
                        <button
                            v-if="isLoading"
                            class="w-12 h-6 bg-gray-200 rounded-full p-1 duration-300 ease-in-out"
                            disabled
                        >
                            <div class="bg-white w-4 h-4 rounded-full shadow-md transform duration-300"></div>
                        </button>
                        <button
                            v-else
                            @click="togglePushNotifications"
                            class="w-12 h-6 rounded-full p-1 duration-300 ease-in-out"
                            :class="pushNotificationState ? 'bg-blue-500' : 'bg-gray-200'"
                        >
                            <div
                                class="bg-white w-4 h-4 rounded-full shadow-md transform duration-300"
                                :class="pushNotificationState ? 'translate-x-6' : ''"
                            ></div>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useNotificationsStore } from '../stores/notifications';

const store = useNotificationsStore();
const isLoading = ref(false);
const pushNotificationState = ref(false);

onMounted(async () => {
    await store.checkPushNotificationsEnabled();
    pushNotificationState.value = window.frappePushNotification?.isNotificationEnabled() || false;
});

async function togglePushNotifications() {
    if (isLoading.value) return;
    
    isLoading.value = true;
    try {
        if (!pushNotificationState.value) {
            await window.frappePushNotification.enableNotification();
            pushNotificationState.value = true;
        } else {
            await window.frappePushNotification.disableNotification();
            pushNotificationState.value = false;
        }
    } catch (error) {
        console.error('Failed to toggle push notifications:', error);
        // Revert state on error
        pushNotificationState.value = window.frappePushNotification?.isNotificationEnabled() || false;
    } finally {
        isLoading.value = false;
    }
}
</script> 