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
        <input
          id="date_of_birth"
          v-model="localData.date_of_birth"
          @input="updateData"
          type="date"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        />
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
          Student Email Address *
        </label>
        <div class="mt-1 relative">
          <input
            v-if="!useParentEmail"
            id="student_email_id"
            v-model="localData.student_email_id"
            @input="updateData"
            type="email"
            class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter student email address"
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

    // Watch for external changes to modelValue
    watch(() => props.modelValue, (newValue) => {
      Object.assign(localData, newValue)
    }, { deep: true })

    const updateData = () => {
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

    return {
      localData,
      useParentEmail,
      useParentMobile,
      updateData,
      toggleEmailSource,
      toggleMobileSource
    }
  }
}
</script>

<style scoped>
/* Add any additional styling here */
</style> 