<template>
  <div v-if="course.data">
    <header class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5">
      <Breadcrumbs :items="breadcrumbs" />
    </header>
    <div class="m-5">
      <div class="flex flex-col md:flex-row w-full">
        <div class="md:w-2/3">
          <div class="text-3xl font-semibold text-ink-gray-9">
            {{ course.data.title }}
          </div>
          <div class="my-3 leading-6 text-ink-gray-7">
            {{ course.data.description }}
          </div>
          <div class="mt-10">
            <div class="bg-gray-50 p-4 rounded">
              <div v-if="course.data.chapters && course.data.chapters.length">
                <div v-for="chapter in course.data.chapters" :key="chapter.name" class="mb-5 border-b pb-4">
                  <div class="flex justify-between items-center">
                    <div>
                      <router-link
                        v-if="chapter.is_scorm_package"
                        :to="{ name: 'SCORMChapter', params: { courseName: course.data.name, chapterName: chapter.name } }"
                        class="text-primary hover:underline text-lg font-medium"
                      >
                        {{ chapter.index }}. {{ chapter.title }} (SCORM)
                      </router-link>
                      <span v-else class="text-lg font-medium">
                        {{ chapter.index }}. {{ chapter.title }}
                      </span>
                    </div>
                    <div v-if="chapter.is_scorm_package" class="text-sm">
                      <span class="bg-gray-100 px-2 py-1 rounded text-gray-600 mr-2">
                        <span class="font-semibold">Attempts:</span> {{ chapter.attempts || 0 }}
                      </span>
                      <span class="bg-gray-100 px-2 py-1 rounded text-gray-600 mr-2">
                        <span class="font-semibold">Score:</span> {{ chapter.score || 0 }}%
                      </span>
                      <span 
                        :class="{
                          'bg-green-100 text-green-700': chapter.status === 'completed' || chapter.status === 'passed',
                          'bg-yellow-100 text-yellow-700': chapter.status === 'incomplete',
                          'bg-red-100 text-red-700': chapter.status === 'failed',
                          'bg-gray-100 text-gray-600': chapter.status === 'not attempted'
                        }"
                        class="px-2 py-1 rounded"
                      >
                        {{ chapter.status }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else>No chapters available.</div>
            </div>
          </div>
        </div>
        <div class="hidden md:block md:w-1/3 md:pl-5">
          <!-- Course overview/summary could go here -->
        </div>
      </div>
    </div>
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
})

const course = createResource({
  url: '/api/method/education.education.api.scorm.get_course_data',
  params: { course: props.courseName },
  auto: true,
})

const breadcrumbs = computed(() => [
  { label: 'Courses', route: { name: 'Courses' } },
  { label: course?.data?.title || 'Course Details' },
])
</script> 