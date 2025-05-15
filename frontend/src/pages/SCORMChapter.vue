<template>
  <header class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5">
    <Breadcrumbs :items="breadcrumbs" />
  </header>
  <div v-if="chapter.data && chapter.data.launch_file">
    <iframe :src="chapter.data.launch_file" class="w-full h-screen" />
  </div>
  <div v-else class="text-center pt-10 px-5 md:px-0 pb-10">
    <div class="mb-4">SCORM package not available.</div>
  </div>
</template>
<script setup>
import { createResource, Breadcrumbs } from 'frappe-ui'
import { computed } from 'vue'

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
  url: '/api/method/education.api.get_scorm_chapter',
  params: { chapter: props.chapterName },
  auto: true,
})

const breadcrumbs = computed(() => [
  { label: 'Courses', route: { name: 'Courses' } },
  { label: props.courseName, route: { name: 'CourseDetail', params: { courseName: props.courseName } } },
  { label: chapter?.data?.title || 'SCORM Chapter' },
])
</script> 