<template>
  <div v-if="grades.data?.length > 0" class="container mx-auto p-4">
    <div class="bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-lg shadow-lg p-6 mb-6">
      <h3 class="text-2xl font-bold mb-4">Overall Performance</h3>
      <div class="flex flex-col md:flex-row justify-between items-center">
        <div class="mb-4 md:mb-0">
          <p class="text-lg">Total Score: <span class="font-semibold">{{ overallPerformance.totalScore }}</span>/<span class="font-semibold">{{ overallPerformance.maximumScore }}</span></p>
          <p class="text-lg">Grade: <span class="font-semibold">{{ overallPerformance.grade }}</span></p>
        </div>
        <div class="text-5xl font-extrabold">{{ overallPerformance.percentage }}%</div>
      </div>
    </div>

    <div v-for="(courseData, course) in groupedAssessments" 
         :key="course" 
         class="bg-white shadow-lg rounded-lg p-6 mb-6">
      <div @click="toggleCourse(course)" 
           class="flex justify-between items-center mb-4 cursor-pointer hover:bg-gray-50 p-2 rounded">
        <h3 class="text-xl font-semibold text-gray-800">{{ course }}</h3>
        <div class="flex items-center gap-3 text-lg">
          Course Average: 
          <span class="font-semibold">{{ calculateCourseAverage(courseData) }}%</span>
          <FeatherIcon 
            :name="expandedCourses[course] ? 'chevron-up' : 'chevron-down'"
            class="h-5 w-5 text-gray-500"
          />
        </div>
      </div>
      
      <div v-show="expandedCourses[course]" 
           class="overflow-x-auto transition-all duration-300 ease-in-out">
        
        <!-- Loop through each academic term for this course -->
        <div v-for="(termData, term) in groupedByTerm(courseData)" 
             :key="`${course}-${term}`"
             class="mb-4">
          
          <h4 class="text-lg font-medium text-gray-700 mb-2 pl-2 border-l-4 border-indigo-500">
            {{ term }}
          </h4>
          
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-100">
              <tr>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Assessment Criteria
                </th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Score
                </th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Grade
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              <tr v-for="detail in termData" 
                  :key="detail.id" 
                  class="hover:bg-gray-50">
                <td class="px-6 py-4 text-sm text-gray-900">{{ detail.assessment_criteria }}</td>
                <td class="px-6 py-4 text-sm text-gray-900">
                  {{ detail.score }}/{{ detail.maximum_score }}
                </td>
                <td class="px-6 py-4 text-sm text-gray-900 text-right">
                  <span class="px-2 py-1 rounded-full" 
                        :class="getGradeColor(detail.grade)">
                    {{ detail.grade }}
                  </span>
                </td>
              </tr>
              <!-- Term summary row -->
              <tr class="bg-gray-50">
                <td class="px-6 py-4 text-sm font-semibold text-gray-900">Term Average</td>
                <td class="px-6 py-4 text-sm font-semibold text-gray-900">
                  {{ calculateTermTotal(termData) }}/{{ calculateTermMaximum(termData) }}
                </td>
                <td class="px-6 py-4 text-sm font-semibold text-gray-900 text-right">
                  {{ calculateTermPercentage(termData) }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="bg-white shadow-lg rounded-lg p-6 mb-6">
      <h3 class="text-xl font-semibold mb-4 text-gray-800">Yearly Average</h3>
      <p class="text-lg">Year Average Score: <span class="font-semibold">{{ yearAverageScore }}</span></p>
    </div>
  </div>
  <div v-else>
    <MissingData message="No grades found" />
  </div>
</template>

<script setup>
import {
  Dropdown,
  FeatherIcon,
  createResource,
} from 'frappe-ui'
import { ref, computed } from 'vue'
import { studentStore } from '@/stores/student'
import MissingData from '@/components/MissingData.vue'

const expandedCourses = ref({})

const toggleCourse = (course) => {
  expandedCourses.value[course] = !expandedCourses.value[course]
}

const { getCurrentProgram, getStudentInfo } = studentStore()

let studentInfo = getStudentInfo().value
let currentProgram = getCurrentProgram().value

const allPrograms = ref([])
const selectedProgram = ref('')

const grades = createResource({
  url: '/api/method/education.education.api.get_assessment_results',
  method: 'POST',
  params: {
    student: studentInfo.name,
    program: currentProgram.program
  },
  auto: true,
  onSuccess: (response) => {
    console.log('Assessment results:', response);
    processGradesData(response);
    // Initialize all courses as expanded
    response.forEach(result => {
      if (result.course && !expandedCourses.value.hasOwnProperty(result.course)) {
        expandedCourses.value[result.course] = true
      }
    })
  },
  onError: (error) => {
    console.error('Error fetching assessment results:', error);
  }
})

const overallPerformance = ref({
  totalScore: 0,
  maximumScore: 0,
  grade: '',
  percentage: 0,
})

const assessmentDetails = ref([])
const yearAverageScore = ref(0)

const processGradesData = (data) => {
  if (!data?.length) {
    console.warn('No assessment data found');
    return;
  }
  
  // Process each assessment result
  const details = data.map(curr => ({
    id: curr.name,
    course: curr.course,
    academic_term: curr.assessment_group || curr.academic_term || 'Unknown Term',
    assessment_criteria: curr.assessment_criteria,
    score: curr.score,
    maximum_score: curr.detail_maximum_score,
    grade: curr.detail_grade
  }));
  
  console.log('Processed assessment details:', details);

  // Set overall performance
  const totalScore = details.reduce((sum, detail) => sum + detail.score, 0);
  const maximumScore = details.reduce((sum, detail) => sum + detail.maximum_score, 0);
  overallPerformance.value = {
    totalScore,
    maximumScore,
    grade: '', // Grade calculation logic can be added here
    percentage: ((totalScore / maximumScore) * 100).toFixed(1),
  }

  // Set assessment details for display
  assessmentDetails.value = details;

  // Calculate year average score
  yearAverageScore.value = overallPerformance.value.percentage;
}

const groupedAssessments = computed(() => {
  if (!assessmentDetails.value.length) return {};
  
  return assessmentDetails.value.reduce((acc, curr) => {
    if (!acc[curr.course]) {
      acc[curr.course] = [];
    }
    acc[curr.course].push(curr);
    return acc;
  }, {});
});

// Function to group course data by academic term
const groupedByTerm = (courseData) => {
  return courseData.reduce((acc, curr) => {
    if (!acc[curr.academic_term]) {
      acc[curr.academic_term] = [];
    }
    acc[curr.academic_term].push(curr);
    return acc;
  }, {});
};

// Calculate term-specific totals
const calculateTermTotal = (termData) => {
  return termData.reduce((sum, detail) => sum + detail.score, 0);
};

const calculateTermMaximum = (termData) => {
  return termData.reduce((sum, detail) => sum + detail.maximum_score, 0);
};

const calculateTermPercentage = (termData) => {
  const total = calculateTermTotal(termData);
  const maximum = calculateTermMaximum(termData);
  return maximum > 0 ? ((total / maximum) * 100).toFixed(1) : 0;
};

const calculateCourseAverage = (courseData) => {
  const totalScore = courseData.reduce((sum, detail) => sum + detail.score, 0);
  const maxScore = courseData.reduce((sum, detail) => sum + detail.maximum_score, 0);
  return ((totalScore / maxScore) * 100).toFixed(1);
};

const getGradeColor = (grade) => {
  const colors = {
    'A': 'bg-green-100 text-green-800',
    'B': 'bg-blue-100 text-blue-800',
    'C': 'bg-yellow-100 text-yellow-800',
    'D': 'bg-orange-100 text-orange-800',
    'F': 'bg-red-100 text-red-800',
  };
  return colors[grade.charAt(0)] || 'bg-gray-100 text-gray-800';
};
</script>

<style scoped>
.container {
  max-width: 1200px;
}

.bg-gradient-to-r {
  background-image: linear-gradient(to right, var(--tw-gradient-stops));
}

.from-indigo-500 {
  --tw-gradient-from: #6366f1;
  --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(99, 102, 241, 0));
}

.to-purple-500 {
  --tw-gradient-to: #a855f7;
}

.shadow-lg {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.font-extrabold {
  font-weight: 800;
}

.hover\:bg-gray-50:hover {
  background-color: #f9fafb;
}

.overflow-x-auto {
  overflow-x: auto;
}

.transition-all {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 300ms;
}

.cursor-pointer {
  cursor: pointer;
}
</style>
