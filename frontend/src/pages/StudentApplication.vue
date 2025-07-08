<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-6">
          <div class="flex items-center">
            <h1 class="text-2xl font-bold text-gray-900">Student Application</h1>
          </div>
          <div class="flex items-center space-x-4">
            <div class="text-sm text-gray-500">
              Step {{ currentStep }} of {{ totalSteps }}
            </div>
            <div class="w-48 bg-gray-200 rounded-full h-2">
              <div 
                class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                :style="{ width: `${(currentStep / totalSteps) * 100}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="bg-white rounded-lg shadow-lg p-6">
        
        <!-- Step 1: Guardian Information -->
        <div v-if="currentStep === 1" class="space-y-6">
          <div class="text-center">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Guardian Information</h2>
            <p class="text-gray-600">Please provide information about the parent or guardian</p>
          </div>
          
          <!-- Guardian Type Selection -->
          <div class="space-y-4">
            <label class="block text-sm font-medium text-gray-700">Guardian Type</label>
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <button
                @click="guardianType = 'parent'"
                :class="[
                  'relative rounded-lg border p-4 text-left transition-all duration-200',
                  guardianType === 'parent' 
                    ? 'border-blue-500 bg-blue-50 text-blue-900' 
                    : 'border-gray-300 bg-white text-gray-900 hover:bg-gray-50'
                ]"
              >
                <div class="flex items-center">
                  <div class="flex-shrink-0">
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  </div>
                  <div class="ml-3">
                    <p class="text-sm font-medium">Parent</p>
                    <p class="text-xs text-gray-500">Father and Mother information</p>
                  </div>
                </div>
              </button>
              <button
                @click="guardianType = 'guardian'"
                :class="[
                  'relative rounded-lg border p-4 text-left transition-all duration-200',
                  guardianType === 'guardian' 
                    ? 'border-blue-500 bg-blue-50 text-blue-900' 
                    : 'border-gray-300 bg-white text-gray-900 hover:bg-gray-50'
                ]"
              >
                <div class="flex items-center">
                  <div class="flex-shrink-0">
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <div class="ml-3">
                    <p class="text-sm font-medium">Guardian</p>
                    <p class="text-xs text-gray-500">Other guardian information</p>
                  </div>
                </div>
              </button>
            </div>
          </div>

          <!-- Guardian Forms -->
          <div v-if="guardianType === 'parent'" class="space-y-8">
            <!-- Father Information -->
            <div class="bg-blue-50 rounded-lg p-6">
              <h3 class="text-lg font-medium text-blue-900 mb-4">Father Information</h3>
              <GuardianForm
                v-model="fatherData"
                :errors="validationErrors.father"
                @update="updateFatherData"
              />
            </div>

            <!-- Mother Information -->
            <div class="bg-pink-50 rounded-lg p-6">
              <h3 class="text-lg font-medium text-pink-900 mb-4">Mother Information</h3>
              <GuardianForm
                v-model="motherData"
                :errors="validationErrors.mother"
                @update="updateMotherData"
              />
            </div>
          </div>

          <div v-if="guardianType === 'guardian'" class="space-y-6">
            <!-- Guardian Information -->
            <div class="bg-gray-50 rounded-lg p-6">
              <h3 class="text-lg font-medium text-gray-900 mb-4">Guardian Information</h3>
              <GuardianForm
                v-model="guardianData"
                :errors="validationErrors.guardian"
                @update="updateGuardianData"
              />
            </div>
          </div>
        </div>

        <!-- Step 2: Student Type Selection -->
        <div v-if="currentStep === 2" class="space-y-6">
          <div class="text-center">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Student Type</h2>
            <p class="text-gray-600">Is this a new student or an existing student?</p>
          </div>
          
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <button
              @click="studentType = 'new'"
              :class="[
                'relative rounded-lg border p-6 text-left transition-all duration-200',
                studentType === 'new' 
                  ? 'border-blue-500 bg-blue-50 text-blue-900' 
                  : 'border-gray-300 bg-white text-gray-900 hover:bg-gray-50'
              ]"
            >
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <svg class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                </div>
                <div class="ml-4">
                  <p class="text-lg font-medium">New Student</p>
                  <p class="text-sm text-gray-500">First time enrollment</p>
                </div>
              </div>
            </button>
            <button
              @click="studentType = 'existing'"
              :class="[
                'relative rounded-lg border p-6 text-left transition-all duration-200',
                studentType === 'existing' 
                  ? 'border-blue-500 bg-blue-50 text-blue-900' 
                  : 'border-gray-300 bg-white text-gray-900 hover:bg-gray-50'
              ]"
            >
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <svg class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div class="ml-4">
                  <p class="text-lg font-medium">Existing Student</p>
                  <p class="text-sm text-gray-500">Already has a school ID</p>
                </div>
              </div>
            </button>
          </div>

          <!-- Existing Student School ID Input -->
          <div v-if="studentType === 'existing'" class="mt-6">
            <div class="bg-yellow-50 rounded-lg p-6">
              <h3 class="text-lg font-medium text-yellow-900 mb-4">School ID Lookup</h3>
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700">School ID</label>
                  <input
                    v-model="schoolIdInput"
                    @blur="searchExistingStudent"
                    type="text"
                    placeholder="Enter school ID (e.g., M1/10001/18)"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p v-if="validationErrors.schoolId" class="mt-1 text-sm text-red-600">
                    {{ validationErrors.schoolId }}
                  </p>
                </div>
                
                <div v-if="existingStudentData" class="bg-green-50 border border-green-200 rounded-md p-4">
                  <p class="text-sm text-green-800">
                    <strong>Student Found:</strong> {{ existingStudentData.first_name }} {{ existingStudentData.middle_name }} {{ existingStudentData.last_name }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- New Student Branch Selection -->
          <div v-if="studentType === 'new'" class="mt-6">
            <div class="bg-green-50 rounded-lg p-6">
              <h3 class="text-lg font-medium text-green-900 mb-4">Branch Selection</h3>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <button
                  @click="selectedBranch = 'M1'"
                  :class="[
                    'relative rounded-lg border p-4 text-left transition-all duration-200',
                    selectedBranch === 'M1' 
                      ? 'border-green-500 bg-green-100 text-green-900' 
                      : 'border-gray-300 bg-white text-gray-900 hover:bg-gray-50'
                  ]"
                >
                  <div class="flex items-center">
                    <div class="flex-shrink-0">
                      <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                    </div>
                    <div class="ml-3">
                      <p class="text-sm font-medium">Main Branch</p>
                      <p class="text-xs text-gray-500">School ID: M1/*****/18</p>
                    </div>
                  </div>
                </button>
                <button
                  @click="selectedBranch = 'M2'"
                  :class="[
                    'relative rounded-lg border p-4 text-left transition-all duration-200',
                    selectedBranch === 'M2' 
                      ? 'border-green-500 bg-green-100 text-green-900' 
                      : 'border-gray-300 bg-white text-gray-900 hover:bg-gray-50'
                  ]"
                >
                  <div class="flex items-center">
                    <div class="flex-shrink-0">
                      <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                    </div>
                    <div class="ml-3">
                      <p class="text-sm font-medium">Second Branch</p>
                      <p class="text-xs text-gray-500">School ID: M2/*****/18</p>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 3: Student Details -->
        <div v-if="currentStep === 3" class="space-y-6">
          <div class="text-center">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Student Details</h2>
            <p class="text-gray-600">Please provide the student's personal information</p>
          </div>
          
          <StudentDetailsForm
            v-model="studentData"
            :programs="programs"
            :academic-years="academicYears"
            :parent-contacts="parentContacts"
            :errors="validationErrors.student"
            @update="updateStudentData"
          />
        </div>

        <!-- Step 4: Address Information -->
        <div v-if="currentStep === 4" class="space-y-6">
          <div class="text-center">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Address Information</h2>
            <p class="text-gray-600">Please provide the student's address details</p>
          </div>
          
          <AddressForm
            v-model="addressData"
            :errors="validationErrors.address"
            @update="updateAddressData"
          />
        </div>

        <!-- Step 5: Preview -->
        <div v-if="currentStep === 5" class="space-y-6">
          <div class="text-center">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Application Preview</h2>
            <p class="text-gray-600">Please review your application before submitting</p>
          </div>
          
          <PreviewForm
            :guardian-type="guardianType"
            :father-data="fatherData"
            :mother-data="motherData"
            :guardian-data="guardianData"
            :student-data="studentData"
            :address-data="addressData"
            :school-id="generatedSchoolId || schoolIdInput"
            @edit="editStep"
          />
        </div>

        <!-- Navigation Buttons -->
        <div class="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
          <button
            v-if="currentStep > 1"
            @click="previousStep"
            class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
            Previous
          </button>
          <div v-else></div>
          
          <div class="flex space-x-3">
            <button
              v-if="currentStep < totalSteps"
              @click="nextStep"
              :disabled="!canProceed"
              class="inline-flex items-center px-6 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
              <svg class="ml-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
            
            <button
              v-if="currentStep === totalSteps"
              @click="submitApplication"
              :disabled="isSubmitting"
              class="inline-flex items-center px-6 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg v-if="isSubmitting" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ isSubmitting ? 'Submitting...' : 'Submit Application' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Success Modal -->
    <div v-if="showSuccessModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div class="mt-3 text-center">
          <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
            <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
          <h3 class="text-lg leading-6 font-medium text-gray-900 mt-2">Application Submitted Successfully!</h3>
          <div class="mt-2 px-7 py-3">
            <p class="text-sm text-gray-500">
              Your application has been submitted with ID: <strong>{{ submittedApplicationId }}</strong>
            </p>
          </div>
          <div class="items-center px-4 py-3 space-y-2">
            <button
              @click="addSibling"
              class="px-4 py-2 bg-blue-500 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300"
            >
              Add Another Child
            </button>
            <button
              @click="resetForm"
              class="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
            >
              Start New Application
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { call } from 'frappe-ui'
import GuardianForm from '../components/GuardianForm.vue'
import StudentDetailsForm from '../components/StudentDetailsForm.vue'
import AddressForm from '../components/AddressForm.vue'
import PreviewForm from '../components/PreviewForm.vue'

