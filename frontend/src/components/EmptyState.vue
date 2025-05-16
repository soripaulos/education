<template>
    <div class="flex flex-col items-center justify-center p-8 text-center">
        <FeatherIcon name="inbox" class="h-12 w-12 text-gray-400 mb-4" />
        <p class="text-gray-500">{{ message }}</p>
    </div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"

defineProps({
    message: {
        type: String,
        required: true
    }
})
</script> 