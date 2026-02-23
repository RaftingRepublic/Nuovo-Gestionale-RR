<template>
  <div class="calendar-container">
    <!-- Header: Navigation -->
    <div class="row justify-between items-center q-mb-md">
      <div class="row items-center q-gutter-sm">
        <q-btn flat round icon="chevron_left" @click="prevMonth" />
        <div class="text-h6 text-capitalize">{{ currentMonthName }} {{ currentYear }}</div>
        <q-btn flat round icon="chevron_right" @click="nextMonth" />
        <q-btn flat dense label="Oggi" @click="goToToday" class="q-ml-sm" />
      </div>
      <div class="row items-center q-gutter-md">
      </div>
    </div>

    <!-- Calendar Grid -->
    <div class="calendar-grid">
      <!-- Weekday Headers -->
      <div v-for="day in weekDays" :key="day" class="weekday-header">
        {{ day }}
      </div>

      <!-- Empty cells for start padding -->
      <div v-for="n in startPadding" :key="'pad-'+n" class="day-cell empty"></div>

      <!-- Actual Days -->
      <div
        v-for="day in days"
        :key="day.date"
        class="day-cell"
        :class="{
          'is-today': isToday(day.date),
          'has-bookings': day.booked_rides && day.booked_rides.length > 0
        }"
        @click="$emit('day-click', day.date)"
      >
        <div class="day-number">{{ getDayNumber(day.date) }}</div>

        <!-- BLOCCO DISCESE: mattoncini colorati -->
        <div class="slots-container scroll" v-if="getRidesForDay(day).length > 0" v-show="viewFilter === 'discese' || viewFilter === 'tutto'">
          <div
            v-for="(ride, idx) in getRidesForDay(day)"
            :key="'r-'+idx"
            class="ride-brick"
            :class="{
              'ride-brick-clickable': ride.pax > 0,
              'ride-brick-empty': ride.pax === 0 || !ride.pax
            }"
            :style="ride.pax > 0 ? { backgroundColor: ride.color_hex } : {}"
            @click.stop="ride.pax > 0 ? $emit('ride-click', { date: day.date, ride }) : null"
          >
            <template v-if="ride.pax > 0">
              {{ ride.activity_code }}x{{ ride.pax }} | {{ ride.time }}
            </template>
            <template v-else>
              {{ ride.time }} {{ ride.title || ride.activity_code || '—' }}
            </template>
          </div>
        </div>

        <!-- BADGE STAFF — figlio diretto della cella, FUORI dal loop eventi -->
        <div
          v-show="viewFilter === 'staff' || viewFilter === 'tutto'"
          class="staff-badge text-caption text-grey-8 q-mt-xs"
        >
          <q-icon name="person" size="12px" class="q-mr-xs" />
          {{ day.staff_count || 5 }} Guide disp.
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
  monthData: { type: Array, default: () => [] },
  viewMode: { type: String, default: 'DESCENTS' },
  viewFilter: { type: String, default: 'tutto' }
})

const emit = defineEmits(['update:year', 'update:month', 'day-click', 'update:viewMode', 'ride-click'])

const internalViewMode = ref(props.viewMode)
watch(() => props.viewMode, (v) => internalViewMode.value = v)

const weekDays = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']

const currentMonthName = computed(() => {
  return new Date(props.year, props.month - 1).toLocaleString('it-IT', { month: 'long' })
})

const currentYear = toRef(props, 'year')

const startPadding = computed(() => {
  const firstDay = new Date(props.year, props.month - 1, 1).getDay()
  return (firstDay + 6) % 7
})

const days = computed(() => {
   return props.monthData
})

// FASE 3.17 — Filtro rigoroso per vista mensile (dati ghost/reali arrivano dallo store)
function getRidesForDay(day) {
  if (!day || !day.booked_rides || !Array.isArray(day.booked_rides)) return []
  const allRides = day.booked_rides

  if (props.viewFilter === 'discese') {
    // Ritorna SOLO turni non-ghost
    return allRides.filter(r => r.isGhost === false)
  }
  if (props.viewFilter === 'staff') {
    return []
  }
  return allRides
}

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
    emit('update:month', now.getMonth() + 1, now.getFullYear())
}

function getDayNumber(dateStr) {
    return parseInt(dateStr.split('-')[2])
}

function isToday(dateStr) {
    const today = new Date().toISOString().split('T')[0]
    return dateStr === today
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
    grid-template-rows: auto 1fr 1fr 1fr 1fr 1fr;
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
    min-height: 100px;
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

.day-number {
    font-weight: bold;
    margin-bottom: 4px;
    font-size: 0.9em;
    color: #333;
}

.slots-container {
    flex-grow: 1;
    overflow-y: auto;
}

/* I "mattoncini" di Theo */
.ride-brick {
    font-size: 10px;
    font-weight: bold;
    color: #fff;
    padding: 2px 4px;
    border-radius: 3px;
    margin-bottom: 2px;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.ride-brick-clickable {
    cursor: pointer;
    transition: filter 0.15s, transform 0.15s;
}
.ride-brick-clickable:hover {
    filter: brightness(1.15);
    transform: scale(1.05);
}

/* Slot vuoti: sfondo grigio neutro */
.ride-brick-empty {
    background-color: #e0e0e0 !important;
    color: #757575 !important;
    cursor: default;
    font-weight: normal;
}

.staff-badge {
    font-size: 10px;
    padding: 2px 4px;
    background: #f0f0f0;
    border-radius: 3px;
    margin-top: 2px;
}

/* Scrollbar */
.slots-container::-webkit-scrollbar {
    width: 4px;
}
.slots-container::-webkit-scrollbar-thumb {
    background: #ddd;
    border-radius: 2px;
}
</style>
