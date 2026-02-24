<template>
  <div class="calendar-container">
    <!-- Header: Navigation con Dropdown Mese/Anno -->
    <div class="row justify-between items-center q-mb-md">
      <div class="row items-center q-gutter-sm">
        <q-btn flat round icon="chevron_left" @click="prevMonth" />

        <!-- Mese cliccabile con dropdown -->
        <div class="nav-dropdown-trigger text-h6 text-capitalize">
          {{ currentMonthName }}
          <q-icon name="arrow_drop_down" size="xs" />
          <q-menu auto-close fit>
            <q-list dense style="min-width: 160px">
              <q-item
                v-for="m in availableMonths"
                :key="m.val"
                clickable
                :active="m.val === month"
                active-class="text-primary text-weight-bold"
                @click="jumpToMonth(m.val)"
              >
                <q-item-section>{{ m.label }}</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </div>

        <!-- Anno cliccabile con dropdown -->
        <div class="nav-dropdown-trigger text-h6">
          {{ currentYear }}
          <q-icon name="arrow_drop_down" size="xs" />
          <q-menu auto-close fit>
            <q-list dense style="min-width: 100px; max-height: 300px" class="scroll">
              <q-item
                v-for="y in availableYears"
                :key="y"
                clickable
                :active="y === year"
                active-class="text-primary text-weight-bold"
                @click="jumpToYear(y)"
              >
                <q-item-section>{{ y }}</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </div>

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

        <!-- BLOCCO DISCESE + STAFF: mattoncini colorati -->
        <div class="slots-container scroll" v-if="getRidesForDay(day).length > 0">
          <div
            v-for="(ride, idx) in getRidesForDay(day)"
            :key="'r-'+idx"
            class="ride-brick"
            :class="{ 'ride-brick-ghost': ride.isGhost }"
            :style="{ opacity: ride.isGhost ? 0.3 : 1 }"
            @click.stop="ride.isGhost ? $emit('quick-book', ride, day.date) : $emit('ride-click', { date: day.date, ride })"
          >
            <!-- Riga superiore: corpo + semaforo -->
            <div class="ride-brick-top">
              <div
                class="ride-brick-body"
                :style="{ backgroundColor: ride.color_hex || '#90a4ae' }"
              >
                <template v-if="!ride.isGhost && ride.pax > 0">
                  {{ ride.activity_code }}x{{ ride.pax }} | {{ formatTime(ride.time) }}
                </template>
                <template v-else>
                  {{ formatTime(ride.time) }} {{ ride.title || ride.activity_code || '—' }}
                </template>
              </div>

              <!-- Semaforo laterale -->
              <div
                class="ride-brick-signal"
                :style="{ backgroundColor: getStatusColor(ride) }"
              ></div>
            </div>

            <!-- Riga inferiore: badge risorse (solo per turni reali, vista STAFF o TUTTO) -->
            <div
              v-if="!ride.isGhost && ride.allocations && ride.allocations.length > 0 && (viewFilter === 'staff' || viewFilter === 'tutto')"
              class="ride-brick-allocs"
            >
              <span
                v-for="(alloc, ai) in ride.allocations"
                :key="'a-'+ai"
                class="alloc-badge"
                :class="'alloc-' + (alloc.resource_type || 'guide')"
              >
                {{ alloc.resource_name }}
              </span>
            </div>

            <!-- Tooltip -->
            <q-tooltip
              class="bg-grey-10 text-body2"
              :offset="[0, 8]"
              anchor="top middle"
              self="bottom middle"
              transition-show="fade"
              transition-hide="fade"
              :delay="300"
            >
              <div class="text-weight-bold">{{ ride.title || ride.activity_code }}</div>
              <div>Orario: {{ formatTime(ride.time) }}</div>
              <div v-if="ride.pax > 0">PAX: {{ ride.pax }}</div>
              <div v-if="ride.allocations && ride.allocations.length > 0">
                Risorse: {{ ride.allocations.map(a => a.resource_name).join(', ') }}
              </div>
              <div v-if="ride.isGhost" class="text-grey-5">Slot disponibile — clicca per prenotare</div>
            </q-tooltip>
          </div>
        </div>

        <!-- FOOTER: Potenza di Fuoco — badge colorati -->
        <div
          v-show="viewFilter === 'staff' || viewFilter === 'tutto'"
          class="slots-footer"
        >
          <span
            v-for="(item, idx) in dailyResourcesSummary"
            :key="idx"
            class="power-badge"
            :style="getBadgeStyle(item.type)"
          >{{ item.text }}</span>
          <span v-if="dailyResourcesSummary.length === 0" class="text-caption text-grey">—</span>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, toRef, watch } from 'vue'
