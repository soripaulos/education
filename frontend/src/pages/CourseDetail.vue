<template>
  <div v-if="course.data">
    <header class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5">
      <Breadcrumbs :items="breadcrumbs" />
    </header>
    <div class="m-5">
      <div class="flex justify-between w-full">
        <div class="md:w-2/3">
          <div class="text-3xl font-semibold text-ink-gray-9">
            {{ course.data.title }}
          </div>
          <div class="my-3 leading-6 text-ink-gray-7">
            {{ course.data.short_introduction }}
          </div>
          <div v-html="course.data.description" class="mt-10"></div>
          <div class="mt-10">
            <div class="bg-gray-50 p-4 rounded">
              <div v-if="course.data.chapters && course.data.chapters.length">
                <div v-for="chapter in course.data.chapters" :key="chapter.name" class="mb-2">
                  <router-link
                    v-if="chapter.is_scorm_package"
                    :to="{ name: 'SCORMChapter', params: { courseName: course.data.name, chapterName: chapter.name } }"
                    class="text-primary hover:underline"
                  >
                    ▶ {{ chapter.title }} (SCORM)
                  </router-link>
                  <span v-else>
                    {{ chapter.title }}
                  </span>
                </div>
              </div>
              <div v-else>No chapters available.</div>
            </div>
          </div>
        </div>
        <div class="hidden md:block">
          <!-- Placeholder for CourseCardOverlay -->
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
  url: '/api/method/education.api.get_course_details',
  params: { course: props.courseName },
  auto: true,
})

const breadcrumbs = computed(() => [
  { label: 'Courses', route: { name: 'Courses' } },
  { label: course?.data?.title, route: { name: 'CourseDetail', params: { courseName: course?.data?.name } } },
])
</script> 