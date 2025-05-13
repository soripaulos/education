<template>
  <div class="scorm-packages">
    <header class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5">
      <h1 class="text-xl font-semibold">SCORM Packages</h1>
    </header>

    <div v-if="loading" class="flex justify-center items-center h-screen">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>

    <div v-else-if="error" class="text-red-500 p-4">
      {{ error }}
    </div>

    <div v-else class="p-4">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="pkg in packages" :key="pkg.name" class="bg-white rounded-lg shadow p-4">
          <h2 class="text-lg font-semibold mb-2">{{ pkg.title }}</h2>
          <p class="text-gray-600 mb-4">{{ pkg.description }}</p>
          <div class="flex justify-between items-center">
            <span class="text-sm text-gray-500">
              Last updated: {{ formatDate(pkg.modified) }}
            </span>
            <button
              @click="launchPackage(pkg.name)"
              class="bg-primary text-white px-4 py-2 rounded hover:bg-primary-dark"
            >
              Launch
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { formatDate } from '@/utils/date'

const router = useRouter()
const loading = ref(true)
const error = ref(null)
const packages = ref([])

const fetchPackages = async () => {
  try {
    const response = await fetch('/api/method/education.api.get_scorm_packages', {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    packages.value = data.message || []
  } catch (err) {
    error.value = 'Failed to load SCORM packages: ' + err.message
    console.error('Error fetching packages:', err)
  } finally {
    loading.value = false
  }
}

const launchPackage = (packageId) => {
  router.push(`/scorm-player/${packageId}`)
}

onMounted(fetchPackages)
</script>

<style scoped>
.scorm-packages {
  min-height: 100vh;
  background: #f5f5f5;
}
</style> 