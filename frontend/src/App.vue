<template>
  <div class="min-h-screen bg-gray-50">
    <Sidebar />
    <main class="pt-16">
      <router-view class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"></router-view>
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
