<template>
  <nav class="bg-white shadow-sm border-b">
    <div class="flex items-center justify-between px-4 h-16">
      <!-- Logo and Brand -->
      <div class="flex items-center">
        <UserDropdown
          class="mr-4"
          :isCollapsed="false"
          :educationSettings="!educationSettings.loading && educationSettings.data"
        />
      </div>

      <!-- Desktop Navigation -->
      <div class="hidden md:flex items-center space-x-2">
        <SidebarLink
          v-for="link in links"
          :key="link.to"
          :label="link.label"
          :to="link.to"
          :isCollapsed="false"
          :icon="link.icon"
          class="h-10"
        />
        <NotificationBell class="ml-2" />
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

    <!-- Mobile menu -->
    <div 
      v-show="mobileMenuOpen" 
      class="md:hidden border-t"
    >
      <div class="px-2 pt-2 pb-3 space-y-1">
        <SidebarLink
          v-for="link in links"
          :key="link.to"
          :label="link.label"
          :to="link.to"
          :isCollapsed="false"
          :icon="link.icon"
          class="w-full"
          @click="mobileMenuOpen = false"
        />
        <router-link to="/notifications" class="flex items-center px-2 py-2 text-base font-medium text-gray-600 rounded-md hover:bg-gray-100 hover:text-gray-900" @click="mobileMenuOpen = false">
          <BellIcon class="mr-3 h-6 w-6 text-gray-500" />
          Notifications
        </router-link>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import SidebarLink from '@/components/SidebarLink.vue'
import UserDropdown from './UserDropdown.vue'
import NotificationBell from './NotificationBell.vue'
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
  Bell as BellIcon,
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