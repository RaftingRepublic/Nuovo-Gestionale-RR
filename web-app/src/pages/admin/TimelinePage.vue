<template>
  <q-page class="q-pa-md">
    <!-- Intestazione e Controlli -->
    <div class="row items-center justify-between q-mb-md">
      <div class="text-h5 text-weight-bold">
        <q-icon name="view_timeline" class="q-mr-sm" color="primary" />
        Timeline Operativa
      </div>
      <div>
        <q-input v-model="selectedDate" mask="date" :rules="['date']" outlined dense label="Data">
          <template v-slot:append>
            <q-icon name="event" class="cursor-pointer">
              <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                <q-date v-model="selectedDate" mask="YYYY-MM-DD">
                  <div class="row items-center justify-end">
                    <q-btn v-close-popup label="Chiudi" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
            </q-icon>
          </template>
        </q-input>
      </div>
    </div>

    <!-- Container Timeline -->
    <div class="timeline-container bg-white border-radius-sm shadow-2">
      <!-- Header Asse X (Ore) -->
      <div class="timeline-header row no-wrap relative-position">
        <!-- Spazio vuoto allineato con la colonna delle label -->
        <div class="timeline-sidebar header-sidebar"></div>
        <!-- Grid delle ore -->
        <div class="timeline-grid relative-position text-caption text-grey-6 z-top" style="flex-grow: 1;">
          <div
            v-for="hour in hoursScale"
            :key="'hour-'+hour"
            class="hour-marker absolute"
            :style="{ left: calcLeftPercent(hour + ':00') + '%' }"
          >
            {{ String(hour).padStart(2, '0') }}:00
          </div>
        </div>
      </div>

      <q-separator />

      <!-- Body Asse Y (Rides) -->
      <div class="timeline-body">
        <div v-if="loading" class="q-pa-xl text-center text-grey-5">
          <q-spinner color="primary" size="2em" class="q-mb-sm"/>
          <div>Caricamento turni...</div>
        </div>
        <div v-else-if="activeRides.length === 0" class="q-pa-xl text-center text-grey-5">
          <q-icon name="info" size="32px" class="q-mb-sm" />
          <div class="text-body1">Nessun turno reale schedulato in questa data.</div>
        </div>

        <div
          v-for="ride in activeRides"
          :key="ride.id"
          class="timeline-row row no-wrap"
        >
          <!-- Colonna fissa a sinistra -->
          <div class="timeline-sidebar column justify-center q-px-sm bg-grey-1 text-caption text-weight-bold">
            <div class="text-primary">{{ String(ride.time).substring(0,5) }}</div>
            <div class="ellipsis">{{ ride.activity_type || ride.activity_name }}</div>
          </div>

          <!-- Pista del tempo -->
          <div class="timeline-track relative-position">
            <!-- Griglia di sfondo (righe verticali) -->
            <div
              v-for="hour in hoursScale"
              :key="'grid-'+hour"
              class="grid-line absolute-top-bottom"
              :style="{ left: calcLeftPercent(hour + ':00') + '%' }"
            ></div>

            <!-- Mattoncini Spaziali BPMN V5 -->
            <template v-if="!settingsLoading">
              <div
                v-for="(block, idx) in getComputedBlocks(ride)"
                :key="idx"
                class="absolute text-white row items-center justify-center shadow-1 overflow-hidden rounded-borders"
                :style="{
                  left: calcLeftPercent(block.startMin) + '%',
                  width: calcWidthPercent(block.duration) + '%',
                  backgroundColor: getActivityColor(ride),
                  top: '10%',
                  height: '80%',
                  borderRadius: '4px',
                  opacity: block.isEnd ? 0.85 : 1,
                  backgroundImage: block.isEnd ? 'repeating-linear-gradient(45deg, transparent, transparent 5px, rgba(255,255,255,0.2) 5px, rgba(255,255,255,0.2) 10px)' : 'none'
                }"
              >
                <span class="ellipsis q-px-xs text-caption text-weight-bold" style="font-size: 10px; text-transform: lowercase;">
                  {{ block.name }}
                </span>

                <q-tooltip class="bg-indigo-10 text-white text-caption shadow-4" :delay="200">
                  <div class="text-weight-bold">{{ block.name }}</div>
                  <div>Durata: {{ block.duration }} min</div>
                  <div v-if="block.resourceClasses && block.resourceClasses.length">
                    Risorse: {{ block.resourceClasses.join(', ') }}
                  </div>
                </q-tooltip>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useResourceStore } from 'stores/resource-store'
import { useSettingsStore } from 'stores/settings-store'

const store = useResourceStore()
const settingsStore = useSettingsStore()

// Impostazioni Data
const getTodayStr = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
const selectedDate = ref(getTodayStr())

const loading = computed(() => store.loading || settingsStore.loading)
const settingsLoading = computed(() => settingsStore.loading)

