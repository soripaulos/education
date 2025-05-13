<template>
  <div class="scorm-packages">
    <h1 class="text-2xl font-bold mb-6">SCORM Packages</h1>
    
    <div v-if="loading" class="flex justify-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>

    <div v-else-if="error" class="text-red-500">
      {{ error }}
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="scormPackage in packages" :key="scormPackage.name" 
           class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
        <h3 class="text-xl font-semibold mb-2">{{ scormPackage.title }}</h3>
        <div class="text-gray-600 mb-4" v-html="scormPackage.description"></div>
        
        <div class="flex flex-wrap gap-2 mb-4">
          <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
            Version: {{ scormPackage.version }}
          </span>
          <span v-if="scormPackage.last_attempt" 
                class="px-2 py-1 bg-gray-100 text-gray-800 rounded text-sm">
            Last Attempt: {{ formatDate(scormPackage.last_attempt.date) }}
          </span>
        </div>

        <div class="flex justify-between items-center">
          <div v-if="scormPackage.last_attempt" class="text-sm">
            <span class="font-medium">Score: </span>
            {{ scormPackage.last_attempt.score }}%
          </div>
          <button @click="launchPackage(scormPackage.name)" 
                  class="bg-primary text-white px-4 py-2 rounded hover:bg-primary-dark transition-colors">
            Launch Package
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { formatDate } from '@/utils/date'

export default {
  name: 'ScormPackages',
  
  setup() {
    const router = useRouter()
    const packages = ref([])
    const loading = ref(true)
    const error = ref(null)

    const fetchPackages = async () => {
      try {
        const response = await fetch('/api/method/education.api.get_scorm_packages')
        const data = await response.json()
        
        if (data.message) {
          packages.value = data.message
        }
      } catch (err) {
        error.value = 'Failed to load SCORM packages'
        console.error('Error fetching packages:', err)
      } finally {
        loading.value = false
      }
    }

    const launchPackage = (packageName) => {
      router.push(`/scorm/${packageName}`)
    }

    onMounted(fetchPackages)

    return {
      packages,
      loading,
      error,
      launchPackage,
      formatDate
    }
  }
}
</script>

<style scoped>
.scorm-packages {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}
</style> 