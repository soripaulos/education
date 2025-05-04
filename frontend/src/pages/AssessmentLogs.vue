<template>
  <div v-if="assessmentLogs.data?.length > 0" class="container mx-auto p-4">
    <div class="bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-lg shadow-lg p-6 mb-6">
      <h3 class="text-2xl font-bold mb-4">Assessment Log Performance</h3>
      <div class="flex flex-col md:flex-row justify-between items-center">
        <div class="mb-4 md:mb-0">
          <p class="text-lg">Total Score: <span class="font-semibold">{{ overallPerformance.totalScore }}</span>/<span class="font-semibold">{{ overallPerformance.maximumScore }}</span></p>
          <p class="text-lg">Grade: <span class="font-semibold">{{ overallPerformance.grade }}</span></p>
        </div>
        <div class="text-5xl font-extrabold">{{ formatPercentage(overallPerformance.percentage) }}</div>
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
          <span class="font-semibold">{{ formatPercentage(calculateCourseAverage(courseData)) }}</span>
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
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Comments
                </th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Date
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              <tr v-for="detail in sortAssessmentCriteria(termData)" 
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
                <td class="px-6 py-4 text-sm text-gray-900">{{ detail.comments || '-' }}</td>
                <td class="px-6 py-4 text-sm text-gray-900 text-right">
                  {{ formatDate(detail.entry_datetime) }}
                </td>
              </tr>
              <!-- Term total row -->
              <tr class="bg-gray-50">
                <td class="px-6 py-4 text-sm font-semibold text-gray-900">Term Total</td>
                <td class="px-6 py-4 text-sm font-semibold text-gray-900">
                  {{ calculateTermTotal(termData) }}/{{ calculateTermMaximum(termData) }}
                </td>
                <td class="px-6 py-4 text-sm font-semibold text-gray-900 text-right">
                  <span class="px-2 py-1 rounded-full" 
                       :class="getGradeColor(calculateTermGrade(termData))">
                    {{ calculateTermGrade(termData) }}
                  </span>
                </td>
                <td class="px-6 py-4"></td> <!-- Empty cell for comments -->
                <td class="px-6 py-4"></td> <!-- Empty cell for date -->
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Term Averages Component -->
    <div class="bg-white shadow-lg rounded-lg p-6 mb-6">
      <h3 class="text-xl font-semibold mb-4 text-gray-800">Term Averages</h3>
      <div v-for="(termAvg, term) in calculateAllTermAverages()" :key="term" class="mb-2">
        <div class="flex justify-between items-center p-2 border-b">
          <div class="text-lg text-gray-800">{{ term }}</div>
          <div class="flex items-center gap-4">
            <span class="text-lg">{{ termAvg.score }}/{{ termAvg.maximum }}</span>
            <span class="px-2 py-1 rounded-full font-semibold" 
                  :class="getGradeColor(termAvg.grade)">
              {{ termAvg.grade }}
            </span>
            <span class="text-lg font-semibold">{{ formatPercentage(termAvg.percentage) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-white shadow-lg rounded-lg p-6 mb-6">
      <h3 class="text-xl font-semibold mb-4 text-gray-800">Yearly Average</h3>
      <p class="text-lg">Year Average Score: <span class="font-semibold">{{ formatPercentage(yearAverageScore) }}</span></p>
    </div>
  </div>
  <div v-else>
    <MissingData message="No assessment logs found" />
  </div>
</template>

<script setup>
import {
  Dropdown,
  FeatherIcon,
  createResource,
} from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'
import { studentStore } from '@/stores/student'
import MissingData from '@/components/MissingData.vue'
import dayjs from 'dayjs'

const expandedCourses = ref({})

const toggleCourse = (course) => {
  expandedCourses.value[course] = !expandedCourses.value[course]
}

const { getCurrentProgram, getStudentInfo } = studentStore()

let studentInfo = getStudentInfo().value
let currentProgram = getCurrentProgram().value

const allPrograms = ref([])
const selectedProgram = ref('')

const assessmentLogs = createResource({
  url: '/api/method/education.education.api.get_assessment_log_entries',
  method: 'POST',
  params: {
    student: studentInfo.name,
    program: currentProgram.program
  },
  auto: true,
  onSuccess: (response) => {
    console.log('Assessment logs:', response);
    processLogsData(response);
    // Initialize all courses as expanded
    response.forEach(result => {
      if (result.course && !expandedCourses.value.hasOwnProperty(result.course)) {
        expandedCourses.value[result.course] = true
      }
    })
  },
  onError: (error) => {
    console.error('Error fetching assessment logs:', error);
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

const processLogsData = (data) => {
  if (!data?.length) {
    console.warn('No assessment log data found');
    return;
  }
  
  // Process each assessment log
  const details = data.map(curr => ({
    id: curr.name,
    course: curr.course,
    academic_term: curr.academic_term || 'Unknown Term',
    assessment_criteria: curr.assessment_criteria,
    score: curr.score,
    maximum_score: curr.detail_maximum_score,
    grade: curr.detail_grade,
    comments: curr.comments,
    entry_datetime: curr.entry_datetime
  }));
  
  console.log('Processed assessment details:', details);

  // Set overall performance
  const totalScore = details.reduce((sum, detail) => sum + detail.score, 0);
  const maximumScore = details.reduce((sum, detail) => sum + detail.maximum_score, 0);
  overallPerformance.value = {
    totalScore,
    maximumScore,
    grade: calculateOverallGrade(totalScore, maximumScore),
    percentage: ((totalScore / maximumScore) * 100) || 0,
  }

  // Set assessment details for display
  assessmentDetails.value = details;

  // Calculate year average score
  yearAverageScore.value = overallPerformance.value.percentage;
}

// Function to calculate overall grade based on percentage
const calculateOverallGrade = (totalScore, maximumScore) => {
  if (!maximumScore) return '';
  const percentage = (totalScore / maximumScore) * 100;
  
  // Basic grade calculation - this could be enhanced to match your grading scale
  if (percentage >= 90) return 'A';
  if (percentage >= 80) return 'B';
  if (percentage >= 70) return 'C';
  if (percentage >= 60) return 'D';
  return 'F';
}

const formatDate = (dateString) => {
  return dayjs(dateString).format('MMM D, YYYY')
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

// Sort assessment criteria in specific order
const sortAssessmentCriteria = (termData) => {
  const order = {
    'First Test': 1,
    'Second Test': 2,
    'Mid Exam': 3,
    'Final Exam': 4
  };
  
  return [...termData].sort((a, b) => {
    const orderA = order[a.assessment_criteria] || 999;
    const orderB = order[b.assessment_criteria] || 999;
    return orderA - orderB;
  });
};

// Calculate term-specific totals
const calculateTermTotal = (termData) => {
  return termData.reduce((sum, detail) => sum + detail.score, 0);
};

const calculateTermMaximum = (termData) => {
  return termData.reduce((sum, detail) => sum + detail.maximum_score, 0);
};

const calculateTermGrade = (termData) => {
  const total = calculateTermTotal(termData);
  const maximum = calculateTermMaximum(termData);
  
  if (!maximum) return '';
  
  const percentage = (total / maximum) * 100;
  
  // Basic grade calculation
  if (percentage >= 90) return 'A';
  if (percentage >= 80) return 'B';
  if (percentage >= 70) return 'C';
  if (percentage >= 60) return 'D';
  return 'F';
};

// Calculate course average
const calculateCourseAverage = (courseData) => {
  const total = courseData.reduce((sum, detail) => sum + detail.score, 0);
  const maximum = courseData.reduce((sum, detail) => sum + detail.maximum_score, 0);
  
  return maximum ? (total / maximum) * 100 : 0;
};

// Calculate averages for all terms
const calculateAllTermAverages = () => {
  const termAverages = {};
  
  // Group all assessment details by term
  const termGroups = assessmentDetails.value.reduce((acc, curr) => {
    if (!acc[curr.academic_term]) {
      acc[curr.academic_term] = [];
    }
    acc[curr.academic_term].push(curr);
    return acc;
  }, {});
  
  // Calculate average for each term
  for (const term in termGroups) {
    const termData = termGroups[term];
    const score = termData.reduce((sum, detail) => sum + detail.score, 0);
    const maximum = termData.reduce((sum, detail) => sum + detail.maximum_score, 0);
    const percentage = maximum ? (score / maximum) * 100 : 0;
    
    // Determine grade
    let grade = '';
    if (percentage >= 90) grade = 'A';
    else if (percentage >= 80) grade = 'B';
    else if (percentage >= 70) grade = 'C';
    else if (percentage >= 60) grade = 'D';
    else grade = 'F';
    
    termAverages[term] = {
      score,
      maximum,
      percentage,
      grade
    };
  }
  
  return termAverages;
};

// Format percentage for display
const formatPercentage = (value) => {
  return value ? `${value.toFixed(1)}%` : '0.0%';
};

// Determine color based on grade
const getGradeColor = (grade) => {
  switch (grade) {
    case 'A': return 'bg-green-500 text-white';
    case 'B': return 'bg-blue-500 text-white';
    case 'C': return 'bg-yellow-500 text-white';
    case 'D': return 'bg-orange-500 text-white';
    case 'F': return 'bg-red-500 text-white';
    default: return 'bg-gray-200';
  }
};
</script> 