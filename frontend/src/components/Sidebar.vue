<template>
  <div
    class="flex h-full flex-col justify-between transition-all duration-300 ease-in-out"
    :class="sidebarState ? 'w-12' : 'w-56'"
  >
    <div class="flex flex-col overflow-hidden">
      <UserDropdown
        class="p-2"
        :isCollapsed="sidebarState"
        :educationSettings="
          !educationSettings.loading && educationSettings.data
        "
      />
      <div class="flex flex-col overflow-y-auto">
        <SidebarLink
          :label="link.label"
          :to="link.to"
          v-for="link in links"
          :isCollapsed="sidebarState"
          :icon="link.icon"
          class="mx-2 my-0.5"
        />
      </div>
    </div>
    <button 
      @click="toggleSidebar"
      class="m-2 flex items-center p-2 rounded hover:bg-gray-100"
    >
      <span class="grid h-5 w-6 flex-shrink-0 place-items-center">
        <ArrowLeftToLine
          class="h-4.5 w-4.5 text-gray-700 transition-transform duration-300 ease-in-out"
          :class="{ 'rotate-180': sidebarState }"
        />
      </span>
      <span v-if="!sidebarState" class="ml-2">
        {{ sidebarState ? 'Expand' : 'Collapse' }}
      </span>
    </button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useStorage } from '@vueuse/core'
import SidebarLink from '@/components/SidebarLink.vue'
import {
  LayoutDashboard,
  CalendarCheck,
  GraduationCap,
  Banknote,
  UserCheck,
  ArrowLeftToLine,
  BookOpen,
  BarChart2,
  Star,
} from 'lucide-vue-next'

import UserDropdown from './UserDropdown.vue'
import { createResource } from 'frappe-ui'

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

// Create a reactive ref for immediate UI updates
const sidebarState = ref(false)
const isSidebarCollapsed = useStorage('sidebar_is_collapsed', true)

// Sync the storage value with our reactive ref
watch(isSidebarCollapsed, (newValue) => {
  sidebarState.value = newValue
}, { immediate: true })

const toggleSidebar = () => {
  sidebarState.value = !sidebarState.value
  isSidebarCollapsed.value = sidebarState.value
}

const educationSettings = createResource({
  url: 'education.education.api.get_school_abbr_logo',
  auto: true,
})
</script>


