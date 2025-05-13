<template>
  <div class="scorm-player">
    <header class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5">
      <div class="flex items-center">
        <h1 class="text-xl font-semibold">{{ packageDetails.title }}</h1>
      </div>
      <button @click="exitPlayer" class="text-gray-600 hover:text-gray-800">
        Exit
      </button>
    </header>

    <div v-if="loading" class="flex justify-center items-center h-screen">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>

    <div v-else-if="error" class="text-red-500 p-4">
      {{ error }}
    </div>

    <div v-else-if="readyToRender" class="h-screen flex flex-col">
      <iframe
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
</template>

<script setup>
import { ref, onMounted, onUnmounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref(null)
const packageDetails = ref({})
const launchUrl = ref('')
const readyToRender = ref(false)
const scormFrame = ref(null)
const user = inject('$user')

const getDataFromLMS = (key) => {
  if (key === 'cmi.core.lesson_status') {
    if (progress.data?.status === 'Complete') {
      return 'passed'
    }
    return 'incomplete'
  }
  return ''
}

const saveDataToLMS = (key, value) => {
  if (key === 'cmi.core.lesson_status' && value === 'passed') {
    saveProgress()
  }
}

const saveProgress = async () => {
  try {
    await fetch('/api/method/education.api.save_scorm_session', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        package: route.params.packageId,
        data: JSON.stringify({
          status: 'Complete',
          score: 100
        })
      })
    })
  } catch (err) {
    console.error('Error saving progress:', err)
  }
}

const progress = createResource({
  url: 'frappe.client.get_value',
  makeParams(values) {
    return {
      doctype: 'SCORM Session',
      fieldname: 'status',
      filters: {
        package: route.params.packageId,
        student: user?.data?.name
      }
    }
  },
  onSuccess(data) {
    readyToRender.value = true
  }
})

const setupSCORMAPI = () => {
  window.API_1484_11 = {
    Initialize: () => 'true',
    Terminate: () => 'true',
    GetValue: (key) => {
      console.log(`GET: ${key}`)
      return getDataFromLMS(key)
    },
    SetValue: (key, value) => {
      console.log(`SET: ${key} to value: ${value}`)
      saveDataToLMS(key, value)
      return 'true'
    },
    Commit: () => 'true',
    GetLastError: () => '0',
    GetErrorString: () => '',
    GetDiagnostic: () => ''
  }

  window.API = {
    LMSInitialize: () => 'true',
    LMSFinish: () => 'true',
    LMSGetValue: (key) => {
      console.log(`GET: ${key}`)
      return getDataFromLMS(key)
    },
    LMSSetValue: (key, value) => {
      console.log(`SET: ${key} to value: ${value}`)
      saveDataToLMS(key, value)
      return 'true'
    },
    LMSCommit: () => 'true',
    LMSGetLastError: () => '0',
    LMSGetErrorString: () => '',
    LMSGetDiagnostic: () => ''
  }
}

const fetchPackageDetails = async () => {
  try {
    const response = await fetch(`/api/method/education.api.get_scorm_package_details?package=${route.params.packageId}`, {
      headers: {
        'Accept': 'application/json'
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    
    if (data.message) {
      packageDetails.value = data.message
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
    setupSCORMAPI()
    const iframeWindow = scormFrame.value.contentWindow
    if (iframeWindow) {
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
  router.push('/scorm-packages')
}

onMounted(() => {
  fetchPackageDetails()
  setupSCORMAPI()
})

onUnmounted(() => {
  delete window.API_1484_11
  delete window.API
})
</script>

<style scoped>
.scorm-player {
  height: 100vh;
  background: #f5f5f5;
}
</style> 