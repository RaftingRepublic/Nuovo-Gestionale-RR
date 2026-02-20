<template>
  <div class="calendar-container">
    <!-- Header: Navigation & Filters -->
    <div class="row justify-between items-center q-mb-md">
      <div class="row items-center q-gutter-sm">
        <q-btn flat round icon="chevron_left" @click="prevMonth" />
        <div class="text-h6 text-capitalize">{{ currentMonthName }} {{ currentYear }}</div>
        <q-btn flat round icon="chevron_right" @click="nextMonth" />
        <q-btn flat dense label="Oggi" @click="goToToday" class="q-ml-sm" />
      </div>

      <div class="row items-center q-gutter-md">
         <q-btn-toggle
          v-model="internalViewMode"
          push
          glossy
          toggle-color="primary"
          :options="[
            {label: 'Discese', value: 'DESCENTS'},
            {label: 'Staff', value: 'STAFF'},
            {label: 'Tutto', value: 'BOTH'}
          ]"
          @update:model-value="$emit('update:viewMode', $event)"
        />
      </div>
    </div>

    <!-- Calendar Grid -->
    <div class="calendar-grid">
      <!-- Weekday Headers -->
      <div v-for="day in weekDays" :key="day" class="weekday-header">
        {{ day }}
      </div>

      <!-- Days -->
      <!-- Empty cells for start padding -->
      <div v-for="n in startPadding" :key="'pad-'+n" class="day-cell empty"></div>

      <!-- Actual Days -->
      <div 
        v-for="day in days" 
        :key="day.date" 
        class="day-cell"
        :class="{ 
          'is-today': isToday(day.date),
          'is-closed': day.is_closed,
          'has-slots': day.slots && day.slots.length > 0
        }"
        @click="$emit('day-click', day.date)"
      >
        <div class="day-number">{{ getDayNumber(day.date) }}</div>
        
        <div class="slots-container scroll" v-if="!day.is_closed">
           <!-- Mode: DESCENTS or BOTH -->
           <template v-if="internalViewMode === 'DESCENTS' || internalViewMode === 'BOTH'">
              <template v-for="(slot, idx) in day.slots" :key="'s-'+idx">
                  <div 
                    v-if="slot.booked_pax > 0" 
                    class="slot-bar"
                    :style="{ backgroundColor: getSlotColor(slot), color: '#fff' }"
                  >
                     <div class="row items-center no-wrap justify-between" style="width: 100%">
                        <span class="text-caption text-weight-bold q-mr-xs">{{ slot.time }}</span>
                        <span style="font-size: 0.9em;">{{ slot.booked_pax }}/{{ slot.capacity }}</span>
                     </div>
                  </div>
              </template>
           </template>

           <!-- Mode: STAFF or BOTH -->
           <template v-if="internalViewMode === 'STAFF' || internalViewMode === 'BOTH'">
              <div v-if="internalViewMode === 'BOTH'" class="q-my-xs"></div>
              <div v-for="(slot, idx) in day.slots" :key="'st-'+idx" class="staff-row text-caption q-mb-xs">
                  <template v-if="slot.guides && slot.guides.length > 0">
                    <div class="text-weight-bold text-primary" style="font-size: 0.85em;">
                        {{ slot.time }} Guide:
                    </div>
                    <div class="text-grey-8" style="font-size: 0.8em; line-height: 1.1em; white-space: normal;">
                         {{ slot.guides.join(', ') }}
                    </div>
                  </template>
                  <template v-if="slot.drivers && slot.drivers.length > 0">
                     <div class="text-weight-bold text-teal q-mt-xs" style="font-size: 0.85em;">
                        Navette:
                     </div>
                     <div class="text-grey-8" style="font-size: 0.8em; line-height: 1.1em; white-space: normal;">
                         {{ slot.drivers.join(', ') }}
                     </div>
                  </template>
              </div>
           </template>
        </div>

        <div v-if="day.is_closed" class="closed-overlay text-center text-grey-5">
           <q-icon name="block" size="sm" />
           <div style="font-size: 10px;">CHIUSO</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, toRef, watch } from 'vue'

const props = defineProps({
  year: Number,
  month: Number,
  monthData: { type: Array, default: () => [] }, // Array of day objects from API
  viewMode: { type: String, default: 'DESCENTS' } // DESCENTS, STAFF, BOTH
})

const emit = defineEmits(['update:year', 'update:month', 'day-click', 'update:viewMode'])

const internalViewMode = ref(props.viewMode)
watch(() => props.viewMode, (v) => internalViewMode.value = v)

const weekDays = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']

const currentMonthName = computed(() => {
  return new Date(props.year, props.month - 1).toLocaleString('it-IT', { month: 'long' })
})

const currentYear = toRef(props, 'year')

// Compute grid padding
const startPadding = computed(() => {
  const firstDay = new Date(props.year, props.month - 1, 1).getDay()
  // Generic JS getDay: 0=Sun, 1=Mon... 
  // We want Mon=0, ... Sun=6
  return (firstDay + 6) % 7
})

const days = computed(() => {
   // Map API data to standard calendar grid days (1..N)
   // We trust monthData covers days 1..End
   return props.monthData
})

function prevMonth() {
   if(props.month === 1) emit('update:month', 12, props.year - 1)
   else emit('update:month', props.month - 1, props.year)
}

function nextMonth() {
   if(props.month === 12) emit('update:month', 1, props.year + 1)
   else emit('update:month', props.month + 1, props.year)
}

function goToToday() {
    const now = new Date()
    emit('update:month', now.getMonth() + 1, now.getFullYear()) // We emit proper month/year
}

function getDayNumber(dateStr) {
    return parseInt(dateStr.split('-')[2])
}

function isToday(dateStr) {
    const today = new Date().toISOString().split('T')[0]
    return dateStr === today
}

function getSlotColor(slot) {
    if (slot.color_hex) return slot.color_hex
    return '#2196F3' 
}
</script>

<style scoped>
.calendar-container {
    height: 100%;
    display: flex;
    flex-direction: column;
}

.calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    grid-template-rows: auto 1fr 1fr 1fr 1fr 1fr; /* Header + 5/6 weeks */
    gap: 4px;
    flex-grow: 1;
    overflow-y: auto;
    background-color: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 4px;
}

.weekday-header {
    text-align: center;
    font-weight: bold;
    padding: 8px;
    background: #fff;
    color: #666;
    border-radius: 4px;
}

.day-cell {
    background: #fff;
    border-radius: 4px;
    min-height: 100px; /* Minimum height for a cell */
    display: flex;
    flex-direction: column;
    padding: 4px;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.2s;
    position: relative;
}

.day-cell:hover {
    border-color: var(--q-primary);
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    z-index: 10;
}

.day-cell.is-today {
    background: #e3f2fd;
    border: 1px solid #bbdefb;
}

.day-cell.is-closed {
    background: #fafafa;
}

.day-number {
    font-weight: bold;
    margin-bottom: 4px;
    font-size: 0.9em;
    color: #333;
}

.slots-container {
    flex-grow: 1;
    overflow-y: auto;
    font-size: 0.8em;
}

.slot-bar {
    border-radius: 3px;
    padding: 2px 4px;
    margin-bottom: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.staff-row {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.closed-overlay {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    opacity: 0.5;
}

/* Scrollbar refinement for cells */
.slots-container::-webkit-scrollbar {
    width: 4px;
}
.slots-container::-webkit-scrollbar-thumb {
    background: #ddd;
    border-radius: 2px;
}
</style>
