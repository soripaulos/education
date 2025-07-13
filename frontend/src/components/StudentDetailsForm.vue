<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
      <!-- First Name -->
      <div>
        <label for="first_name" class="block text-sm font-medium text-gray-700">
          First Name *
        </label>
        <input
          id="first_name"
          v-model="localData.first_name"
          @input="updateData"
          type="text"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter first name"
        />
        <p v-if="errors.first_name" class="mt-1 text-sm text-red-600">
          {{ errors.first_name }}
        </p>
      </div>

      <!-- Middle Name -->
      <div>
        <label for="middle_name" class="block text-sm font-medium text-gray-700">
          Middle Name
        </label>
        <input
          id="middle_name"
          v-model="localData.middle_name"
          @input="updateData"
          type="text"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter middle name"
        />
        <p v-if="errors.middle_name" class="mt-1 text-sm text-red-600">
          {{ errors.middle_name }}
        </p>
      </div>

      <!-- Last Name -->
      <div>
        <label for="last_name" class="block text-sm font-medium text-gray-700">
          Last Name *
        </label>
        <input
          id="last_name"
          v-model="localData.last_name"
          @input="updateData"
          type="text"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter last name"
        />
        <p v-if="errors.last_name" class="mt-1 text-sm text-red-600">
          {{ errors.last_name }}
        </p>
      </div>

      <!-- Date of Birth -->
      <div>
        <label for="date_of_birth" class="block text-sm font-medium text-gray-700">
          Date of Birth *
        </label>
        <div class="space-y-2">
          <div class="flex items-center space-x-4">
            <label class="flex items-center">
              <input type="radio" v-model="datePickerType" value="gregorian" class="mr-2">
              <span class="text-sm text-gray-600">Gregorian Calendar</span>
            </label>
            <label class="flex items-center">
              <input type="radio" v-model="datePickerType" value="ethiopian" class="mr-2">
              <span class="text-sm text-gray-600">Ethiopian Calendar</span>
            </label>
          </div>
          <div v-if="datePickerType === 'gregorian'">
            <input
              id="date_of_birth"
              v-model="localData.date_of_birth"
              @input="updateData"
              type="date"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div v-if="datePickerType === 'ethiopian'" class="space-y-2">
            <div class="grid grid-cols-3 gap-2">
              <div>
                <label class="block text-xs font-medium text-gray-500">Day</label>
                <select v-model="ethiopianDate.day" @change="convertEthiopianToGregorian" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500">
                  <option value="">Day</option>
                  <option v-for="day in getEthiopianDays()" :key="day" :value="day">{{ day }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500">Month</label>
                <select v-model="ethiopianDate.month" @change="convertEthiopianToGregorian" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500">
                  <option value="">Month</option>
                  <option v-for="(month, index) in ethiopianMonths" :key="index" :value="index + 1">{{ month }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500">Year</label>
                <select v-model="ethiopianDate.year" @change="convertEthiopianToGregorian" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500">
                  <option value="">Year</option>
                  <option v-for="year in getEthiopianYears()" :key="year" :value="year">{{ year }}</option>
                </select>
              </div>
            </div>
            <div v-if="ethiopianDate.day && ethiopianDate.month && ethiopianDate.year" class="text-sm text-gray-600">
              <p>Ethiopian Date: {{ ethiopianDate.day }}/{{ ethiopianDate.month }}/{{ ethiopianDate.year }}</p>
              <p>Gregorian Date: {{ localData.date_of_birth || 'Converting...' }}</p>
            </div>
          </div>
        </div>
        <p v-if="errors.date_of_birth" class="mt-1 text-sm text-red-600">
          {{ errors.date_of_birth }}
        </p>
      </div>

      <!-- Gender -->
      <div>
        <label for="gender" class="block text-sm font-medium text-gray-700">
          Gender *
        </label>
        <select
          id="gender"
          v-model="localData.gender"
          @change="updateData"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select gender</option>
          <option value="Male">Male</option>
          <option value="Female">Female</option>
        </select>
        <p v-if="errors.gender" class="mt-1 text-sm text-red-600">
          {{ errors.gender }}
        </p>
      </div>

      <!-- Program -->
      <div>
        <label for="program" class="block text-sm font-medium text-gray-700">
          Grade/Program *
        </label>
        <select
          id="program"
          v-model="localData.program"
          @change="updateData"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select grade/program</option>
          <option v-for="program in programs" :key="program.name" :value="program.name">
            {{ program.program_name }}
          </option>
        </select>
        <p v-if="errors.program" class="mt-1 text-sm text-red-600">
          {{ errors.program }}
        </p>
      </div>

      <!-- Academic Year -->
      <div>
        <label for="academic_year" class="block text-sm font-medium text-gray-700">
          Academic Year *
        </label>
        <select
          id="academic_year"
          v-model="localData.academic_year"
          @change="updateData"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select academic year</option>
          <option v-for="year in academicYears" :key="year.name" :value="year.name">
            {{ year.name }}
          </option>
        </select>
        <p v-if="errors.academic_year" class="mt-1 text-sm text-red-600">
          {{ errors.academic_year }}
        </p>
      </div>

      <!-- Student Email -->
      <div>
        <label for="student_email_id" class="block text-sm font-medium text-gray-700">
          Student Email Address
        </label>
        <div class="mt-1 relative">
          <input
            v-if="!useParentEmail"
            id="student_email_id"
            v-model="localData.student_email_id"
            @input="updateData"
            type="email"
            class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter student email address (optional - will be auto-generated)"
          />
          <select
            v-else
            id="student_email_id"
            v-model="localData.student_email_id"
            @change="updateData"
            class="block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select email from parent/guardian</option>
            <option v-for="contact in parentContacts.filter(c => c.value.includes('@'))" :key="contact.value" :value="contact.value">
              {{ contact.label }}
            </option>
          </select>
        </div>
        <div class="mt-2 flex items-center">
          <input
            id="useParentEmail"
            v-model="useParentEmail"
            @change="toggleEmailSource"
            type="checkbox"
            class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label for="useParentEmail" class="ml-2 block text-sm text-gray-900">
            Use parent/guardian email
          </label>
        </div>
        <p v-if="errors.student_email_id" class="mt-1 text-sm text-red-600">
          {{ errors.student_email_id }}
        </p>
      </div>

      <!-- Student Mobile -->
      <div>
        <label for="student_mobile_number" class="block text-sm font-medium text-gray-700">
          Student Mobile Number *
        </label>
        <div class="mt-1 relative">
          <input
            v-if="!useParentMobile"
            id="student_mobile_number"
            v-model="localData.student_mobile_number"
            @input="updateData"
            type="tel"
            class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter student mobile number"
          />
          <select
            v-else
            id="student_mobile_number"
            v-model="localData.student_mobile_number"
            @change="updateData"
            class="block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select mobile from parent/guardian</option>
            <option v-for="contact in parentContacts.filter(c => !c.value.includes('@'))" :key="contact.value" :value="contact.value">
              {{ contact.label }}
            </option>
          </select>
        </div>
        <div class="mt-2 flex items-center">
          <input
            id="useParentMobile"
            v-model="useParentMobile"
            @change="toggleMobileSource"
            type="checkbox"
            class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label for="useParentMobile" class="ml-2 block text-sm text-gray-900">
            Use parent/guardian mobile
          </label>
        </div>
        <p v-if="errors.student_mobile_number" class="mt-1 text-sm text-red-600">
          {{ errors.student_mobile_number }}
        </p>
      </div>

      <!-- Nationality -->
      <div>
        <label for="nationality" class="block text-sm font-medium text-gray-700">
          Nationality
        </label>
        <input
          id="nationality"
          v-model="localData.nationality"
          @input="updateData"
          type="text"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter nationality"
        />
        <p v-if="errors.nationality" class="mt-1 text-sm text-red-600">
          {{ errors.nationality }}
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { reactive, ref, watch } from 'vue'

export default {
  name: 'StudentDetailsForm',
  props: {
    modelValue: {
      type: Object,
      required: true
    },
    programs: {
      type: Array,
      default: () => []
    },
    academicYears: {
      type: Array,
      default: () => []
    },
    parentContacts: {
      type: Array,
      default: () => []
    },
    errors: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['update:modelValue', 'update'],
  setup(props, { emit }) {
    const localData = reactive({ ...props.modelValue })
    const useParentEmail = ref(false)
    const useParentMobile = ref(false)
    
    // Ethiopian calendar related data
    const datePickerType = ref('gregorian')
    const ethiopianDate = reactive({
      day: '',
      month: '',
      year: ''
    })
    const ethiopianMonths = [
      'መስከረም', 'ጥቅምት', 'ኅዳር', 'ታኅሣስ',
      'ጥር', 'የካቲት', 'መጋቢት', 'ሚያዝያ',
      'ግንቦት', 'ሰኔ', 'ሐምሌ', 'ነሐሴ', 'ጷጉሜን'
    ]

    // Watch for external changes to modelValue
    watch(() => props.modelValue, (newValue) => {
      Object.assign(localData, newValue)
    }, { deep: true })

    const updateData = () => {
      // Generate email if not provided
      if (!localData.student_email_id && localData.first_name && localData.middle_name) {
        const firstName = localData.first_name.toLowerCase().replace(/\s+/g, '')
        const middleName = localData.middle_name.toLowerCase().replace(/\s+/g, '')
        localData.student_email_id = `${firstName}.${middleName}@m.b.s`
      }
      
      emit('update:modelValue', { ...localData })
      emit('update', { ...localData })
    }

    const toggleEmailSource = () => {
      if (!useParentEmail.value) {
        localData.student_email_id = ''
        updateData()
      }
    }

    const toggleMobileSource = () => {
      if (!useParentMobile.value) {
        localData.student_mobile_number = ''
        updateData()
      }
    }

    // Ethiopian calendar methods
    const getEthiopianDays = () => {
      if (!ethiopianDate.month) return []
      
      // Ethiopian months 1-12 have 30 days, month 13 has 5 or 6 days
      if (ethiopianDate.month == 13) {
        // Check if it's a leap year
        const year = parseInt(ethiopianDate.year)
        const isLeapYear = (year % 4 === 3)
        return Array.from({length: isLeapYear ? 6 : 5}, (_, i) => i + 1)
      } else {
        return Array.from({length: 30}, (_, i) => i + 1)
      }
    }

    const getEthiopianYears = () => {
      // Generate Ethiopian years (roughly 1980-2020 Ethiopian calendar)
      const currentYear = new Date().getFullYear()
      const currentEthiopianYear = currentYear - 7 // Approximate conversion
      const startYear = currentEthiopianYear - 30
      const endYear = currentEthiopianYear + 5
      
      return Array.from({length: endYear - startYear + 1}, (_, i) => startYear + i)
    }

    const convertEthiopianToGregorian = () => {
      if (!ethiopianDate.day || !ethiopianDate.month || !ethiopianDate.year) {
        return
      }
      
      try {
        const ethDay = parseInt(ethiopianDate.day)
        const ethMonth = parseInt(ethiopianDate.month)
        const ethYear = parseInt(ethiopianDate.year)
        
        // Simple Ethiopian to Gregorian conversion
        const gregorianDate = ethiopianToGregorian(ethYear, ethMonth, ethDay)
        
        if (gregorianDate) {
          localData.date_of_birth = gregorianDate
          updateData()
        }
      } catch (error) {
        console.error('Error converting Ethiopian date:', error)
      }
    }

    const ethiopianToGregorian = (ethYear, ethMonth, ethDay) => {
      // Simplified Ethiopian to Gregorian conversion
      // Ethiopian New Year (1 Meskerem) corresponds to September 11 (or 12 in leap years)
      
      // Convert Ethiopian year to approximate Gregorian year
      const gregYear = ethYear + 7 // Ethiopian calendar is ~7-8 years behind
      
      // Ethiopian New Year starts on September 11 (or 12 in leap years)
      const isLeapYear = (gregYear % 4 === 0 && gregYear % 100 !== 0) || (gregYear % 400 === 0)
      const newYearDay = isLeapYear ? 12 : 11
      
      // Calculate the day of year in Ethiopian calendar
      let dayOfYear = (ethMonth - 1) * 30 + ethDay
      
      // Create Ethiopian New Year date
      const ethiopianNewYear = new Date(gregYear, 8, newYearDay) // September is month 8
      
      // Add days to Ethiopian New Year
      const gregorianDate = new Date(ethiopianNewYear)
      gregorianDate.setDate(gregorianDate.getDate() + dayOfYear - 1)
      
      // Format as YYYY-MM-DD
      return gregorianDate.toISOString().split('T')[0]
    }

    return {
      localData,
      useParentEmail,
      useParentMobile,
      updateData,
      toggleEmailSource,
      toggleMobileSource,
      datePickerType,
      ethiopianDate,
      ethiopianMonths,
      getEthiopianDays,
      getEthiopianYears,
      convertEthiopianToGregorian
    }
  }
}
</script>

<style scoped>
/* Add any additional styling here */
</style> 