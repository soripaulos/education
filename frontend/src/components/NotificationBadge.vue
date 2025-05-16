<template>
  <div class="relative">
    <Button variant="ghost" class="!p-2" @click="router.push({ name: 'Notifications' })">
      <FeatherIcon name="bell" class="h-5 w-5" />
      <div
        v-if="unreadNotificationsCount.data"
        class="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center"
      >
        {{ unreadNotificationsCount.data > 99 ? "99+" : unreadNotificationsCount.data }}
      </div>
    </Button>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router"
import { FeatherIcon } from "frappe-ui"
import { unreadNotificationsCount } from "@/data/notifications"

const router = useRouter()
</script>

<style scoped>
.notification-badge {
  background-color: #dc3545;
  color: white;
  border-radius: 50%;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  position: absolute;
  top: -5px;
  right: -5px;
}
</style> 