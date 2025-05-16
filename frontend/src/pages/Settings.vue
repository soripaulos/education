<template>
    <div class="flex flex-col h-screen w-screen">
        <div class="w-full sm:w-96">
            <header class="flex flex-row bg-white shadow-sm py-4 px-3 items-center justify-between border-b sticky top-0 z-10">
                <div class="flex flex-row items-center">
                    <Button variant="ghost" class="!pl-0 hover:bg-white" @click="router.back()">
                        <FeatherIcon name="chevron-left" class="h-5 w-5" />
                    </Button>
                    <h2 class="text-xl font-semibold text-gray-900">{{ __("Settings") }}</h2>
                </div>
            </header>

            <div class="flex flex-col gap-4 mt-5 p-4">
                <PushNotificationSettings />
            </div>
        </div>
    </div>
</template>

<script setup>
import { useRouter } from "vue-router"
import { Button, FeatherIcon } from "frappe-ui"
import { inject } from "vue"
import PushNotificationSettings from "@/components/PushNotificationSettings.vue"

const router = useRouter()
const __ = inject("$translate")
</script> 