<template>
  <div class="space-y-8">
    <div class="bg-green-50 border border-green-200 rounded-md p-4">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <p class="text-sm text-green-800">
            <strong>Ready to Submit!</strong> Please review all information carefully before submitting your application.
          </p>
        </div>
      </div>
    </div>

    <!-- Student Information -->
    <div class="bg-white border border-gray-200 rounded-lg p-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold text-gray-900">Student Information</h3>
        <button
          @click="$emit('edit', 3)"
          class="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          Edit
        </button>
      </div>
      
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <span class="text-sm text-gray-500">Full Name:</span>
          <p class="text-sm font-medium text-gray-900">
            {{ studentData.first_name }} {{ studentData.middle_name }} {{ studentData.last_name }}
          </p>
        </div>
        <div>
          <span class="text-sm text-gray-500">School ID:</span>
          <p class="text-sm font-medium text-gray-900">{{ schoolId }}</p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Date of Birth:</span>
          <p class="text-sm font-medium text-gray-900">{{ formatDate(studentData.date_of_birth) }}</p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Gender:</span>
          <p class="text-sm font-medium text-gray-900">{{ studentData.gender }}</p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Program:</span>
          <p class="text-sm font-medium text-gray-900">{{ studentData.program }}</p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Academic Year:</span>
          <p class="text-sm font-medium text-gray-900">{{ studentData.academic_year }}</p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Email:</span>
          <p class="text-sm font-medium text-gray-900">{{ studentData.student_email_id }}</p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Mobile:</span>
          <p class="text-sm font-medium text-gray-900">{{ studentData.student_mobile_number }}</p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Nationality:</span>
          <p class="text-sm font-medium text-gray-900">{{ studentData.nationality }}</p>
        </div>
      </div>
    </div>

    <!-- Guardian Information -->
    <div class="bg-white border border-gray-200 rounded-lg p-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold text-gray-900">Guardian Information</h3>
        <button
          @click="$emit('edit', 1)"
          class="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          Edit
        </button>
      </div>
      
      <div v-if="guardianType === 'parent'" class="space-y-6">
        <!-- Father Information -->
        <div class="bg-blue-50 rounded-lg p-4">
          <h4 class="text-md font-medium text-blue-900 mb-3">Father Information</h4>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <span class="text-sm text-gray-500">Name:</span>
              <p class="text-sm font-medium text-gray-900">{{ fatherData.guardian_name }}</p>
            </div>
            <div>
              <span class="text-sm text-gray-500">Email:</span>
              <p class="text-sm font-medium text-gray-900">{{ fatherData.email_address }}</p>
            </div>
            <div>
              <span class="text-sm text-gray-500">Mobile:</span>
              <p class="text-sm font-medium text-gray-900">{{ fatherData.mobile_number }}</p>
            </div>
            <div v-if="fatherData.alternate_number">
              <span class="text-sm text-gray-500">Alternate:</span>
              <p class="text-sm font-medium text-gray-900">{{ fatherData.alternate_number }}</p>
            </div>
            <div v-if="fatherData.education">
              <span class="text-sm text-gray-500">Education:</span>
              <p class="text-sm font-medium text-gray-900">{{ fatherData.education }}</p>
            </div>
            <div v-if="fatherData.occupation">
              <span class="text-sm text-gray-500">Occupation:</span>
              <p class="text-sm font-medium text-gray-900">{{ fatherData.occupation }}</p>
            </div>
            <div v-if="fatherData.work_address" class="sm:col-span-2">
              <span class="text-sm text-gray-500">Work Address:</span>
              <p class="text-sm font-medium text-gray-900">{{ fatherData.work_address }}</p>
            </div>
          </div>
        </div>

        <!-- Mother Information -->
        <div class="bg-pink-50 rounded-lg p-4">
          <h4 class="text-md font-medium text-pink-900 mb-3">Mother Information</h4>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <span class="text-sm text-gray-500">Name:</span>
              <p class="text-sm font-medium text-gray-900">{{ motherData.guardian_name }}</p>
            </div>
            <div>
              <span class="text-sm text-gray-500">Email:</span>
              <p class="text-sm font-medium text-gray-900">{{ motherData.email_address }}</p>
            </div>
            <div>
              <span class="text-sm text-gray-500">Mobile:</span>
              <p class="text-sm font-medium text-gray-900">{{ motherData.mobile_number }}</p>
            </div>
            <div v-if="motherData.alternate_number">
              <span class="text-sm text-gray-500">Alternate:</span>
              <p class="text-sm font-medium text-gray-900">{{ motherData.alternate_number }}</p>
            </div>
            <div v-if="motherData.education">
              <span class="text-sm text-gray-500">Education:</span>
              <p class="text-sm font-medium text-gray-900">{{ motherData.education }}</p>
            </div>
            <div v-if="motherData.occupation">
              <span class="text-sm text-gray-500">Occupation:</span>
              <p class="text-sm font-medium text-gray-900">{{ motherData.occupation }}</p>
            </div>
            <div v-if="motherData.work_address" class="sm:col-span-2">
              <span class="text-sm text-gray-500">Work Address:</span>
              <p class="text-sm font-medium text-gray-900">{{ motherData.work_address }}</p>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="space-y-6">
        <!-- Guardian Information -->
        <div class="bg-gray-50 rounded-lg p-4">
          <h4 class="text-md font-medium text-gray-900 mb-3">Guardian Information</h4>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <span class="text-sm text-gray-500">Name:</span>
              <p class="text-sm font-medium text-gray-900">{{ guardianData.guardian_name }}</p>
            </div>
            <div>
              <span class="text-sm text-gray-500">Email:</span>
              <p class="text-sm font-medium text-gray-900">{{ guardianData.email_address }}</p>
            </div>
            <div>
              <span class="text-sm text-gray-500">Mobile:</span>
              <p class="text-sm font-medium text-gray-900">{{ guardianData.mobile_number }}</p>
            </div>
            <div v-if="guardianData.alternate_number">
              <span class="text-sm text-gray-500">Alternate:</span>
              <p class="text-sm font-medium text-gray-900">{{ guardianData.alternate_number }}</p>
            </div>
            <div v-if="guardianData.education">
              <span class="text-sm text-gray-500">Education:</span>
              <p class="text-sm font-medium text-gray-900">{{ guardianData.education }}</p>
            </div>
            <div v-if="guardianData.occupation">
              <span class="text-sm text-gray-500">Occupation:</span>
              <p class="text-sm font-medium text-gray-900">{{ guardianData.occupation }}</p>
            </div>
            <div v-if="guardianData.work_address" class="sm:col-span-2">
              <span class="text-sm text-gray-500">Work Address:</span>
              <p class="text-sm font-medium text-gray-900">{{ guardianData.work_address }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Address Information -->
    <div class="bg-white border border-gray-200 rounded-lg p-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold text-gray-900">Address Information</h3>
        <button
          @click="$emit('edit', 4)"
          class="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          Edit
        </button>
      </div>
      
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div class="sm:col-span-2">
          <span class="text-sm text-gray-500">Address Line 1:</span>
          <p class="text-sm font-medium text-gray-900">{{ addressData.address_line_1 }}</p>
        </div>
        <div v-if="addressData.address_line_2" class="sm:col-span-2">
          <span class="text-sm text-gray-500">Address Line 2:</span>
          <p class="text-sm font-medium text-gray-900">{{ addressData.address_line_2 }}</p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Subcity:</span>
          <p class="text-sm font-medium text-gray-900">{{ addressData.state }}</p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Kebele:</span>
          <p class="text-sm font-medium text-gray-900">{{ addressData.pincode }}</p>
        </div>
        <div>
          <span class="text-sm text-gray-500">City:</span>
          <p class="text-sm font-medium text-gray-900">{{ addressData.city }}</p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Country:</span>
          <p class="text-sm font-medium text-gray-900">{{ addressData.country }}</p>
        </div>
      </div>
    </div>

    <!-- Terms and Conditions -->
    <div class="bg-white border border-gray-200 rounded-lg p-6">
      <div class="flex items-start">
        <div class="flex items-center h-5">
          <input
            id="terms"
            v-model="acceptTerms"
            type="checkbox"
            class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
        </div>
        <div class="ml-3 text-sm">
          <label for="terms" class="font-medium text-gray-700">
            I agree to the terms and conditions
          </label>
          <p class="text-gray-500">
            By submitting this application, I certify that all information provided is accurate and complete.
            I understand that any false information may result in rejection of the application.
          </p>
        </div>
      </div>
    </div>

    <!-- Summary Stats -->
    <div class="bg-gray-50 rounded-lg p-6">
      <h4 class="text-lg font-semibold text-gray-900 mb-4">Application Summary</h4>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ guardianType === 'parent' ? 2 : 1 }}</p>
          <p class="text-sm text-gray-500">Guardian(s)</p>
        </div>
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">1</p>
          <p class="text-sm text-gray-500">Student</p>
        </div>
        <div class="text-center">
          <p class="text-2xl font-bold text-purple-600">{{ studentData.program || 'N/A' }}</p>
          <p class="text-sm text-gray-500">Program</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'PreviewForm',
  props: {
    guardianType: {
      type: String,
      required: true
    },
    fatherData: {
      type: Object,
      default: () => ({})
    },
    motherData: {
      type: Object,
      default: () => ({})
    },
    guardianData: {
      type: Object,
      default: () => ({})
    },
    studentData: {
      type: Object,
      required: true
    },
    addressData: {
      type: Object,
      required: true
    },
    schoolId: {
      type: String,
      required: true
    }
  },
  emits: ['edit'],
  setup(props) {
    const acceptTerms = ref(false)

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }

    const canSubmit = computed(() => {
      return acceptTerms.value
    })

    return {
      acceptTerms,
      canSubmit,
      formatDate
    }
  }
}
</script>

<style scoped>
/* Add any additional styling here */
</style> 