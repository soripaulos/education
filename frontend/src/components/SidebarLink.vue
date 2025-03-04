<template>
  <router-link
    :to="to"
    class="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-150 whitespace-nowrap"
    :class="[
      $route.path === to
        ? 'text-indigo-600 bg-indigo-50'
        : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
    ]"
  >
    <component
      :is="icon"
      class="flex-shrink-0 h-5 w-5"
      :class="$route.path === to ? 'text-indigo-600' : 'text-gray-500'"
    />
    <span
      v-if="!isCollapsed"
      class="ml-2"
    >
      {{ label }}
    </span>
  </router-link>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    required: true,
  },
  to: {
    type: String,
    required: true,
  },
  icon: {
    type: Object,
    required: true,
  },
  isCollapsed: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
.router-link-active {
  @apply text-indigo-600 bg-indigo-50;
}
</style> 