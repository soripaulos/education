<template>
  <nav class="bg-white shadow-sm">
    <!-- Desktop Navigation -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <!-- Logo and Brand -->
        <div class="flex items-center">
          <div class="flex-shrink-0 flex items-center">
            <img 
              v-if="educationSettings?.school_logo" 
              :src="educationSettings.school_logo" 
              class="h-8 w-auto"
              alt="School Logo"
            />
            <span v-if="educationSettings?.school_abbr" class="ml-2 text-xl font-semibold text-gray-900">
              {{ educationSettings.school_abbr }}
            </span>
          </div>
        </div>

        <!-- Desktop Menu Items -->
        <div class="hidden sm:flex sm:space-x-4">
          <router-link
            v-for="link in links"
            :key="link.to"
            :to="link.to"
            class="inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-150 hover:bg-gray-50"
            :class="[
              $route.path === link.to
                ? 'text-indigo-600 bg-indigo-50'
                : 'text-gray-700 hover:text-gray-900'
            ]"
          >
            <component :is="link.icon" class="h-5 w-5 mr-1.5" />
            {{ link.label }}
          </router-link>
        </div>

        <!-- User Menu -->
        <div class="hidden sm:flex sm:items-center">
          <UserDropdown :educationSettings="!educationSettings.loading && educationSettings.data" />
        </div>

        <!-- Mobile menu button -->
        <div class="flex items-center sm:hidden">
          <button
            @click="mobileMenuOpen = !mobileMenuOpen"
            class="inline-flex items-center justify-center p-2 rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
          >
            <Menu v-if="!mobileMenuOpen" class="h-6 w-6" />
            <X v-else class="h-6 w-6" />
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Navigation -->
    <div
      v-show="mobileMenuOpen"
      class="sm:hidden bg-white border-t border-gray-200"
    >
      <div class="pt-2 pb-3 space-y-1">
        <router-link
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="flex items-center px-4 py-2 text-base font-medium transition-colors duration-150"
          :class="[
            $route.path === link.to
              ? 'text-indigo-600 bg-indigo-50'
              : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
          ]"
          @click="mobileMenuOpen = false"
        >
          <component :is="link.icon" class="h-5 w-5 mr-3" />
          {{ link.label }}
        </router-link>
      </div>
      <!-- Mobile User Menu -->
      <div class="pt-4 pb-3 border-t border-gray-200">
        <div class="px-4">
          <UserDropdown 
            :educationSettings="!educationSettings.loading && educationSettings.data"
            class="w-full" 
          />
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import { createResource } from 'frappe-ui'
import UserDropdown from './UserDropdown.vue'
import {
  CalendarCheck,
  GraduationCap,
  Banknote,
  UserCheck,
  BarChart2,
  Star,
  Menu,
  X,
  Clipboard,
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
    label: 'Assessment Logs',
    to: '/assessment-logs',
    icon: Clipboard,
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

@media (max-width: 640px) {
  .router-link-active {
    @apply bg-indigo-50;
  }
}
</style> 