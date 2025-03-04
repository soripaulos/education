<template>
  <div class="min-h-screen bg-gray-50">
    <Sidebar />
    <main class="pt-16 px-4">
      <router-view></router-view>
    </main>
    <Toasts />
  </div>
</template>

<script setup>
import Sidebar from '@/components/Sidebar.vue'
import { RouterView } from 'vue-router'
import { Toasts } from 'frappe-ui'
</script>

<style>
#app {
  @apply antialiased text-gray-900;
}
</style>
