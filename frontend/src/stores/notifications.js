import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useNotificationsStore = defineStore('notifications', () => {
    const notifications = ref([]);
    const unreadCount = ref(0);
    const isLoading = ref(false);

    const arePushNotificationsEnabled = ref(false);

    // Computed property to check if push notifications are available
    const allowPushNotifications = computed(() => {
        return window.frappe?.boot.push_relay_server_url && arePushNotificationsEnabled.value;
    });

    // Fetch notifications
    async function fetchNotifications() {
        isLoading.value = true;
        try {
            const response = await fetch('/api/method/education.api.get_notifications');
            const data = await response.json();
            notifications.value = data.message;
            unreadCount.value = notifications.value.filter(n => !n.read).length;
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
        } finally {
            isLoading.value = false;
        }
    }

    // Mark notification as read
    async function markAsRead(notificationId) {
        try {
            await fetch(`/api/method/education.api.mark_notification_as_read?notification_id=${notificationId}`);
            const notification = notifications.value.find(n => n.name === notificationId);
            if (notification && !notification.read) {
                notification.read = true;
                unreadCount.value--;
            }
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
        }
    }

    // Mark all notifications as read
    async function markAllAsRead() {
        try {
            await fetch('/api/method/education.api.mark_all_notifications_as_read');
            notifications.value.forEach(n => n.read = true);
            unreadCount.value = 0;
        } catch (error) {
            console.error('Failed to mark all notifications as read:', error);
        }
    }

    // Check if push notifications are enabled
    async function checkPushNotificationsEnabled() {
        try {
            const response = await fetch('/api/method/education.api.are_push_notifications_enabled');
            const data = await response.json();
            arePushNotificationsEnabled.value = data.message;
        } catch (error) {
            console.error('Failed to check push notifications status:', error);
            arePushNotificationsEnabled.value = false;
        }
    }

    return {
        notifications,
        unreadCount,
        isLoading,
        arePushNotificationsEnabled,
        allowPushNotifications,
        fetchNotifications,
        markAsRead,
        markAllAsRead,
        checkPushNotificationsEnabled
    };
}); 