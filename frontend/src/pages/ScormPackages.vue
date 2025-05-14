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
      <div v-for="pkg in packages" :key="pkg.name" class="mb-8 bg-white rounded-lg shadow p-4">
        <h2 class="text-lg font-semibold mb-2">{{ pkg.title }}</h2>
        <p class="text-gray-600 mb-4">{{ pkg.description }}</p>
        <iframe
          v-if="pkg.launch_file"
          :src="getScormUrl(pkg)"
          class="w-full h-[600px] border"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-downloads"
        ></iframe>
        <div v-else class="text-red-500">No launch file found for this package.</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const loading = ref(true)
const error = ref(null)
const packages = ref([])

const getScormUrl = (pkg) => {
  // Assume SCORM packages are extracted to /files/scorm_packages/{pkg.name}/{launch_file}
  return `/files/scorm_packages/${pkg.name}/${pkg.launch_file}`
}

const fetchPackages = async () => {
  try {
    const response = await fetch('/api/method/education.api.get_all_scorm_packages', {
      headers: {
        'Accept': 'application/json'
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

onMounted(fetchPackages)
</script>

<style scoped>
.scorm-packages {
  min-height: 100vh;
  background: #f5f5f5;
}
</style> 