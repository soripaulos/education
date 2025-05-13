<template>
  <div class="scorm-player">
    <div v-if="loading" class="flex justify-center items-center h-screen">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>

    <div v-else-if="error" class="text-red-500 p-4">
      {{ error }}
    </div>

    <div v-else class="h-screen flex flex-col">
      <div class="bg-white shadow-sm p-4 flex justify-between items-center">
        <h1 class="text-xl font-semibold">{{ packageDetails.title }}</h1>
        <button @click="exitPlayer" 
                class="text-gray-600 hover:text-gray-800">
          Exit
        </button>
      </div>

      <div class="flex-1 relative">
        <iframe
          v-if="launchUrl"
          :src="launchUrl"
          class="w-full h-full border-0"
          @load="onIframeLoad"
          ref="scormFrame"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-downloads"
          @error="handleIframeError"
        ></iframe>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ScormAPI } from '@/utils/scorm'

export default {
  name: 'ScormPlayer',

  setup() {
    const route = useRoute()
    const router = useRouter()
    const loading = ref(true)
    const error = ref(null)
    const packageDetails = ref({})
    const launchUrl = ref('')
    const scormAPI = ref(null)
    const scormFrame = ref(null)

    const fetchPackageDetails = async () => {
      try {
        const response = await fetch(`/api/method/education.api.get_scorm_package_details?package=${route.params.packageId}`, {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        })
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        
        if (data.message) {
          packageDetails.value = data.message
          // Ensure the launch URL is properly formatted
          launchUrl.value = data.message.launch_url.startsWith('/') 
            ? window.location.origin + data.message.launch_url
            : data.message.launch_url
        }
      } catch (err) {
        error.value = 'Failed to load SCORM package: ' + err.message
        console.error('Error fetching package details:', err)
      } finally {
        loading.value = false
      }
    }

    const handleIframeError = (err) => {
      console.error('Iframe error:', err)
      error.value = 'Failed to load SCORM content. Please check your browser settings and try again.'
    }

    const onIframeLoad = () => {
      try {
        // Initialize SCORM API when iframe is loaded
        scormAPI.value = new ScormAPI({
          packageId: route.params.packageId,
          onCommit: async (data) => {
            try {
              const response = await fetch('/api/method/education.api.save_scorm_session', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Accept': 'application/json'
                },
                body: JSON.stringify({
                  package: route.params.packageId,
                  data: JSON.stringify(data)
                })
              })
              
              if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
              }
            } catch (err) {
              console.error('Error saving SCORM session:', err)
            }
          }
        })

        // Try to find API in iframe
        const iframeWindow = scormFrame.value.contentWindow
        if (iframeWindow) {
          // Set up message listener for cross-frame communication if needed
          window.addEventListener('message', (event) => {
            if (event.source === iframeWindow) {
              console.log('Received message from SCORM content:', event.data)
            }
          })
        }
      } catch (err) {
        console.error('Error initializing SCORM API:', err)
        error.value = 'Failed to initialize SCORM API'
      }
    }

    const exitPlayer = () => {
      if (scormAPI.value) {
        scormAPI.value.terminate()
      }
      router.push('/scorm-packages')
    }

    onMounted(fetchPackageDetails)

    onUnmounted(() => {
      if (scormAPI.value) {
        scormAPI.value.terminate()
      }
    })

    return {
      loading,
      error,
      packageDetails,
      launchUrl,
      onIframeLoad,
      handleIframeError,
      exitPlayer,
      scormFrame
    }
  }
}
</script>

<style scoped>
.scorm-player {
  height: 100vh;
  background: #f5f5f5;
}
</style> 