// Fetching automatico al variare della data
watch(selectedDate, async (newVal) => {
  if (newVal) {
    if (store.activities.length === 0) await store.fetchCatalogs()
    if (settingsStore.settings.length === 0) await settingsStore.fetchSettings()
    const queryDate = String(newVal).replace(/\//g, '-')
    await store.fetchDailySchedule(queryDate)
  }
}, { immediate: true })

// Solo turni reali
const activeRides = computed(() => {
  return (store.dailySchedule || []).filter(r => !r.isGhost)
})

// Motore Matematico di Rendering
const START_MIN = 480 // 08:00
const END_MIN = 1200  // 20:00
const TOTAL_MIN = END_MIN - START_MIN // 720 minuti

const hoursScale = Array.from({ length: 13 }, (_, i) => i + 8) // [8, 9, ..., 20]

function timeToMinutes(timeStr) {
  if (!timeStr) return 0
  const parts = String(timeStr).split(':')
  const h = parseInt(parts[0], 10) || 0
  const m = parseInt(parts[1], 10) || 0
  return h * 60 + m
}

function calcLeftPercent(timeStr) {
  const mins = timeToMinutes(timeStr)
  let offset = mins - START_MIN
  if (offset < 0) offset = 0
  if (offset > TOTAL_MIN) offset = TOTAL_MIN
  return (offset / TOTAL_MIN) * 100
}

function calcWidthPercent(durationMins) {
  const dur = parseInt(durationMins, 10) || 0
  return (dur / TOTAL_MIN) * 100
}

function getActivityColor(ride) {
  const act = store.activities.find(a => String(a.id) === String(ride.activity_id))
  return act?.color_hex || ride.color_hex || '#1976D2'
}

// Fase 6.A.2: Parser Matematico Bidirezionale BPMN
function resolveDuration(durationVal) {
  if (durationVal === undefined || durationVal === null) return 15
  if (typeof durationVal === 'number') return durationVal

  const parsed = parseFloat(durationVal)
  if (!isNaN(parsed) && isFinite(parsed)) return parsed

  if (typeof durationVal === 'string') {
    const valFromDb = settingsStore.getSetting(durationVal)
    if (valFromDb !== null && valFromDb !== undefined) {
      const numFromDb = parseFloat(valFromDb)
      if (!isNaN(numFromDb)) return numFromDb
    }
    console.warn(`[Timeline Engine] Chiave di settings mancante o invalida: "${durationVal}". Fallback a 15 min.`)
  }
  return 15
}

function getComputedBlocks(ride) {
  const baseStartMin = timeToMinutes(ride.time)
  const act = store.activities.find(a => String(a.id) === String(ride.activity_id)) || ride.activity || {}

  let schema = act.workflow_schema
  if (typeof schema === 'string') {
    try { schema = JSON.parse(schema) } catch { schema = null }
  }

  // Fallback Monolitico
  if (!schema || !schema.flows || schema.flows.length === 0) {
    const defaultDur = act.duration_hours ? (parseFloat(act.duration_hours) * 60) : 120
    let fallbackEndMin = baseStartMin + defaultDur
    if (ride.end_time) fallbackEndMin = timeToMinutes(ride.end_time)

    return [{
      name: 'Turno Singolo',
      startMin: baseStartMin,
      duration: fallbackEndMin - baseStartMin,
      isEnd: false,
      resourceClasses: []
    }]
  }

  const blocksOutput = []

  // Calcola durata totale teorica (se serve per stabilire sessionEndMin)
  const durH = parseFloat(act.duration_hours) || 2.0
  let sessionEndMin = baseStartMin + Math.round(durH * 60)
  if (ride.end_time) {
    sessionEndMin = timeToMinutes(ride.end_time)
  }

  for (const flow of schema.flows) {
    const blocks = flow.blocks || []

    // Divide le categorie
    const startBlocks = blocks.filter(b => b.anchor !== 'end')
    const endBlocks = blocks.filter(b => b.anchor === 'end')

    // 1. Ciclo Forward (Acqua / Andata)
    let forwardCursor = baseStartMin
    for (const b of startBlocks) {
      const dur = resolveDuration(b.duration_min ?? b.duration)
      blocksOutput.push({
        name: b.name || b.code || 'Blocco',
        startMin: forwardCursor,
        duration: dur,
        isEnd: false,
        resourceClasses: b.resources || []
      })
      forwardCursor += dur
    }

    // 2. Ciclo Backward (Navetta Elastica / Ritorno)
    let backwardCursor = sessionEndMin
    const reversedEndBlocks = endBlocks.slice().reverse()
    for (const b of reversedEndBlocks) {
      const dur = resolveDuration(b.duration_min ?? b.duration)
      const startMin = backwardCursor - dur
      backwardCursor = startMin
      blocksOutput.push({
        name: b.name || b.code || 'Blocco Navetta',
        startMin: startMin,
        duration: dur,
        isEnd: true,
        resourceClasses: b.resources || []
      })
    }
  }

  return blocksOutput
}

</script>

<style scoped>
.timeline-container {
  overflow-x: auto;
  border: 1px solid #e0e0e0;
}
.timeline-header {
  height: 30px;
  background: #fcfcfc;
}
.header-sidebar {
  border-right: 1px solid #e0e0e0;
}
.timeline-sidebar {
  width: 150px;
  flex-shrink: 0;
  z-index: 1;
  border-right: 1px solid #e0e0e0;
}
.hour-marker {
  transform: translateX(-50%);
  bottom: 2px;
}
.timeline-row {
  border-bottom: 1px solid #eee;
}
.timeline-track {
  flex-grow: 1;
  height: 50px;
  overflow: hidden;
  min-width: 600px; /* minima larghezza per evitare collasso estremo */
}
.grid-line {
  border-left: 1px dashed #e0e0e0;
  z-index: 0;
}
.dummy-block {
  z-index: 2;
  transition: all 0.3s ease;
  overflow: hidden;
}
</style>
