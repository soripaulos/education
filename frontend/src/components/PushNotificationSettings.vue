<template>
    <div class="flex flex-col gap-4">
        <div class="flex flex-row items-center justify-between">
            <div class="flex flex-col">
                <h3 class="text-lg font-semibold text-gray-900">{{ __("Push Notifications") }}</h3>
                <p class="text-sm text-gray-500">{{ __("Receive notifications on your device") }}</p>
            </div>
            <Switch
                v-model="enabled"
                :loading="loading"
                @update:modelValue="handleToggle"
            />
        </div>
        <div v-if="error" class="text-sm text-red-500">
            {{ error }}
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { Switch } from "frappe-ui"
import { arePushNotificationsEnabled } from "@/data/notifications"

const enabled = ref(false)
const loading = ref(false)
const error = ref("")
const __ = inject("$translate")

const handleToggle = async (value) => {
    loading.value = true
    error.value = ""
    
    try {
        const method = value ? "enable_push_notifications" : "disable_push_notifications"
        const response = await frappe.call({
            method: `education.education.api.notifications.${method}`,
        })
        
        if (response.message?.status === "error") {
            throw new Error(response.message.message)
        }
        
        // Request permission if enabling
        if (value && window.frappePushNotification) {
            const permission = await window.frappePushNotification.requestPermission()
            if (permission !== "granted") {
                throw new Error(__("Notification permission denied"))
            }
        }
        
        arePushNotificationsEnabled.reload()
    } catch (e) {
        error.value = e.message
        enabled.value = !value // Revert the switch
    } finally {
        loading.value = false
    }
}

onMounted(() => {
    enabled.value = arePushNotificationsEnabled.data
})
</script> 