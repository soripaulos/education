import { defineStore } from 'pinia';
import { ref } from 'vue';
import frappe from 'frappe-ui/src/utils/frappe'; // Assuming frappe-ui provides a frappe instance for API calls

// Helper function to convert VAPID public key
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export const useNotificationStore = defineStore('notifications', () => {
  const isSubscribed = ref(false);
  const fcmToken = ref(null);
  const permissionStatus = ref(Notification.permission);
  const error = ref(null);
  const VAPID_PUBLIC_KEY = ref(null); // This needs to be fetched or configured

  async function fetchVapidKey() {
    // In a real scenario, this key should be fetched from the server
    // or be part of the initial app configuration.
    // For Frappe, this might be in frappe.boot.vapid_public_key or a similar global object.
    if (window.frappe && window.frappe.boot && window.frappe.boot.vapid_public_key) {
      VAPID_PUBLIC_KEY.value = window.frappe.boot.vapid_public_key;
    } else {
      // Fallback or error if key is not available
      // For now, let's hardcode a placeholder. THIS IS NOT SECURE FOR PRODUCTION.
      // console.warn('VAPID Public Key not found in frappe.boot. Using placeholder.');
      // VAPID_PUBLIC_KEY.value = 'YOUR_VAPID_PUBLIC_KEY_HERE'; // Replace this
      // Ideally, this should throw an error or prevent subscription if the key isn't available.
      // For this exercise, we will allow it to proceed, but real implementation needs a server-provided key.
      error.value = 'VAPID public key not available. Push notifications cannot be enabled.';
      console.error(error.value);
    }
  }

  async function initialize() {
    await fetchVapidKey();
    permissionStatus.value = Notification.permission;

    if (!('serviceWorker' in navigator) || !('PushManager' in window) || !VAPID_PUBLIC_KEY.value) {
      console.warn('Push messaging is not supported or VAPID key is missing.');
      error.value = 'Push messaging is not supported by this browser or VAPID key is missing.';
      return;
    }

    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();

    if (subscription) {
      isSubscribed.value = true;
      fcmToken.value = subscription.endpoint; // Or a more specific token if FCM is used directly
      // You might want to send the token to your server here to confirm subscription state
    } else {
      isSubscribed.value = false;
    }
  }

  async function subscribe() {
    if (!VAPID_PUBLIC_KEY.value) {
        await fetchVapidKey();
        if (!VAPID_PUBLIC_KEY.value) {
            error.value = "VAPID public key is not configured. Cannot subscribe.";
            console.error(error.value);
            return false;
        }
    }

    const registration = await navigator.serviceWorker.ready;
    try {
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY.value)
      });

      // The subscription object for FCM is complex. Usually, the endpoint is the FCM token.
      // For Frappe's Push Notification Relay, the entire subscription object might be needed by `frappe.push_notification.subscribe`
      // or it might expect just the FCM token extracted from the subscription.
      // The backend API created (`subscribe_to_notifications`) expects a simple `token`.
      // Let's assume for now `subscription.endpoint` is what we need or a similar unique identifier.
      // If `frappe.push_notification.subscribe` (the Frappe whitelisted method) expects the whole object,
      // then the backend API needs to be adjusted or this payload needs to be sent differently.
      // For now, we send the endpoint, assuming it acts as the token.
      const tokenToSend = subscription.endpoint; 

      await frappe.call({
        method: 'education.api.subscribe_to_notifications',
        args: { token: tokenToSend },
      });
      fcmToken.value = tokenToSend;
      isSubscribed.value = true;
      error.value = null;
      return true;
    } catch (e) {
      console.error('Failed to subscribe to push notifications:', e);
      error.value = e.message;
      isSubscribed.value = false;
      // If permission was denied, update status
      if (Notification.permission === 'denied') {
        permissionStatus.value = 'denied';
      }
      return false;
    }
  }

  async function unsubscribe() {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();

    if (subscription) {
      try {
        await subscription.unsubscribe();
        // Similar to subscribe, send the token (endpoint) that was used to subscribe.
        await frappe.call({
          method: 'education.api.unsubscribe_from_notifications',
          args: { token: fcmToken.value }, // Use the stored token for unsubscription
        });
        isSubscribed.value = false;
        fcmToken.value = null;
        error.value = null;
        return true;
      } catch (e) {
        console.error('Failed to unsubscribe from push notifications:', e);
        error.value = e.message;
        return false;
      }
    }
    return false;
  }

  async function requestPermissionAndSubscribe() {
    permissionStatus.value = await Notification.requestPermission();
    if (permissionStatus.value === 'granted') {
      return await subscribe();
    }
    return false;
  }

  return {
    isSubscribed,
    fcmToken,
    permissionStatus,
    error,
    initialize,
    subscribe,
    unsubscribe,
    requestPermissionAndSubscribe
  };
}); 