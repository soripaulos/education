import { createRouter, createWebHistory } from 'vue-router'
import { usersStore } from '@/stores/user'
import { sessionStore } from '@/stores/session'
import { studentStore } from '@/stores/student'

const routes = [
  { path: '/', redirect: '/schedule' },
  {
    path: '/schedule',
    name: 'Schedule',
    component: () => import('@/pages/Schedule.vue'),
  },
  {
    path: '/grades',
    name: 'Grades',
    component: () => import('@/pages/Grades.vue'),
  },
  {
    path: '/assessment-logs',
    name: 'AssessmentLogs',
    component: () => import('@/pages/AssessmentLogs.vue'),
  },
  {
    path: '/fees',
    name: 'Fees',
    component: () => import('@/pages/Fees.vue'),
  },
  {
    path: '/attendance',
    name: 'Attendance',
    component: () => import('@/pages/Attendance.vue'),
  },
  {
    path: '/evaluation',
    name: 'Evaluation',
    component: () => import('@/pages/Evaluation.vue'),
  },
  {
    path: '/teacher-evaluation',
    name: 'TeacherEvaluation',
    component: () => import('@/pages/TeacherEvaluation.vue'),
  },
  {
    path: '/courses',
    name: 'Courses',
    component: () => import('@/pages/Courses.vue'),
  },
  {
    path: '/courses/:courseName',
    name: 'CourseDetail',
    component: () => import('@/pages/CourseDetail.vue'),
    props: true,
  },
  {
    path: '/courses/:courseName/learn/:chapterName',
    name: 'SCORMChapter',
    component: () => import('@/pages/SCORMChapter.vue'),
    props: true,
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('./pages/Notifications.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('./pages/Settings.vue')
  },
  {
    path: '/:catchAll(.*)',
    redirect: '/schedule',
  },
]

let router = createRouter({
  history: createWebHistory('/student-portal'),
  routes,
})

router.beforeEach(async (to, from) => {
  const { isLoggedIn, user: sessionUser } = sessionStore()
  const { user } = usersStore()
  const { student } = studentStore()

  if (!isLoggedIn) {
    window.location.href = '/login'
    return await next(false)
  }

  if (user.data.length === 0) {
    await user.reload()
  }
  await student.reload()
})

export default router
