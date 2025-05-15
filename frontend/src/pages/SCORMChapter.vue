<template>
  <header class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5">
    <Breadcrumbs :items="breadcrumbs" />
  </header>
  <div v-if="chapter.data && chapter.data.launch_file" class="scorm-container">
    <div class="flex justify-between items-center p-3 bg-gray-100">
      <div>
        <span class="mr-4">
          <span class="font-semibold">Status:</span>
          <span 
            :class="{
              'text-green-600': chapter.data.status === 'completed' || chapter.data.status === 'passed',
              'text-yellow-600': chapter.data.status === 'incomplete',
              'text-red-600': chapter.data.status === 'failed',
              'text-gray-600': chapter.data.status === 'not attempted'
            }"
          >
            {{ chapter.data.status }}
          </span>
        </span>
        <span class="mr-4">
          <span class="font-semibold">Score:</span> {{ chapter.data.score || 0 }}%
        </span>
        <span>
          <span class="font-semibold">Attempts:</span> {{ chapter.data.attempts || 0 }}
        </span>
      </div>
      <div>
        <router-link 
          :to="{ name: 'CourseDetail', params: { courseName: props.courseName }}" 
          class="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
        >
          Back to Course
        </router-link>
      </div>
    </div>
    <iframe ref="scormIframe" :src="chapter.data.launch_file" class="w-full h-screen"></iframe>
  </div>
  <div v-else class="text-center pt-10 px-5 md:px-0 pb-10">
    <div class="mb-4">SCORM package not available.</div>
    <router-link 
      :to="{ name: 'CourseDetail', params: { courseName: props.courseName }}" 
      class="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
    >
      Back to Course
    </router-link>
  </div>
</template>
<script setup>
import { createResource, Breadcrumbs } from 'frappe-ui'
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  courseName: {
    type: String,
    required: true,
  },
  chapterName: {
    type: String,
    required: true,
  },
})

const chapter = createResource({
  url: '/api/method/education.education.api.scorm.get_scorm_chapter',
  params: { chapter: props.chapterName },
  auto: true,
})

const breadcrumbs = computed(() => [
  { label: 'Courses', route: { name: 'Courses' } },
  { label: props.courseName, route: { name: 'CourseDetail', params: { courseName: props.courseName } } },
  { label: chapter?.data?.title || 'SCORM Chapter' },
])

const scormIframe = ref(null)
let API = null
let terminated = false

// Define simple version of SCORM 1.2 API
const createSCORM12API = () => {
  const data = {
    'cmi.core.student_id': '',
    'cmi.core.student_name': '',
    'cmi.core.lesson_location': '',
    'cmi.core.lesson_status': chapter.data?.status || 'not attempted',
    'cmi.core.score.raw': chapter.data?.score || '',
    'cmi.core.score.min': '0',
    'cmi.core.score.max': '100',
    'cmi.core.exit': '',
    'cmi.core.session_time': '',
    'cmi.suspend_data': '',
    'cmi.launch_data': '',
    'cmi.comments': '',
    'cmi.comments_from_lms': '',
  }

  return {
    LMSInitialize: function() {
      console.log('[SCORM] LMSInitialize called')
      return 'true'
    },
    LMSFinish: function() {
      console.log('[SCORM] LMSFinish called')
      saveProgress()
      terminated = true
      return 'true'
    },
    LMSGetValue: function(element) {
      console.log(`[SCORM] LMSGetValue: ${element} = ${data[element] || ''}`)
      return data[element] || ''
    },
    LMSSetValue: function(element, value) {
      console.log(`[SCORM] LMSSetValue: ${element} = ${value}`)
      data[element] = value
      return 'true'
    },
    LMSCommit: function() {
      console.log('[SCORM] LMSCommit called')
      saveProgress()
      return 'true'
    },
    LMSGetLastError: function() {
      return '0'
    },
    LMSGetErrorString: function() {
      return 'No error'
    },
    LMSGetDiagnostic: function() {
      return 'No diagnostic information available'
    }
  }
}

// Function to save progress to backend
const saveProgress = async () => {
  if (!API || terminated) return

  const score = API.LMSGetValue('cmi.core.score.raw')
  const status = API.LMSGetValue('cmi.core.lesson_status')

  try {
    const response = await fetch('/api/method/education.education.api.scorm.save_scorm_data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        course_chapter: props.chapterName,
        score: score,
        status: status
      })
    })
    
    const result = await response.json()
    if (result.message) {
      console.log('[SCORM] Progress saved:', result.message)
      
      // Refresh the chapter data to update UI
      chapter.reload()
    }
  } catch (error) {
    console.error('[SCORM] Error saving progress:', error)
  }
}

onMounted(() => {
  // Create and expose SCORM 1.2 API
  API = createSCORM12API()
  window.API = API
  
  // Handle window unload - save progress when leaving the page
  window.addEventListener('beforeunload', saveProgress)
})

onBeforeUnmount(() => {
  // Save progress before component is destroyed
  saveProgress()
  
  // Clean up
  window.removeEventListener('beforeunload', saveProgress)
  delete window.API
  API = null
})
</script>

<style scoped>
.scorm-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 50px);
}

.scorm-container iframe {
  flex: 1;
  border: none;
}
</style> 