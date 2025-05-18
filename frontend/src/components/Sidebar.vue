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
        <!-- Notification Icon -->
        <button 
          @click="goToNotifications"
          title="Notifications"
          class="p-2 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <Bell class="h-6 w-6 text-gray-700" />
        </button>
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
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import SidebarLink from '@/components/SidebarLink.vue'
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
  Bell,
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

// Placeholder for navigation to a notifications page/area
// You might want to implement a dedicated notifications view or a dropdown panel.
const goToNotifications = () => {
  // Example: router.push('/notifications');
  // For now, it can just log or do nothing if a page doesn't exist yet.
  console.log('Notification icon clicked. Implement navigation or display panel.');
  // Potentially, open the NotificationSettings component in a modal or navigate to a page containing it.
}
</script> 