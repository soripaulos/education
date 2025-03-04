<template>
  <div class="fixed top-0 left-0 right-0 bg-white shadow-sm z-50">
    <div class="flex items-center justify-between h-16 px-4">
      <!-- Logo and Brand -->
      <div class="flex items-center">
        <UserDropdown
          :isCollapsed="false"
          :educationSettings="!educationSettings.loading && educationSettings.data"
        />
      </div>

      <!-- Desktop Navigation -->
      <div class="hidden md:flex items-center space-x-4">
        <router-link
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-150"
          :class="[
            $route.path === link.to
              ? 'text-indigo-600 bg-indigo-50'
              : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
          ]"
        >
          <component
            :is="link.icon"
            class="h-5 w-5 mr-1.5"
            :class="$route.path === link.to ? 'text-indigo-600' : 'text-gray-500'"
          />
          {{ link.label }}
        </router-link>
      </div>

      <!-- Mobile menu button -->
      <button 
        @click="mobileMenuOpen = !mobileMenuOpen"
        class="md:hidden p-2 rounded-md hover:bg-gray-100"
      >
        <Menu v-if="!mobileMenuOpen" class="h-6 w-6 text-gray-700" />
        <X v-else class="h-6 w-6 text-gray-700" />
      </button>
    </div>

    <!-- Mobile Navigation -->
    <div
      v-show="mobileMenuOpen"
      class="md:hidden border-t bg-white absolute w-full shadow-lg"
    >
      <div class="px-2 pt-2 pb-3 space-y-1">
        <router-link
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="flex items-center px-3 py-2 text-base font-medium rounded-md transition-colors duration-150"
          :class="[
            $route.path === link.to
              ? 'text-indigo-600 bg-indigo-50'
              : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
          ]"
          @click="mobileMenuOpen = false"
        >
          <component
            :is="link.icon"
            class="h-5 w-5 mr-2"
            :class="$route.path === link.to ? 'text-indigo-600' : 'text-gray-500'"
          />
          {{ link.label }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UserDropdown from './UserDropdown.vue'
import { createResource } from 'frappe-ui'
import {
  CalendarCheck,
  GraduationCap,
  Banknote,
  UserCheck,
  BarChart2,
  Star,
  Menu,
  X,
} from 'lucide-vue-next'

const mobileMenuOpen = ref(false)

const links = [
  {
    label: 'Schedule',
    to: '/schedule',
    icon: CalendarCheck,
  },
  {
    label: 'Grades',
    to: '/grades',
    icon: GraduationCap,
  },
  {
    label: 'Fees',
    to: '/fees',
    icon: Banknote,
  },
  {
    label: 'Attendance',
    to: '/attendance',
    icon: UserCheck,
  },
  {
    label: 'Student Evaluation',
    to: '/evaluation',
    icon: BarChart2,
  },
  {
    label: 'Teacher Evaluation',
    to: '/teacher-evaluation',
    icon: Star,
  },
]

const educationSettings = createResource({
  url: 'education.education.api.get_school_abbr_logo',
  auto: true,
})
</script>

<style scoped>
.router-link-active {
  @apply text-indigo-600 bg-indigo-50;
}
</style> 