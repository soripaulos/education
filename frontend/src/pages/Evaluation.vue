<template>
    <div class="p-6 relative">
      <!-- Sacred Geometry Background -->
      <div class="absolute inset-0 opacity-5 pointer-events-none overflow-hidden">
        <!-- Fibonacci Spiral -->
        <div class="absolute top-0 right-0 w-96 h-96">
          <svg viewBox="0 0 100 100" class="w-full h-full">
            <path d="M50 10 A40 40 0 0 1 90 50 A30 30 0 0 1 50 80 A20 20 0 0 1 30 60 A10 10 0 0 1 40 50"
                  fill="none" stroke="currentColor" stroke-width="0.5"/>
            <!-- Golden Ratio Rectangles -->
            <rect x="20" y="20" width="61.8" height="38.2" fill="none" stroke="currentColor" stroke-width="0.3"/>
            <rect x="30" y="30" width="38.2" height="23.6" fill="none" stroke="currentColor" stroke-width="0.3"/>
            <!-- Sacred Circles -->
            <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="0.3"/>
            <circle cx="50" cy="50" r="25" fill="none" stroke="currentColor" stroke-width="0.3"/>
            <circle cx="50" cy="50" r="15" fill="none" stroke="currentColor" stroke-width="0.3"/>
          </svg>
        </div>
      </div>
  
      <div class="relative">
        <!-- Header with sacred geometry accent -->
        <div class="mb-6">
          <h2 class="text-2xl font-bold relative inline-block">
            Student Evaluation
            <div class="absolute -bottom-1 left-0 w-full h-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"></div>
          </h2>
          <p class="text-gray-600 mt-2">Performance metrics and assessment</p>
        </div>
  
        <!-- Loading State with sacred geometry spinner -->
        <div v-if="evaluation.loading" class="flex justify-center items-center h-64">
          <div class="sacred-spinner"></div>
        </div>
  
        <!-- Content -->
        <div v-else class="space-y-6">
          <!-- Metadata with geometric accents -->
          <div v-if="hasData" class="text-sm bg-gradient-to-r from-gray-50 to-white p-4 rounded-lg border border-gray-100">
            <div class="flex items-center space-x-4">
              <div v-for="(value, key) in metadata" :key="key" class="flex items-center">
                <span class="w-2 h-2 rounded-full bg-blue-500 mr-2"></span>
                <span class="font-medium">{{ formatMetadataLabel(key) }}:</span>
                <span class="ml-1 text-gray-600">{{ formatMetadataValue(key, value) }}</span>
              </div>
            </div>
          </div>
  
          <!-- Performance Chart Card -->
          <Card class="overflow-hidden bg-white shadow-sm hover:shadow-md transition-shadow duration-300">
            <div class="p-6">
              <h3 class="text-lg font-semibold mb-6 flex items-center">
                <div class="w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded mr-3"></div>
                Performance Metrics
              </h3>
              
              <!-- Modern Performance Chart -->
              <div class="relative">
                <div v-if="hasData" class="space-y-8">
                  <!-- Chart Container with Grid Layout -->
                  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div v-for="(metric, index) in metrics" :key="metric.key"
                         class="relative p-4 rounded-xl bg-gradient-to-br from-white to-gray-50 border border-gray-100 
                                shadow-sm hover:shadow-md transition-all duration-300 group">
                      <!-- Metric Header -->
                      <div class="flex items-center justify-between mb-3">
                        <h4 class="text-sm font-medium text-gray-700">{{ metric.label }}</h4>
                        <div class="w-2 h-2 rounded-full" 
                             :class="getMetricDotColor(chartData.values[index])"></div>
                      </div>
                      
                      <!-- Vertical Bar Chart -->
                      <div class="relative h-32 flex items-end justify-center">
                        <div class="relative w-full max-w-[80px]">
                          <!-- Background Bar -->
                          <div class="absolute inset-0 bg-gray-100 rounded-full"></div>
                          
                          <!-- Progress Bar with Gradient -->
                          <div class="absolute bottom-0 w-full rounded-full transition-all duration-700 ease-out"
                               :class="getMetricGradient(index)"
                               :style="{
                                 height: `${chartData.values[index] * 100}%`,
                                 transform: 'translateY(2px)'
                               }">
                            <!-- Animated Glow Effect -->
                            <div class="absolute inset-0 rounded-full opacity-0 group-hover:opacity-20
                                      bg-gradient-to-t from-white via-transparent to-transparent
                                      transition-opacity duration-300"></div>
                          </div>
                        </div>
                        
                        <!-- Value Label -->
                        <div class="absolute -top-1 left-1/2 transform -translate-x-1/2
                                  px-2 py-1 rounded-full text-xs font-semibold
                                  bg-white shadow-sm border border-gray-100
                                  transition-all duration-300 group-hover:scale-110">
                          {{ formatPercentage(chartData.values[index]) }}
                        </div>
                      </div>
                      
                      <!-- Target Line -->
                      <div class="absolute left-4 right-4 h-px bg-gray-200"
                           style="bottom: calc(32px * 0.75)">
                        <div class="absolute -top-4 right-0 text-xs text-gray-400">Target 75%</div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Interactive Legend -->
                  <div class="flex flex-wrap gap-4 justify-center">
                    <div v-for="(metric, index) in metrics" :key="metric.key"
                         class="flex items-center gap-2 px-3 py-1.5 rounded-full
                                bg-gradient-to-r from-gray-50 to-white
                                border border-gray-100 shadow-sm
                                hover:shadow-md transition-all duration-300
                                cursor-pointer group">
                      <div class="w-2 h-2 rounded-full transition-transform duration-300 group-hover:scale-125"
                           :class="getMetricDotColor(chartData.values[index])"></div>
                      <span class="text-sm text-gray-600">{{ metric.label }}</span>
                      <span class="text-xs font-medium ml-1">
                        {{ formatPercentage(chartData.values[index]) }}
                      </span>
                    </div>
                  </div>
                </div>
                
                <!-- No Data State -->
                <div v-else class="flex flex-col items-center justify-center py-12 px-4">
                  <div class="w-16 h-16 mb-4 text-gray-300">
                    <svg class="w-full h-full" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <p class="text-gray-500 text-center">No evaluation data available</p>
                </div>
              </div>
            </div>
          </Card>
  
          <!-- After the chart card -->
          <Card class="mt-6">
            <div class="p-4">
              <!-- Collapsible Header -->
              <button 
                @click="showAnalysis = !showAnalysis"
                class="w-full flex items-center justify-between p-3 rounded-lg bg-gradient-to-r from-gray-50 to-white group hover:from-indigo-50 hover:to-white transition-all duration-300"
              >
                <div class="flex items-center">
                  <BarChart class="w-5 h-5 text-indigo-500 mr-2"/>
                  <span class="text-lg font-semibold text-gray-700">Detailed Analysis</span>
                </div>
                <ChevronRight 
                  class="w-5 h-5 text-gray-400 transition-transform duration-200 group-hover:text-indigo-500"
                  :class="{ 'transform rotate-90': showAnalysis }"
                />
              </button>
  
              <!-- Analysis Content -->
              <div v-if="showAnalysis" 
                   class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-6 transition-all duration-300">
                
                <!-- Academic Performance -->
                <div class="space-y-4">
                  <h4 class="font-medium text-gray-700 flex items-center">
                    <GraduationCap class="w-4 h-4 mr-2 text-indigo-500"/>
                    Academic Performance
                  </h4>
                  <div class="space-y-3">
                    <div v-for="metric in academicMetrics" :key="metric.key" class="space-y-1">
                      <div class="flex justify-between text-sm">
                        <span class="text-gray-600">{{ metric.label }}</span>
                        <span class="font-medium">{{ formatPercentage(getMetricAverage(metric.key)) }}</span>
                      </div>
                      <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div 
                          class="h-full rounded-full transition-all duration-500"
                          :class="getProgressColorClass(getMetricAverage(metric.key))"
                          :style="{ width: `${getMetricAverage(metric.key) * 100}%` }"
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
  
                <!-- Behavioral Metrics -->
                <div class="space-y-4">
                  <h4 class="font-medium text-gray-700 flex items-center">
                    <Users class="w-4 h-4 mr-2 text-purple-500"/>
                    Behavioral Metrics
                  </h4>
                  <div class="space-y-3">
                    <div v-for="metric in behavioralMetrics" :key="metric.key" class="space-y-1">
                      <div class="flex justify-between text-sm">
                        <span class="text-gray-600">{{ metric.label }}</span>
                        <span class="font-medium">{{ formatPercentage(getMetricAverage(metric.key)) }}</span>
                      </div>
                      <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div 
                          class="h-full rounded-full transition-all duration-500"
                          :class="getProgressColorClass(getMetricAverage(metric.key))"
                          :style="{ width: `${getMetricAverage(metric.key) * 100}%` }"
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
  
                <!-- Growth & Development Analysis -->
                <div class="md:col-span-2 space-y-4">
                  <h4 class="font-medium text-gray-700 flex items-center">
                    <Target class="w-4 h-4 mr-2 text-indigo-500"/>
                    Growth & Development Analysis
                  </h4>
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <!-- Academic Progress -->
                    <div class="p-4 rounded-lg bg-white border border-gray-100 shadow-sm">
                      <div class="flex items-center justify-between mb-3">
                        <span class="text-sm font-medium text-gray-600">Academic Progress</span>
                        <GraduationCap class="w-4 h-4 text-blue-400"/>
                      </div>
                      <div class="space-y-3">
                        <div class="flex items-center justify-between">
                          <span class="text-xs text-gray-500">Homework</span>
                          <div class="flex items-center">
                            <div class="h-1.5 w-16 bg-gray-100 rounded-full overflow-hidden mr-2">
                              <div 
                                class="h-full bg-blue-400 transition-all duration-300"
                                :style="{ width: `${evaluation.data?.evaluations[0]?.homework * 100}%` }"
                              ></div>
                            </div>
                            <span class="text-xs font-medium">
                              {{ formatPercentage(evaluation.data?.evaluations[0]?.homework || 0) }}
                            </span>
                          </div>
                        </div>
                        <div class="flex items-center justify-between">
                          <span class="text-xs text-gray-500">Tests</span>
                          <div class="flex items-center">
                            <div class="h-1.5 w-16 bg-gray-100 rounded-full overflow-hidden mr-2">
                              <div 
                                class="h-full bg-blue-400 transition-all duration-300"
                                :style="{ width: `${evaluation.data?.evaluations[0]?.tests * 100}%` }"
                              ></div>
                            </div>
                            <span class="text-xs font-medium">
                              {{ formatPercentage(evaluation.data?.evaluations[0]?.tests || 0) }}
                            </span>
                          </div>
                        </div>
                        <div class="flex items-center justify-between">
                          <span class="text-xs text-gray-500">Proficiency</span>
                          <div class="flex items-center">
                            <div class="h-1.5 w-16 bg-gray-100 rounded-full overflow-hidden mr-2">
                              <div 
                                class="h-full bg-blue-400 transition-all duration-300"
                                :style="{ width: `${evaluation.data?.evaluations[0]?.proficiency * 100}%` }"
                              ></div>
                            </div>
                            <span class="text-xs font-medium">
                              {{ formatPercentage(evaluation.data?.evaluations[0]?.proficiency || 0) }}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
  
                    <!-- Social & Communication -->
                    <div class="p-4 rounded-lg bg-white border border-gray-100 shadow-sm">
                      <div class="flex items-center justify-between mb-3">
                        <span class="text-sm font-medium text-gray-600">Social Skills</span>
                        <Users class="w-4 h-4 text-purple-400"/>
                      </div>
                      <div class="space-y-3">
                        <div class="flex items-center justify-between">
                          <span class="text-xs text-gray-500">Peer Relations</span>
                          <div class="flex items-center">
                            <div class="h-1.5 w-16 bg-gray-100 rounded-full overflow-hidden mr-2">
                              <div 
                                class="h-full bg-purple-400 transition-all duration-300"
                                :style="{ width: `${evaluation.data?.evaluations[0]?.communicationpeer_relationships * 100}%` }"
                              ></div>
                            </div>
                            <span class="text-xs font-medium">
                              {{ formatPercentage(evaluation.data?.evaluations[0]?.communicationpeer_relationships || 0) }}
                            </span>
                          </div>
                        </div>
                        <div class="flex items-center justify-between">
                          <span class="text-xs text-gray-500">Communication</span>
                          <div class="flex items-center">
                            <div class="h-1.5 w-16 bg-gray-100 rounded-full overflow-hidden mr-2">
                              <div 
                                class="h-full bg-purple-400 transition-all duration-300"
                                :style="{ width: `${evaluation.data?.evaluations[0]?.speaking_and_communication_skills * 100}%` }"
                              ></div>
                            </div>
                            <span class="text-xs font-medium">
                              {{ formatPercentage(evaluation.data?.evaluations[0]?.speaking_and_communication_skills || 0) }}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
  
                    <!-- Behavioral Indicators -->
                    <div class="p-4 rounded-lg bg-white border border-gray-100 shadow-sm">
                      <div class="flex items-center justify-between mb-3">
                        <span class="text-sm font-medium text-gray-600">Behavioral Traits</span>
                        <Shield class="w-4 h-4 text-emerald-400"/>
                      </div>
                      <div class="space-y-3">
                        <div class="flex items-center justify-between">
                          <span class="text-xs text-gray-500">Discipline</span>
                          <div class="flex items-center">
                            <div class="h-1.5 w-16 bg-gray-100 rounded-full overflow-hidden mr-2">
                              <div 
                                class="h-full bg-emerald-400 transition-all duration-300"
                                :style="{ width: `${evaluation.data?.evaluations[0]?.discipline * 100}%` }"
                              ></div>
                            </div>
                            <span class="text-xs font-medium">
                              {{ formatPercentage(evaluation.data?.evaluations[0]?.discipline || 0) }}
                            </span>
                          </div>
                        </div>
                        <div class="flex items-center justify-between">
                          <span class="text-xs text-gray-500">Hygiene</span>
                          <div class="flex items-center">
                            <div class="h-1.5 w-16 bg-gray-100 rounded-full overflow-hidden mr-2">
                              <div 
                                class="h-full bg-emerald-400 transition-all duration-300"
                                :style="{ width: `${evaluation.data?.evaluations[0]?.hygiene * 100}%` }"
                              ></div>
                            </div>
                            <span class="text-xs font-medium">
                              {{ formatPercentage(evaluation.data?.evaluations[0]?.hygiene || 0) }}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
  
                    <!-- Achievements Section -->
                    <div v-if="evaluation.data?.evaluations.length > 0" 
                         class="md:col-span-3 p-4 rounded-lg bg-gradient-to-r from-indigo-50 to-purple-50 shadow-sm">
                      <div class="flex items-center mb-4">
                        <Trophy class="w-5 h-5 text-amber-500 mr-3"/>
                        <span class="text-base font-semibold text-gray-800">Achievements & Notes</span>
                      </div>
                      <div v-for="evaluation in evaluation.data.evaluations" :key="evaluation.name" class="mb-2">
                        <p class="text-base text-gray-700">
                          {{ evaluation.achievements }}
                        </p>
                      </div>
                    </div>
  
                    <!-- Behavioral Heatmap -->
                    <div class="md:col-span-3 p-4 rounded-lg bg-white border border-gray-100 shadow-sm mt-4">
                      <div class="flex items-center mb-4">
                        <Flag class="w-4 h-4 text-red-500 mr-2"/>
                        <h4 class="font-medium text-gray-700">Behavioral Incidents Heatmap</h4>
                      </div>
  
                      <div class="space-y-6">
                        <!-- Late to Class -->
                        <div>
                          <div class="flex items-center justify-between mb-2">
                            <div class="flex items-center gap-2">
                              <Clock class="w-4 h-4 text-amber-500"/>
                              <span class="text-sm text-gray-600">Late to Class</span>
                            </div>
                            <span class="text-xs font-medium bg-amber-50 text-amber-700 px-2 py-1 rounded-full">
                              {{ getBehaviorCount('late') }} incidents
                            </span>
                          </div>
                          <div class="grid grid-cols-12 gap-1">
                            <div v-for="month in 12" :key="month" 
                                 class="aspect-square rounded-sm relative group cursor-pointer"
                                 :class="getHeatmapColor('late', month)">
                              <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 bg-black/50 text-white text-xs rounded-sm transition-opacity">
                                {{ new Date(2024, month-1).toLocaleString('default', { month: 'short' }) }}
                              </div>
                            </div>
                          </div>
                        </div>
  
                        <!-- Breaking Rules -->
                        <div>
                          <div class="flex items-center justify-between mb-2">
                            <div class="flex items-center gap-2">
                              <AlertTriangle class="w-4 h-4 text-red-500"/>
                              <span class="text-sm text-gray-600">Breaking Rules</span>
                            </div>
                            <span class="text-xs font-medium bg-red-50 text-red-700 px-2 py-1 rounded-full">
                              {{ getBehaviorCount('breaking_rules') }} incidents
                            </span>
                          </div>
                          <div class="grid grid-cols-12 gap-1">
                            <div v-for="month in 12" :key="month" 
                                 class="aspect-square rounded-sm relative group cursor-pointer"
                                 :class="getHeatmapColor('breaking_rules', month)">
                              <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 bg-black/50 text-white text-xs rounded-sm transition-opacity">
                                {{ new Date(2024, month-1).toLocaleString('default', { month: 'short' }) }}
                              </div>
                            </div>
                          </div>
                        </div>
  
                        <!-- Fight/Conflict -->
                        <div>
                          <div class="flex items-center justify-between mb-2">
                            <div class="flex items-center gap-2">
                              <Swords class="w-4 h-4 text-red-500"/>
                              <span class="text-sm text-gray-600">Fight/Conflict</span>
                            </div>
                            <span class="text-xs font-medium bg-red-50 text-red-700 px-2 py-1 rounded-full">
                              {{ getBehaviorCount('fight') }} incidents
                            </span>
                          </div>
                          <div class="grid grid-cols-12 gap-1">
                            <div v-for="month in 12" :key="month" 
                                 class="aspect-square rounded-sm relative group cursor-pointer"
                                 :class="getHeatmapColor('fight', month)">
                              <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 bg-black/50 text-white text-xs rounded-sm transition-opacity">
                                {{ new Date(2024, month-1).toLocaleString('default', { month: 'short' }) }}
                              </div>
                            </div>
                          </div>
                        </div>
  
                        <!-- Sick -->
                        <div>
                          <div class="flex items-center justify-between mb-2">
                            <div class="flex items-center gap-2">
                              <Thermometer class="w-4 h-4 text-yellow-500"/>
                              <span class="text-sm text-gray-600">Sick</span>
                            </div>
                            <span class="text-xs font-medium bg-yellow-50 text-yellow-700 px-2 py-1 rounded-full">
                              {{ getBehaviorCount('sick') }} incidents
                            </span>
                          </div>
                          <div class="grid grid-cols-12 gap-1">
                            <div v-for="month in 12" :key="month" 
                                 class="aspect-square rounded-sm relative group cursor-pointer"
                                 :class="getHeatmapColor('sick', month)">
                              <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 bg-black/50 text-white text-xs rounded-sm transition-opacity">
                                {{ new Date(2024, month-1).toLocaleString('default', { month: 'short' }) }}
                              </div>
                            </div>
                          </div>
                        </div>
  
                        <!-- Missing Items -->
                        <div>
                          <div class="flex items-center justify-between mb-2">
                            <div class="flex items-center gap-2">
                              <Package class="w-4 h-4 text-orange-500"/>
                              <span class="text-sm text-gray-600">Missing Items</span>
                            </div>
                            <span class="text-xs font-medium bg-orange-50 text-orange-700 px-2 py-1 rounded-full">
                              {{ getBehaviorCount('incomplete_school_items') }} incidents
                            </span>
                          </div>
                          <div class="grid grid-cols-12 gap-1">
                            <div v-for="month in 12" :key="month" 
                                 class="aspect-square rounded-sm relative group cursor-pointer"
                                 :class="getHeatmapColor('incomplete_school_items', month)">
                              <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 bg-black/50 text-white text-xs rounded-sm transition-opacity">
                                {{ new Date(2024, month-1).toLocaleString('default', { month: 'short' }) }}
                              </div>
                            </div>
                          </div>
                        </div>
  
                        <!-- Missing Homework -->
                        <div>
                          <div class="flex items-center justify-between mb-2">
                            <div class="flex items-center gap-2">
                              <BookX class="w-4 h-4 text-purple-500"/>
                              <span class="text-sm text-gray-600">Missing Homework</span>
                            </div>
                            <span class="text-xs font-medium bg-purple-50 text-purple-700 px-2 py-1 rounded-full">
                              {{ getBehaviorCount('homework_not_done') }} incidents
                            </span>
                          </div>
                          <div class="grid grid-cols-12 gap-1">
                            <div v-for="month in 12" :key="month" 
                                 class="aspect-square rounded-sm relative group cursor-pointer"
                                 :class="getHeatmapColor('homework_not_done', month)">
                              <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 bg-black/50 text-white text-xs rounded-sm transition-opacity">
                                {{ new Date(2024, month-1).toLocaleString('default', { month: 'short' }) }}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>     
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { computed, onMounted, ref, watch, onUnmounted, nextTick } from 'vue'
  import { evaluationStore } from '@/stores/evaluation'
  import { studentStore } from '@/stores/student'
  import { Card } from 'frappe-ui'
  import dayjs from 'dayjs'
  import { debounce } from 'lodash'
  import { ChevronRight, TrendingUp, Minus, GraduationCap, Users, CalendarCheck, BookOpen, MessageSquare, Flag, BarChart, AlertCircle, Target, Clock, Backpack, Shield, Trophy, AlertTriangle, Swords, Thermometer, BookX, Package } from 'lucide-vue-next'
  
  // Store access
  const { evaluation } = evaluationStore()
  const { student } = studentStore()
  
  // Debounced fetch function
  const fetchEvaluation = debounce(async (studentId) => {
    if (!studentId) return
    
    try {
      await evaluation.submit({
        student_email: studentId
      })
    } catch (error) {
      console.error('Error fetching evaluations:', error)
    }
  }, 300) // 300ms debounce
  
  // Constants
  const metrics = [
    { key: 'homework', label: 'Homework', color: '#4F46E5' },
    { key: 'participation', label: 'Class Participation', color: '#EC4899' },
    { key: 'tests', label: 'Test Scores', color: '#06B6D4' },
    { key: 'proficiency', label: 'Subject Proficiency', color: '#F59E0B' }
  ]
  
  const academicMetrics = [
    { key: 'maths', label: 'Mathematics' },
    { key: 'science', label: 'Science' },
    { key: 'speaking_and_communication_skills', label: 'Speaking Skills' },
    { key: 'grammar_and_vocabulary', label: 'Grammar & Vocabulary' },
    { key: 'writing', label: 'Writing' },
    { key: 'reading', label: 'Reading' }
  ]
  
  const behavioralMetrics = [
    { key: 'attendance', label: 'Attendance' },
    { key: 'discipline', label: 'Discipline' },
    { key: 'communicationpeer_relationships', label: 'Peer Relationships' },
    { key: 'hygiene', label: 'Hygiene' },
    { key: 'extracurricular', label: 'Extracurricular' },
    { key: 'sports', label: 'Sports' }
  ]
  
  const tooltipOptions = {
    formatTooltipX: d => d,
    formatTooltipY: d => `${(d * 100).toFixed(1)}%`
  }
  
  const axisOptions = {
    xAxisMode: 'tick',
    yAxisMode: 'tick',
    xIsSeries: true,
    yMarkers: [{ 
      label: 'Target', 
      value: 0.75,
      type: 'solid'
    }],
    yAxis: {
      min: 0,
      max: 1,
      stepSize: 0.2,
      labels: [
        '0%', '20%', '40%', '60%', '80%', '100%'
      ]
    }
  }
  
  // Computed properties
  const hasData = computed(() => {
    return evaluation.data?.values?.length > 0
  })
  
  const averageScore = computed(() => {
    return evaluation.data?.average || 0
  })
  
  const metadata = computed(() => {
    return evaluation.data?.metadata || {}
  })
  
  // Methods
  const getMetricValue = (key) => {
    if (!evaluation.data?.evaluations?.[0]) return 0
    return evaluation.data.evaluations[0][key] || 0
  }
  
  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(1)}%`
  }
  
  const formatDate = (date) => {
    return date ? dayjs(date).format('MMM D, YYYY') : ''
  }
  
  // Helper function for metadata formatting
  const formatMetadataLabel = (key) => {
    if (key === 'review_date') return 'Latest Review Date'
    if (key === 'class') return 'Latest Class Review'
    return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
  }
  
  const formatMetadataValue = (key, value) => {
    if (key === 'review_date') return formatDate(value)
    if (key === 'total_evaluations') return `${value} evaluations`
    return value
  }
  
  // Helper function for detailed metrics
  const getDetailMetricValue = (key) => {
    const evaluations = evaluation.data?.evaluations || []
    if (!evaluations.length) return 0
    
    // Calculate average using the insights formula
    const nonZeroValues = evaluations
      .map(e => e[key])
      .filter(v => v !== null && v !== undefined && v !== 0)
    
    if (!nonZeroValues.length) return 0
    return nonZeroValues.reduce((a, b) => a + b, 0) / nonZeroValues.length
  }
  
  const showAnalysis = ref(false)
  
  // Lifecycle
  onMounted(async () => {
    if (!student.data) {
      await student.reload()
    }
    
    const studentId = student.data?.name
    if (studentId) {
      await fetchEvaluation(studentId)
    }
  })
  
  // Add these methods
  const getMetricAverage = (metric) => {
    const evaluations = evaluation.data?.evaluations || []
    if (!evaluations.length) return 0
    
    const values = evaluations
      .map(e => e[metric])
      .filter(v => v !== null && v !== undefined && v !== 0)
    
    if (!values.length) return 0
    return values.reduce((a, b) => a + b, 0) / values.length
  }
  
  const getProgressColorClass = (value) => {
    if (value >= 0.75) return 'bg-gradient-to-r from-green-500 to-emerald-500'
    if (value >= 0.5) return 'bg-gradient-to-r from-blue-500 to-indigo-500'
    if (value >= 0.25) return 'bg-gradient-to-r from-yellow-500 to-orange-500'
    return 'bg-gradient-to-r from-red-500 to-pink-500'
  }
  
  const getBehaviorSummary = () => {
    const evaluations = evaluation.data?.evaluations || []
    if (!evaluations.length) return {}
    
    const summary = {}
    behavioralMetrics.forEach(metric => {
      const values = evaluations
        .map(e => e[metric.key])
        .filter(v => v !== null && v !== undefined && v !== 0)
      
      if (values.length > 0) {
        summary[metric.key] = values.length
      }
    })
    
    return summary
  }
  
  const formatBehaviorLabel = (behavior) => {
    return behavior.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
  }
  
  const getBehaviorColorClass = (count) => {
    if (count > 5) return 'text-red-500'
    if (count > 3) return 'text-yellow-500'
    if (count > 1) return 'text-green-500'
    return 'text-gray-500'
  }
  
  const getCompletionRate = () => {
    const evaluations = evaluation.data?.evaluations || []
    if (!evaluations.length) return 0
    
    const completedAssignments = evaluations
      .filter(e => e['assignment_status'] === 'completed')
      .length
    
    return completedAssignments / evaluations.length
  }
  
  const getMaterialsCompletionRate = () => {
    const evaluations = evaluation.data?.evaluations || []
    if (!evaluations.length) return 0
    
    const completedMaterials = evaluations
      .filter(e => e['materials_complete'] === true)
      .length
    
    return completedMaterials / evaluations.length
  }
  
  const getLateStatusColor = () => {
    const lateCount = evaluation.data?.analysis?.flags?.late_count || 0
    if (lateCount > 5) return 'text-red-500'
    if (lateCount > 3) return 'text-yellow-500'
    if (lateCount > 1) return 'text-green-500'
    return 'text-gray-500'
  }
  
  const getHomeworkCompletionRate = () => {
    const evaluations = evaluation.data?.evaluations || []
    if (!evaluations.length) return 0
    
    const completedHomework = evaluations
      .filter(e => e['homework_status'] === 'completed')
      .length
    
    return completedHomework / evaluations.length
  }
  
  const getMissedHomeworkCount = () => {
    const evaluations = evaluation.data?.evaluations || []
    if (!evaluations.length) return 0
    
    const missedHomework = evaluations
      .filter(e => e['homework_status'] === 'missed')
      .length
    
    return missedHomework
  }
  
  const getMissedTasksColor = () => {
    const missedHomeworkCount = getMissedHomeworkCount()
    if (missedHomeworkCount > 5) return 'text-red-500'
    if (missedHomeworkCount > 3) return 'text-yellow-500'
    if (missedHomeworkCount > 1) return 'text-green-500'
    return 'text-gray-500'
  }
  
  const getMissingItemsCount = () => {
    const evaluations = evaluation.data?.evaluations || []
    if (!evaluations.length) return 0
    
    const missingItems = evaluations
      .filter(e => e['missing_items'] !== null && e['missing_items'] !== undefined && e['missing_items'] !== 0)
      .length
    
    return missingItems
  }
  
  const getHygieneRate = () => {
    const evaluations = evaluation.data?.evaluations || []
    if (!evaluations.length) return 0
    
    const hygieneRate = evaluations
      .filter(e => e['hygiene'] !== null && e['hygiene'] !== undefined && e['hygiene'] !== 0)
      .length
    
    return hygieneRate / evaluations.length
  }
  
  const getMaterialsStatusColor = () => {
    const missingItemsCount = getMissingItemsCount()
    if (missingItemsCount > 5) return 'text-red-500'
    if (missingItemsCount > 3) return 'text-yellow-500'
    if (missingItemsCount > 1) return 'text-green-500'
    return 'text-gray-500'
  }
  
  const totalEvaluations = computed(() => {
    return evaluation.data?.metadata?.total_evaluations || 0
  })
  
  // Add a watcher to log the evaluation data
  watch(() => evaluation.data, (newData) => {
    console.log('Raw evaluation data:', JSON.parse(JSON.stringify(newData)))  // Convert Proxy to plain object
    console.log('Flags data:', JSON.parse(JSON.stringify(newData?.flags)))
    console.log('Sample evaluation:', JSON.parse(JSON.stringify(newData?.evaluations?.[0])))
  }, { deep: true })
  
  const getIncidentBadgeColor = (count) => {
    if (!count) return 'bg-gray-100 text-gray-500'
    if (count >= 4) return 'bg-red-100 text-red-700'
    if (count >= 2) return 'bg-amber-100 text-amber-700'
    return 'bg-green-100 text-green-700'
  }
  
  const getBehaviorCount = (behavior) => {
    const evaluations = evaluation.data?.evaluations || []
    console.log(`Counting ${behavior}:`, evaluations.map(e => e[behavior])) // Debug log
    return evaluations.filter(e => e[behavior] === 1).length
  }
  
  const getHeatmapColor = (behavior, month) => {
    const evaluations = evaluation.data?.evaluations || []
    const monthlyCount = evaluations.filter(e => {
      const evalMonth = new Date(e.review_date).getMonth() + 1
      return evalMonth === month && e[behavior] === 1
    }).length
  
    if (monthlyCount === 0) return 'bg-gray-100'
    if (monthlyCount === 1) return 'bg-yellow-200'
    if (monthlyCount === 2) return 'bg-orange-300'
    if (monthlyCount === 3) return 'bg-red-400'
    return 'bg-red-500'
  }
  
  // Add this computed property before the template
  const chartData = computed(() => {
    if (!evaluation.data?.labels) return null;
    
    // Define label mappings (abbreviation -> full name)
    const labelMappings = {
      'HW': 'Homework',
      'Part': 'Participation',
      'Test': 'Test Scores',
      'Prof': 'Proficiency'
    };

    // Create abbreviated labels
    const abbreviatedLabels = evaluation.data.labels.map(label => {
      // Find matching abbreviation or use first 3 chars + '.'
      const abbr = Object.entries(labelMappings).find(([_, full]) => full === label)?.[0] 
        || `${label.slice(0, 3)}.`;
      return abbr;
    });

    return {
      labels: abbreviatedLabels,
      values: evaluation.data.values,
      mappings: labelMappings
    };
  });
  
  // Add a ref for chart dimensions
  const chartContainer = ref(null)
  const chartDimensions = ref({
    width: 0,
    height: 350
  })
  
  // Add resize observer
  const updateChartDimensions = () => {
    if (chartContainer.value) {
      const { width } = chartContainer.value.getBoundingClientRect()
      chartDimensions.value = {
        width,
        height: 350
      }
      // Force chart update
      nextTick(() => {
        if (window.$frappe) window.$frappe.charts.update()
      })
    }
  }
  
  // Setup resize observer
  let resizeObserver
  onMounted(() => {
    resizeObserver = new ResizeObserver(debounce(updateChartDimensions, 100))
    if (chartContainer.value) {
      resizeObserver.observe(chartContainer.value)
      resizeObserver.observe(document.body) // Watch for layout changes
    }
    updateChartDimensions()
  })
  
  onUnmounted(() => {
    if (resizeObserver) {
      resizeObserver.disconnect()
    }
  })
  
  // Watch for layout changes with immediate effect
  watch(
    [
      () => isSidebarCollapsed,
      () => showAnalysis,
      () => chartContainer.value?.offsetWidth
    ],
    () => {
      updateChartDimensions()
    },
    { immediate: true, deep: true }
  )
  
  const getMetricDotColor = (value) => {
    if (value >= 0.75) return 'bg-emerald-500'
    if (value >= 0.5) return 'bg-blue-500'
    if (value >= 0.25) return 'bg-amber-500'
    return 'bg-red-500'
  }
  
  const getMetricGradient = (index) => {
    const gradients = [
      'bg-gradient-to-t from-indigo-600 to-blue-400',   // Homework
      'bg-gradient-to-t from-pink-600 to-rose-400',     // Participation
      'bg-gradient-to-t from-cyan-600 to-sky-400',      // Test Scores
      'bg-gradient-to-t from-amber-600 to-yellow-400'   // Proficiency
    ]
    return gradients[index]
  }
  
  // Add touch interaction helpers
  const handleTouchStart = (event) => {
    const touch = event.touches[0]
    touchStartX.value = touch.clientX
    touchStartY.value = touch.clientY
  }
  
  const handleTouchMove = (event) => {
    if (!touchStartX.value || !touchStartY.value) return
    
    const touch = event.touches[0]
    const deltaX = touch.clientX - touchStartX.value
    const deltaY = touch.clientY - touchStartY.value
    
    // If horizontal scroll is greater than vertical, prevent default
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      event.preventDefault()
    }
  }
  
  const handleTouchEnd = () => {
    touchStartX.value = null
    touchStartY.value = null
  }
  
  // Add refs for touch interaction
  const touchStartX = ref(null)
  const touchStartY = ref(null)
  
  // Add to onMounted
  onMounted(() => {
    // ... existing mounted code ...
    
    // Add touch event listeners
    const chartElement = document.querySelector('.chart-container')
    if (chartElement) {
      chartElement.addEventListener('touchstart', handleTouchStart, { passive: false })
      chartElement.addEventListener('touchmove', handleTouchMove, { passive: false })
      chartElement.addEventListener('touchend', handleTouchEnd)
    }
  })
  
  // Add to onUnmounted
  onUnmounted(() => {
    // ... existing unmounted code ...
    
    // Remove touch event listeners
    const chartElement = document.querySelector('.chart-container')
    if (chartElement) {
      chartElement.removeEventListener('touchstart', handleTouchStart)
      chartElement.removeEventListener('touchmove', handleTouchMove)
      chartElement.removeEventListener('touchend', handleTouchEnd)
    }
  })
  </script>
  
  <style scoped>
  .sacred-spinner {
    width: 4rem;  /* w-16 */
    height: 4rem; /* h-16 */
    position: relative;
    animation: sacred-spin 3s linear infinite;
  }
  
  .sacred-spinner::before,
  .sacred-spinner::after {
    content: '';
    position: absolute;
    inset: 0;
    border: 4px solid transparent;
    border-radius: 9999px;
  }
  
  .sacred-spinner::before {
    border-top-color: rgb(59, 130, 246);    /* blue-500 */
    border-right-color: rgb(59, 130, 246);  /* blue-500 */
    animation: sacred-pulse 2s ease-in-out infinite;
  }
  
  .sacred-spinner::after {
    border-bottom-color: rgb(168, 85, 247);  /* purple-500 */
    border-left-color: rgb(168, 85, 247);    /* purple-500 */
    animation: sacred-pulse 2s ease-in-out infinite reverse;
  }
  
  .pattern-grid {
    background-image: linear-gradient(0deg, 
      transparent 24%, 
      rgba(79, 70, 229, 0.03) 25%, 
      rgba(79, 70, 229, 0.03) 26%, 
      transparent 27%, transparent 74%, 
      rgba(79, 70, 229, 0.03) 75%, 
      rgba(79, 70, 229, 0.03) 76%, 
      transparent 77%, transparent
    );
    background-size: 15px 15px;
  }
  
  .sacred-symbol {
    background: conic-gradient(
      from 0deg,
      rgb(99, 102, 241),    /* indigo-500 */
      rgb(168, 85, 247),    /* purple-500 */
      rgb(99, 102, 241)     /* indigo-500 */
    );
    mask-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='45'/%3E%3Cpath d='M50 5L95 50L50 95L5 50Z'/%3E%3C/svg%3E");
  }
  
  .circular-chart {
    transform: rotate(-90deg);
    stroke-linecap: round;
  }
  
  @keyframes sacred-spin {
    100% { 
      transform: rotate(360deg); 
    }
  }
  
  @keyframes sacred-pulse {
    50% { 
      transform: scale(1.2); 
      opacity: 0.5; 
    }
  }
  
  /* Additional sacred geometry animations */
  .sacred-hover {
    transition: all 0.3s ease;
  }
  
  .sacred-hover:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.1);
  }
  
  .sacred-glow {
    position: relative;
  }
  
  .sacred-glow::after {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(
      circle at center,
      rgba(99, 102, 241, 0.1),
      transparent 70%
    );
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .sacred-glow:hover::after {
    opacity: 1;
  }
  
  .v-frappe-chart {
    background: linear-gradient(to bottom, rgba(249, 250, 251, 0.5), white);
    border-radius: 8px;
    padding: 1rem;
  }
  
  .v-frappe-chart .bar {
    transition: all 0.3s ease;
  }
  
  .v-frappe-chart .bar:hover {
    filter: brightness(1.1);
    transform: translateY(-2px);
  }
  
  /* Add smooth transitions for chart resizing */
  .v-frappe-chart {
    transition: all 0.3s ease-in-out;
  }
  
  .v-frappe-chart svg {
    transition: all 0.3s ease-in-out;
  }
  
  .custom-tooltip {
    @apply bg-white shadow-lg rounded-lg p-3 border border-gray-100;
    font-size: 0.875rem;
  }
  
  @media (max-width: 768px) {
    .custom-tooltip {
      font-size: 0.75rem;
      padding: 0.5rem;
    }
  }
  
  /* Improve touch interactions on mobile */
  @media (max-width: 768px) {
    .v-frappe-chart {
      touch-action: pan-y pinch-zoom;
    }
  }
  
  /* Chart Animations */
  @keyframes slideUp {
    from {
      transform: translateY(20px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes pulse {
    0% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.05);
    }
    100% {
      transform: scale(1);
    }
  }

  /* Chart Container Styles */
  .chart-container {
    animation: slideUp 0.6s ease-out;
  }

  /* Bar Animation */
  .metric-bar {
    transition: height 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  }

  /* Value Label Animation */
  .value-label {
    animation: fadeIn 0.3s ease-out;
  }

  /* Hover Effects */
  .metric-card:hover .metric-bar {
    filter: brightness(1.1);
  }

  .metric-card:hover .value-label {
    animation: pulse 1s infinite;
  }

  /* Mobile Optimizations */
  @media (max-width: 640px) {
    .chart-container {
      margin: 0 -1rem;
      padding: 0 1rem;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      scroll-snap-type: x mandatory;
    }
    
    .metric-card {
      scroll-snap-align: start;
      min-width: 200px;
    }
    
    .value-label {
      font-size: 0.75rem;
    }
  }

  /* Accessibility Improvements */
  @media (prefers-reduced-motion: reduce) {
    .chart-container,
    .metric-bar,
    .value-label {
      animation: none;
      transition: none;
    }
  }

  /* High Contrast Mode */
  @media (prefers-contrast: more) {
    .metric-bar {
      border: 1px solid currentColor;
    }
    
    .target-line {
      border-width: 2px;
    }
  }

  /* Dark Mode Support */
  @media (prefers-color-scheme: dark) {
    .metric-card {
      background: linear-gradient(to bottom right, rgba(255, 255, 255, 0.05), transparent);
      border-color: rgba(255, 255, 255, 0.1);
    }
    
    .value-label {
      background-color: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.2);
    }
  }

  /* Touch Interaction Styles */
  @media (hover: none) {
    .metric-card {
      touch-action: pan-y pinch-zoom;
    }
    
    .chart-container {
      user-select: none;
      -webkit-user-select: none;
    }
  }

  /* Smooth Scrolling */
  .chart-container {
    scroll-behavior: smooth;
  }

  /* Loading State Animation */
  .loading-spinner {
    animation: rotate 1s linear infinite;
  }

  @keyframes rotate {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
  </style> 
  
  

</``rewritten_file
```
</>`rewritten_file>