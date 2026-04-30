<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
      <!-- Address Line 1 -->
      <div class="sm:col-span-2">
        <label for="address_line_1" class="block text-sm font-medium text-gray-700">
          Address Line 1 *
        </label>
        <input
          id="address_line_1"
          v-model="localData.address_line_1"
          @input="updateData"
          type="text"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter address line 1"
        />
        <p v-if="errors.address_line_1" class="mt-1 text-sm text-red-600">
          {{ errors.address_line_1 }}
        </p>
      </div>

      <!-- Address Line 2 -->
      <div class="sm:col-span-2">
        <label for="address_line_2" class="block text-sm font-medium text-gray-700">
          Address Line 2
        </label>
        <input
          id="address_line_2"
          v-model="localData.address_line_2"
          @input="updateData"
          type="text"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter address line 2 (optional)"
        />
        <p v-if="errors.address_line_2" class="mt-1 text-sm text-red-600">
          {{ errors.address_line_2 }}
        </p>
      </div>

      <!-- Subcity -->
      <div>
        <label for="state" class="block text-sm font-medium text-gray-700">
          Subcity *
        </label>
        <select
          id="state"
          v-model="localData.state"
          @change="updateData"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select subcity</option>
          <option value="Bole">Bole</option>
          <option value="Yeka">Yeka</option>
          <option value="Kirkos">Kirkos</option>
          <option value="Arada">Arada</option>
          <option value="Addis Ketema">Addis Ketema</option>
          <option value="Lideta">Lideta</option>
          <option value="Gulele">Gulele</option>
          <option value="Kolfe Keranio">Kolfe Keranio</option>
          <option value="Akaky Kaliti">Akaky Kaliti</option>
          <option value="Nifas Silk-Lafto">Nifas Silk-Lafto</option>
          <option value="Lemi Kura">Lemi Kura</option>
          <option value="Other">Other</option>
        </select>
        <p v-if="errors.state" class="mt-1 text-sm text-red-600">
          {{ errors.state }}
        </p>
      </div>

      <!-- Kebele -->
      <div>
        <label for="pincode" class="block text-sm font-medium text-gray-700">
          Kebele *
        </label>
        <input
          id="pincode"
          v-model="localData.pincode"
          @input="updateData"
          type="text"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter kebele"
        />
        <p v-if="errors.pincode" class="mt-1 text-sm text-red-600">
          {{ errors.pincode }}
        </p>
      </div>

      <!-- City -->
      <div>
        <label for="city" class="block text-sm font-medium text-gray-700">
          City *
        </label>
        <input
          id="city"
          v-model="localData.city"
          @input="updateData"
          type="text"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-gray-50"
          placeholder="City"
          readonly
        />
        <p class="mt-1 text-xs text-gray-500">
          City is set to Adama by default
        </p>
        <p v-if="errors.city" class="mt-1 text-sm text-red-600">
          {{ errors.city }}
        </p>
      </div>

      <!-- Country -->
      <div>
        <label for="country" class="block text-sm font-medium text-gray-700">
          Country *
        </label>
        <input
          id="country"
          v-model="localData.country"
          @input="updateData"
          type="text"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-gray-50"
          placeholder="Country"
          readonly
        />
        <p class="mt-1 text-xs text-gray-500">
          Country is set to Ethiopia by default
        </p>
        <p v-if="errors.country" class="mt-1 text-sm text-red-600">
          {{ errors.country }}
        </p>
      </div>
    </div>

    <!-- Additional Information -->
    <div class="bg-blue-50 border border-blue-200 rounded-md p-4">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <p class="text-sm text-blue-800">
            <strong>Note:</strong> Please provide the current residential address where the student lives. This address will be used for all official correspondence and emergency contacts.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { reactive, watch } from 'vue'

export default {
  name: 'AddressForm',
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
    const localData = reactive({ 
      city: 'Adama',
      country: 'Ethiopia',
      ...props.modelValue
    })

    // Watch for external changes to modelValue
    watch(() => props.modelValue, (newValue) => {
      Object.assign(localData, {
        city: 'Adama',
        country: 'Ethiopia',
        ...newValue
      })
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