import { useResourceStore } from 'src/stores/resource-store'

const store = useResourceStore()

const props = defineProps({
  year: Number,
  month: Number,
  monthData: { type: Array, default: () => [] },
  viewMode: { type: String, default: 'DESCENTS' },
  viewFilter: { type: String, default: 'tutto' }
})

const emit = defineEmits(['update:year', 'update:month', 'day-click', 'update:viewMode', 'ride-click', 'quick-book'])

const internalViewMode = ref(props.viewMode)
watch(() => props.viewMode, (v) => internalViewMode.value = v)

const weekDays = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']

const currentMonthName = computed(() => {
  return new Date(props.year, props.month - 1).toLocaleString('it-IT', { month: 'long' })
})

const currentYear = toRef(props, 'year')

// ── Navigazione rapida: mesi stagionali e anni ──
const availableMonths = [
  { label: 'Aprile', val: 4 },
  { label: 'Maggio', val: 5 },
  { label: 'Giugno', val: 6 },
  { label: 'Luglio', val: 7 },
  { label: 'Agosto', val: 8 },
  { label: 'Settembre', val: 9 },
  { label: 'Ottobre', val: 10 }
]
const availableYears = Array.from({ length: 16 }, (_, i) => 2020 + i)

function jumpToMonth(monthVal) {
  emit('update:month', monthVal, props.year)
}

function jumpToYear(yearVal) {
  emit('update:month', props.month, yearVal)
}

const startPadding = computed(() => {
  const firstDay = new Date(props.year, props.month - 1, 1).getDay()
  return (firstDay + 6) % 7
})

const days = computed(() => {
   return props.monthData
})

// ── Potenza di Fuoco: riepilogo organico attivo ──
const dailyResourcesSummary = computed(() => {
  const summary = []

  // — Staff per brevetto primario —
  let raf4 = 0, raf3 = 0, hyd = 0, nc = 0, nOnly = 0
  const activeStaff = (store.staffList || []).filter(s => s.is_active !== 0 && s.is_active !== false)
  activeStaff.forEach(s => {
    let roles = []
    try {
      roles = typeof s.roles === 'string' ? JSON.parse(s.roles) : (Array.isArray(s.roles) ? s.roles : [])
    } catch { roles = [] }

    // Brevetto primario (esclusione gerarchica)
    if (roles.includes('RAF4')) raf4++
    else if (roles.includes('RAF3')) raf3++
    else if (roles.includes('HYD') || roles.includes('SH')) hyd++

    // Patenti (indipendenti dal brevetto)
    if (roles.includes('N') && roles.includes('C')) nc++
    else if (roles.includes('N') && !roles.includes('C')) nOnly++
  })

  if (raf4) summary.push({ text: `${raf4} RAF4`, type: 'guide' })
  if (raf3) summary.push({ text: `${raf3} RAF3`, type: 'guide' })
  if (hyd) summary.push({ text: `${hyd} HYD`, type: 'guide' })
  if (nc) summary.push({ text: `${nc} NC`, type: 'driver' })
  if (nOnly) summary.push({ text: `${nOnly} N`, type: 'driver' })

  // — Flotta per categoria —
  let vans = 0, trailers = 0, rafts = 0
  const activeFleet = (store.fleetList || []).filter(f => f.is_active !== 0 && f.is_active !== false)
  activeFleet.forEach(f => {
    const cat = (f.category || f.resource_type || f.type || '').toUpperCase()
    if (cat === 'VAN') vans++
    else if (cat === 'TRAILER') trailers++
    else if (cat === 'RAFT') rafts++
  })

  if (vans) summary.push({ text: `${vans} FURG`, type: 'van' })
  if (trailers) summary.push({ text: `${trailers} CARR`, type: 'trailer' })
  if (rafts) summary.push({ text: `${rafts} GOMM`, type: 'raft' })

  return summary
})

