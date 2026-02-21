<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
      <!-- Full Name -->
      <div class="sm:col-span-2">
        <label for="guardian_name" class="block text-sm font-medium text-gray-700">
          Full Name *
        </label>
        <input
          id="guardian_name"
          v-model="localData.guardian_name"
          @input="updateData"
          type="text"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter full name"
        />
        <p v-if="errors.guardian_name" class="mt-1 text-sm text-red-600">
          {{ errors.guardian_name }}
        </p>
      </div>

      <!-- Email Address -->
      <div>
        <label for="email_address" class="block text-sm font-medium text-gray-700">
          Email Address *
        </label>
        <input
          id="email_address"
          v-model="localData.email_address"
          @input="updateData"
          type="email"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter email address"
        />
        <p v-if="errors.email_address" class="mt-1 text-sm text-red-600">
          {{ errors.email_address }}
        </p>
      </div>

      <!-- Mobile Number -->
      <div>
        <label for="mobile_number" class="block text-sm font-medium text-gray-700">
          Mobile Number *
        </label>
        <input
          id="mobile_number"
          v-model="localData.mobile_number"
          @input="updateData"
          type="tel"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter mobile number"
        />
        <p v-if="errors.mobile_number" class="mt-1 text-sm text-red-600">
          {{ errors.mobile_number }}
        </p>
      </div>

      <!-- Alternate Number -->
      <div>
        <label for="alternate_number" class="block text-sm font-medium text-gray-700">
          Alternate Number
        </label>
        <input
          id="alternate_number"
          v-model="localData.alternate_number"
          @input="updateData"
          type="tel"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter alternate number"
        />
        <p v-if="errors.alternate_number" class="mt-1 text-sm text-red-600">
          {{ errors.alternate_number }}
        </p>
      </div>

      <!-- Education Level -->
      <div>
        <label for="education" class="block text-sm font-medium text-gray-700">
          Education Level
        </label>
        <select
          id="education"
          v-model="localData.education"
          @change="updateData"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select education level</option>
          <option value="No Formal Education">No Formal Education</option>
          <option value="Primary School">Primary School</option>
          <option value="Secondary School">Secondary School</option>
          <option value="High School">High School</option>
          <option value="Certificate">Certificate</option>
          <option value="Diploma">Diploma</option>
          <option value="Bachelor's Degree">Bachelor's Degree</option>
          <option value="Master's Degree">Master's Degree</option>
          <option value="PhD">PhD</option>
          <option value="Other">Other</option>
        </select>
        <p v-if="errors.education" class="mt-1 text-sm text-red-600">
          {{ errors.education }}
        </p>
      </div>

      <!-- Occupation -->
      <div>
        <label for="occupation" class="block text-sm font-medium text-gray-700">
          Occupation
        </label>
        <input
          id="occupation"
          v-model="localData.occupation"
          @input="updateData"
          type="text"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter occupation"
        />
        <p v-if="errors.occupation" class="mt-1 text-sm text-red-600">
          {{ errors.occupation }}
        </p>
      </div>

      <!-- Work Address -->
      <div class="sm:col-span-2">
        <label for="work_address" class="block text-sm font-medium text-gray-700">
          Work Address
        </label>
        <textarea
          id="work_address"
          v-model="localData.work_address"
          @input="updateData"
          rows="3"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter work address"
        ></textarea>
        <p v-if="errors.work_address" class="mt-1 text-sm text-red-600">
          {{ errors.work_address }}
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { reactive, watch } from 'vue'

export default {
  name: 'GuardianForm',
  props: {
    modelValue: {
      type: Object,
      required: true
    },
    errors: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['update:modelValue', 'update'],
  setup(props, { emit }) {
    const localData = reactive({ ...props.modelValue })

    // Watch for external changes to modelValue
    watch(() => props.modelValue, (newValue) => {
      Object.assign(localData, newValue)
    }, { deep: true })

    const updateData = () => {
      emit('update:modelValue', { ...localData })
      emit('update', { ...localData })
    }

    return {
      localData,
      updateData
    }
  }
}
</script>

<style scoped>
/* Add any additional styling here */
</style> 