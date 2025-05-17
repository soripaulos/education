<template>
    <div class="p-4">
        <div class="flex justify-between items-center mb-4">
            <h1 class="text-2xl font-bold">Notifications</h1>
            <div class="flex gap-2">
                <button
                    v-if="notifications.length > 0"
                    @click="markAllAsRead"
                    class="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
                >
                    Mark all as read
                </button>
                <button
                    v-if="allowPushNotifications"
                    @click="$router.push('/settings')"
                    class="px-4 py-2 text-sm bg-blue-500 text-white hover:bg-blue-600 rounded"
                >
                    Push Notification Settings
                </button>
            </div>
        </div>

        <div v-if="isLoading" class="flex justify-center items-center h-32">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>

        <div v-else-if="notifications.length === 0" class="text-center py-8 text-gray-500">
            No notifications yet
        </div>

        <div v-else class="space-y-4">
            <div
                v-for="notification in notifications"
                :key="notification.name"
                class="p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
                :class="{ 'opacity-75': notification.read }"
            >
                <div class="flex justify-between items-start">
                    <div>
                        <h3 class="font-medium">{{ notification.reference_document_type || 'Notification' }}</h3>
                        <p class="text-gray-600 mt-1">{{ notification.message }}</p>
                        <p v-if="notification.reference_document_name" class="text-sm text-blue-600 mt-1">
                            {{ notification.reference_document_name }}
                        </p>
                        <p class="text-sm text-gray-500 mt-2">
                            {{ formatDate(notification.creation) }}
                        </p>
                    </div>
                    <button
                        v-if="!notification.read"
                        @click="markAsRead(notification.name)"
                        class="text-sm text-blue-500 hover:text-blue-600"
                    >
                        Mark as read
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useNotificationsStore } from '../stores/notifications';
import { formatDate } from '../utils/date';

const store = useNotificationsStore();
const {
    notifications,
    isLoading,
    allowPushNotifications,
    fetchNotifications,
    markAsRead,
    markAllAsRead
} = store;

onMounted(async () => {
    await fetchNotifications();
});
</script> 