export default {
  name: 'StudentApplication',
  components: {
    GuardianForm,
    StudentDetailsForm,
    AddressForm,
    PreviewForm
  },
  setup() {
    const currentStep = ref(1)
    const totalSteps = ref(5)
    const guardianType = ref('parent')
    const studentType = ref('new')
    const selectedBranch = ref('M1')
    const schoolIdInput = ref('')
    const existingStudentData = ref(null)
    const generatedSchoolId = ref('')
    const isSubmitting = ref(false)
    const showSuccessModal = ref(false)
    const submittedApplicationId = ref('')
    const programs = ref([])
    const academicYears = ref([])

    const fatherData = reactive({
      guardian_name: '',
      email_address: '',
      mobile_number: '',
      alternate_number: '',
      education: '',
      occupation: '',
      work_address: ''
    })

    const motherData = reactive({
      guardian_name: '',
      email_address: '',
      mobile_number: '',
      alternate_number: '',
      education: '',
      occupation: '',
      work_address: ''
    })

    const guardianData = reactive({
      guardian_name: '',
      email_address: '',
      mobile_number: '',
      alternate_number: '',
      education: '',
      occupation: '',
      work_address: ''
    })

    const studentData = reactive({
      first_name: '',
      middle_name: '',
      last_name: '',
      date_of_birth: '',
      gender: '',
      student_email_id: '',
      student_mobile_number: '',
      program: '',
      academic_year: '',
      nationality: 'Ethiopian'
    })

    const addressData = reactive({
      address_line_1: '',
      address_line_2: '',
      city: 'Adama',
      state: '',
      pincode: '',
      country: 'Ethiopia'
    })

    const validationErrors = reactive({
      father: {},
      mother: {},
      guardian: {},
      student: {},
      address: {},
      schoolId: ''
    })

    const parentContacts = computed(() => {
      const contacts = []
      if (guardianType.value === 'parent') {
        if (fatherData.email_address) contacts.push({ label: `Father: ${fatherData.email_address}`, value: fatherData.email_address })
        if (fatherData.mobile_number) contacts.push({ label: `Father: ${fatherData.mobile_number}`, value: fatherData.mobile_number })
        if (motherData.email_address) contacts.push({ label: `Mother: ${motherData.email_address}`, value: motherData.email_address })
        if (motherData.mobile_number) contacts.push({ label: `Mother: ${motherData.mobile_number}`, value: motherData.mobile_number })
      } else if (guardianType.value === 'guardian') {
        if (guardianData.email_address) contacts.push({ label: `Guardian: ${guardianData.email_address}`, value: guardianData.email_address })
        if (guardianData.mobile_number) contacts.push({ label: `Guardian: ${guardianData.mobile_number}`, value: guardianData.mobile_number })
      }
      return contacts
    })

    const canProceed = computed(() => {
      switch (currentStep.value) {
        case 1:
          return guardianType.value === 'parent' 
            ? (fatherData.guardian_name && fatherData.email_address && motherData.guardian_name && motherData.email_address)
            : (guardianData.guardian_name && guardianData.email_address)
        case 2:
          return studentType.value === 'new' 
            ? selectedBranch.value 
            : existingStudentData.value
        case 3:
          return studentData.first_name && studentData.last_name && studentData.date_of_birth && studentData.program
        case 4:
          return addressData.address_line_1 && addressData.city
        case 5:
          return true
        default:
          return false
      }
    })

    const loadInitialData = async () => {
      try {
        const [programsResponse, yearsResponse] = await Promise.all([
          call('education.education.api.get_programs_for_application'),
          call('education.education.api.get_academic_years')
        ])
        programs.value = programsResponse
        academicYears.value = yearsResponse
      } catch (error) {
        console.error('Error loading initial data:', error)
      }
    }

    const generateSchoolId = async () => {
      try {
        const schoolId = await call('education.education.api.generate_school_id', {
          branch: selectedBranch.value
        })
        generatedSchoolId.value = schoolId
      } catch (error) {
        console.error('Error generating school ID:', error)
      }
    }

    const searchExistingStudent = async () => {
      if (!schoolIdInput.value) return
      
      try {
        const student = await call('education.education.api.search_student_by_school_id', {
          school_id: schoolIdInput.value
        })
        
        if (student) {
          existingStudentData.value = student
          validationErrors.schoolId = ''
        } else {
          existingStudentData.value = null
          validationErrors.schoolId = 'Student not found with this school ID'
        }
      } catch (error) {
        console.error('Error searching student:', error)
        validationErrors.schoolId = 'Error searching for student'
      }
    }

    const nextStep = async () => {
      if (currentStep.value === 2 && studentType.value === 'new') {
        await generateSchoolId()
      }
      
      if (currentStep.value === 2 && studentType.value === 'existing' && existingStudentData.value) {
        // Pre-populate student data from existing student
        studentData.first_name = existingStudentData.value.first_name
        studentData.middle_name = existingStudentData.value.middle_name || ''
        studentData.last_name = existingStudentData.value.last_name
      }
      
      if (currentStep.value < totalSteps.value) {
        currentStep.value++
      }
    }

    const previousStep = () => {
      if (currentStep.value > 1) {
        currentStep.value--
      }
    }

    const editStep = (step) => {
      currentStep.value = step
    }

    const updateFatherData = (data) => {
      Object.assign(fatherData, data)
    }

    const updateMotherData = (data) => {
      Object.assign(motherData, data)
    }

    const updateGuardianData = (data) => {
      Object.assign(guardianData, data)
    }

    const updateStudentData = (data) => {
      Object.assign(studentData, data)
    }

    const updateAddressData = (data) => {
      Object.assign(addressData, data)
    }

    const createGuardians = async () => {
      const guardians = []
      
      if (guardianType.value === 'parent') {
        // Create father guardian
        const fatherId = await call('education.education.api.create_guardian', fatherData)
        guardians.push({
          guardian: fatherId,
          guardian_name: fatherData.guardian_name,
          relation: 'Father'
        })
        
        // Create mother guardian
        const motherId = await call('education.education.api.create_guardian', motherData)
        guardians.push({
          guardian: motherId,
          guardian_name: motherData.guardian_name,
          relation: 'Mother'
        })
      } else {
        // Create guardian
        const guardianId = await call('education.education.api.create_guardian', guardianData)
        guardians.push({
          guardian: guardianId,
          guardian_name: guardianData.guardian_name,
          relation: 'Others'
        })
      }
      
      return guardians
    }

    const submitApplication = async () => {
      isSubmitting.value = true
      
      try {
        // Create guardians first
        const guardians = await createGuardians()
        
        // Prepare application data
        const applicationData = {
          ...studentData,
          ...addressData,
          custom_school_id: generatedSchoolId.value || schoolIdInput.value,
          guardians: guardians,
          siblings: [] // Will be populated later if needed
        }
        
        // Create application
        const applicationId = await call('education.education.api.create_student_application', applicationData)
        
        submittedApplicationId.value = applicationId
        showSuccessModal.value = true
        
      } catch (error) {
        console.error('Error submitting application:', error)
        alert('Error submitting application. Please try again.')
      } finally {
        isSubmitting.value = false
      }
    }

    const addSibling = () => {
      showSuccessModal.value = false
      // Reset only student-specific data, keep guardian data
      Object.assign(studentData, {
        first_name: '',
        middle_name: '',
        last_name: '',
        date_of_birth: '',
        gender: '',
        student_email_id: '',
        student_mobile_number: '',
        program: '',
        academic_year: '',
        nationality: 'Ethiopian'
      })
      
      currentStep.value = 2 // Start from student type selection
      studentType.value = 'new' // Default to new student for siblings
      selectedBranch.value = 'M1' // Reset branch selection
      generatedSchoolId.value = ''
    }

    const resetForm = () => {
      showSuccessModal.value = false
      currentStep.value = 1
      guardianType.value = 'parent'
      studentType.value = 'new'
      selectedBranch.value = 'M1'
      schoolIdInput.value = ''
      existingStudentData.value = null
      generatedSchoolId.value = ''
      submittedApplicationId.value = ''
      
      // Reset all form data
      Object.assign(fatherData, {
        guardian_name: '',
        email_address: '',
        mobile_number: '',
        alternate_number: '',
        education: '',
        occupation: '',
        work_address: ''
      })
      
      Object.assign(motherData, {
        guardian_name: '',
        email_address: '',
        mobile_number: '',
        alternate_number: '',
        education: '',
        occupation: '',
        work_address: ''
      })
      
      Object.assign(guardianData, {
        guardian_name: '',
        email_address: '',
        mobile_number: '',
        alternate_number: '',
        education: '',
        occupation: '',
        work_address: ''
      })
      
      Object.assign(studentData, {
        first_name: '',
        middle_name: '',
        last_name: '',
        date_of_birth: '',
        gender: '',
        student_email_id: '',
        student_mobile_number: '',
        program: '',
        academic_year: '',
        nationality: 'Ethiopian'
      })
      
      Object.assign(addressData, {
        address_line_1: '',
        address_line_2: '',
        city: 'Adama',
        state: '',
        pincode: '',
        country: 'Ethiopia'
      })
      
      // Clear validation errors
      Object.keys(validationErrors).forEach(key => {
        if (typeof validationErrors[key] === 'object') {
          validationErrors[key] = {}
        } else {
          validationErrors[key] = ''
        }
      })
    }

    onMounted(() => {
      loadInitialData()
    })

    return {
      currentStep,
      totalSteps,
      guardianType,
      studentType,
      selectedBranch,
      schoolIdInput,
      existingStudentData,
      generatedSchoolId,
      isSubmitting,
      showSuccessModal,
      submittedApplicationId,
      programs,
      academicYears,
      fatherData,
      motherData,
      guardianData,
      studentData,
      addressData,
      validationErrors,
      parentContacts,
      canProceed,
      searchExistingStudent,
      nextStep,
      previousStep,
      editStep,
      updateFatherData,
      updateMotherData,
      updateGuardianData,
      updateStudentData,
      updateAddressData,
      submitApplication,
      addSibling,
      resetForm
    }
  }
}
</script>

<style scoped>
/* Add any additional styling here */
</style> 