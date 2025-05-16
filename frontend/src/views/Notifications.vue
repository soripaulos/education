<template>
    <div class="flex flex-col h-screen w-screen">
        <div class="w-full sm:w-96">
            <header class="flex flex-row bg-white shadow-sm py-4 px-3 items-center justify-between border-b sticky top-0 z-10">
                <div class="flex flex-row items-center">
                    <Button variant="ghost" class="!pl-0 hover:bg-white" @click="router.back()">
                        <FeatherIcon name="chevron-left" class="h-5 w-5" />
                    </Button>
                    <h2 class="text-xl font-semibold text-gray-900">{{ __("Notifications") }}</h2>
                </div>
            </header>

            <div class="flex flex-col gap-4 mt-5 p-4">
                <div class="flex flex-row justify-between items-center">
                    <div class="text-lg text-gray-800 font-semibold" v-if="unreadNotificationsCount.data">
                        {{ __("{0} Unread", [unreadNotificationsCount.data]) }}
                    </div>
                    <div class="flex ml-auto gap-1">
                        <Button v-if="allowPushNotifications" variant="outline" @click="router.push({ name: 'Settings' })">
                            <template #prefix>
                                <FeatherIcon name="settings" class="w-4" />
                            </template>
                            {{ __("Settings") }}
                        </Button>
                        <Button v-if="unreadNotificationsCount.data" variant="outline" @click="markAllAsRead.submit" :loading="markAllAsRead.loading">
                            <template #prefix>
                                <FeatherIcon name="check-circle" class="w-4" />
                            </template>
                            {{ __("Mark all as read") }}
                        </Button>
                    </div>
                </div>

                <div class="flex flex-col bg-white rounded" v-if="notifications.data?.length">
                    <router-link
                        :class="[
                            'flex flex-row items-start p-4 justify-between border-b before:mt-3',
                            `before:content-[''] before:mr-2 before:shrink-0 before:w-1.5 before:h-1.5 before:rounded-full`,
                            item.read ? 'bg-white-500' : 'before:bg-blue-500',
                        ]"
                        v-for="item in notifications.data"
                        :key="item.name"
                        :to="getItemRoute(item)"
                        @click="markAsRead(item.name)"
                    >
                        <div class="flex flex-col gap-0.5 grow ml-3">
                            <div class="text-sm leading-5 font-normal text-gray-800" v-html="item.message"></div>
                            <div class="text-xs font-normal text-gray-500">
                                {{ dayjs(item.creation).fromNow() }}
                            </div>
                        </div>
                    </router-link>
                </div>

                <EmptyState v-else :message="__('You have no notifications')" />
            </div>
        </div>
    </div>
</template>

<script setup>
import { useRouter } from "vue-router"
import { createResource, createListResource, FeatherIcon } from "frappe-ui"
import { computed, inject } from "vue"
import EmptyState from "@/components/EmptyState.vue"

// Using createListResource instead of createResource for notifications
const notifications = createListResource({
    doctype: "PWA Notification",
    filters: { to_user: frappe.session.user },
    fields: [
        "name",
        "from_user",
        "message",
        "read",
        "creation",
        "reference_document_type",
        "reference_document_name"
    ],
    auto: true,
    orderBy: "creation desc",
    onSuccess() {
        unreadNotificationsCount.reload()
    }
})

const unreadNotificationsCount = createResource({
    url: "education.education.api.notifications.get_unread_count",
    auto: true,
    transform: (data) => data?.count || 0,
})

const arePushNotificationsEnabled = createResource({
    url: "education.education.api.notifications.are_push_notifications_enabled",
    auto: true,
    transform: (data) => data?.enabled || false,
})

const dayjs = inject("$dayjs")
const router = useRouter()
const __ = inject("$translate")

const allowPushNotifications = computed(
    () => window.frappe?.boot.push_relay_server_url && arePushNotificationsEnabled.data
)

const markAllAsRead = createResource({
    url: "education.education.api.notifications.mark_all_as_read",
    onSuccess() {
        notifications.reload()
        unreadNotificationsCount.reload()
    },
})

function markAsRead(name) {
    notifications.setValue.submit(
        { name, read: 1 },
        {
            onSuccess: () => {
                unreadNotificationsCount.reload()
            },
        }
    )
}

function getItemRoute(item) {
    if (!item.reference_document_type || !item.reference_document_name) {
        return { name: "Home" }
    }
    
    return {
        name: `${item.reference_document_type.replace(/\s+/g, "")}DetailView`,
        params: { id: item.reference_document_name },
    }
}
</script> 