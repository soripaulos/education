<template>
  <header class="sticky flex items-center justify-between top-0 z-10 border-b bg-surface-white px-3 py-2.5 sm:px-5">
    <h1 class="text-xl font-semibold">Courses</h1>
  </header>
  <div class="p-5 pb-10">
    <div v-if="loading" class="flex justify-center items-center h-40">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
    <div v-else-if="error" class="text-red-500 p-4">
      {{ error }}
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4">
      <div v-for="course in courses" :key="course.name" class="flex flex-col h-full rounded-md border overflow-hidden bg-white">
        <div class="h-40 bg-gray-100 flex items-center justify-center" v-if="course.image">
          <img :src="course.image" :alt="course.title" class="object-cover h-full w-full" />
        </div>
        <div class="h-40 bg-gray-100 flex items-center justify-center text-4xl font-bold" v-else>
          {{ course.title[0] }}
        </div>
        <div class="flex flex-col flex-auto p-4">
          <div class="text-xl font-semibold leading-6 text-ink-gray-9 mb-2">
            {{ course.title }}
          </div>
          <div class="text-ink-gray-7 text-sm mb-2">
            {{ course.short_introduction || course.description }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'

const courses = ref([])
const loading = ref(true)
const error = ref(null)

onMounted(async () => {
  try {
    const response = await fetch('/api/method/education.api.get_courses', {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    const data = await response.json()
    courses.value = data.message || []
  } catch (err) {
    error.value = 'Failed to load courses: ' + err.message
    console.error('Error fetching courses:', err)
  } finally {
    loading.value = false
  }
})
</script> 