<template>
  <div class="min-h-screen bg-gray-50">
    <TopNavigation />
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <router-view></router-view>
    </main>
  </div>
</template>

<script setup>
import TopNavigation from '@/components/TopNavigation.vue'
</script>

<style>
#app {
  @apply antialiased text-gray-900;
}
</style>