// ── Colori badge per categoria ──
function getBadgeStyle(type) {
  const styles = {
    guide:   { backgroundColor: '#e3f2fd', color: '#1565c0' },
    driver:  { backgroundColor: '#fff3e0', color: '#e65100' },
    raft:    { backgroundColor: '#e8f5e9', color: '#2e7d32' },
    van:     { backgroundColor: '#fce4ec', color: '#c62828' },
    trailer: { backgroundColor: '#efebe9', color: '#4e342e' },
  }
  return styles[type] || { backgroundColor: '#e0e0e0', color: '#333' }
}

// ── Filtro per vista mensile ──
function getRidesForDay(day) {
  if (!day || !day.booked_rides || !Array.isArray(day.booked_rides)) return []
  const allRides = day.booked_rides

  if (props.viewFilter === 'discese') {
    // Solo turni reali (no ghost)
    return allRides.filter(r => !r.isGhost)
  }
  if (props.viewFilter === 'staff') {
    // Solo turni reali con almeno un'allocazione (mostra chi è assegnato)
    return allRides.filter(r => !r.isGhost && r.allocations && r.allocations.length > 0)
  }
  // TUTTO: mostra tutto (reali + ghost)
  return allRides
}


// ── Semaforo di stato ──
function getStatusColor(ride) {
  if (ride.isGhost) return '#4CAF50'

  const pax = ride.pax || ride.booked_pax || 0
  if (pax === 0) return '#4CAF50'

  const maxCap = ride.total_capacity || ride.capacity?.max || 16
  const yellowThreshold = ride.yellow_threshold || 8
  const remaining = maxCap - pax

  if (remaining <= 0) return '#f44336'
  if (remaining <= yellowThreshold) return '#FF9800'
  return '#2196F3'
}

// ── Formattazione orario ──
function formatTime(timeStr) {
  if (!timeStr) return '--:--'
  return String(timeStr).substring(0, 5)
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

/* ── Mattoncini: Layout a colonna (corpo + allocazioni) ── */
.ride-brick {
    display: flex;
    flex-direction: column;
    border-radius: 4px;
    margin-bottom: 2px;
    overflow: hidden;
    cursor: pointer;
    transition: filter 0.15s, transform 0.1s;
    box-shadow: 0 1px 2px rgba(0,0,0,0.12);
}

.ride-brick:hover {
    filter: brightness(1.12);
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.18);
}

.ride-brick-ghost:hover {
    filter: brightness(1.25);
}

/* Riga superiore: corpo + semaforo (flex orizzontale) */
.ride-brick-top {
    display: flex;
    width: 100%;
}

.ride-brick-body {
    flex-grow: 1;
    color: #fff;
    padding: 2px 5px;
    font-size: 10px;
    font-weight: bold;
    line-height: 1.3;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    text-shadow: 0 1px 1px rgba(0,0,0,0.2);
}

.ride-brick-signal {
    width: 16px;
    flex-shrink: 0;
}

/* Riga inferiore: badge risorse assegnate */
.ride-brick-allocs {
    display: flex;
    flex-wrap: wrap;
    gap: 1px;
    padding: 1px 2px;
    background: rgba(255,255,255,0.92);
    border-top: 1px solid rgba(0,0,0,0.08);
}

.alloc-badge {
    font-size: 8px;
    font-weight: 600;
    padding: 0px 3px;
    border-radius: 2px;
    white-space: nowrap;
    line-height: 1.4;
}

/* Colori badge per tipo risorsa */
.alloc-guide { background: #e3f2fd; color: #1565c0; }
.alloc-driver { background: #fff3e0; color: #e65100; }
.alloc-raft { background: #e8f5e9; color: #2e7d32; }
.alloc-van { background: #fce4ec; color: #c62828; }
.alloc-trailer { background: #efebe9; color: #4e342e; }

/* ── Navigation Dropdown Triggers ── */
.nav-dropdown-trigger {
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 2px;
    border-bottom: 1.5px dashed rgba(0,0,0,0.25);
    padding-bottom: 1px;
    transition: opacity 0.2s, border-color 0.2s;
    user-select: none;
}
.nav-dropdown-trigger:hover {
    opacity: 0.7;
    border-color: var(--q-primary);
}

.slots-footer {
    display: flex;
    flex-wrap: wrap;
    gap: 3px;
    justify-content: center;
    align-items: center;
    padding: 3px 4px;
    background: #fff;
    border-radius: 3px;
    margin-top: auto;
    border-top: 1px solid #e8e8e8;
    min-height: 22px;
}

.power-badge {
    font-size: 0.6rem;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 3px;
    white-space: nowrap;
    line-height: 1.4;
    letter-spacing: 0.3px;
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
