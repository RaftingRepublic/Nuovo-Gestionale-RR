<template>
  <q-page class="q-pa-md">
    <!-- Intestazione e Controlli -->
    <div class="row items-center justify-between q-mb-md">
      <div class="row items-center q-gutter-sm">
        <q-btn flat icon="arrow_back" label="Torna al Giorno" color="primary" @click="router.push({ path: '/admin/operativo', query: { date: store.selectedDate } })" />
        <q-separator vertical />
        <div class="text-h5 text-weight-bold">
          <q-icon name="view_timeline" class="q-mr-sm" color="primary" />
          Timeline Operativa
        </div>
      </div>
      <div class="row items-center q-gutter-sm">
        <!-- Toggle Vista DISC / ROLE -->
        <q-btn-toggle
          v-model="store.timelineViewMode"
          toggle-color="primary"
          dense unelevated
          :options="[
            { label: 'Discese', value: 'DISC', icon: 'directions_boat' },
            { label: 'Ruoli', value: 'ROLE', icon: 'badge' }
          ]"
          class="shadow-1"
        />
        <q-input v-model="selectedDate" mask="date" :rules="['date']" outlined dense label="Data" style="max-width: 180px;">
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
        <div class="timeline-sidebar header-sidebar"></div>
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

      <!-- Barra Saturazione Risorse -->
      <div v-if="!loading && activeRides.length > 0" class="saturation-bar-container row no-wrap relative-position" style="height: 18px;">
        <div class="timeline-sidebar header-sidebar" style="height: 18px;">
          <span class="text-caption text-grey-6 q-px-xs" style="font-size: 9px; line-height: 18px;">SAT%</span>
        </div>
        <div class="relative-position" style="flex-grow: 1; height: 18px; background: #f5f5f5;">
          <div
            v-for="(bucket, bIdx) in saturationBuckets"
            :key="'sat-'+bIdx"
            class="absolute"
            :style="{
              left: (bIdx / saturationBuckets.length * 100) + '%',
              width: (100 / saturationBuckets.length) + '%',
              height: '100%',
              backgroundColor: bucket.pct <= 0 ? 'transparent' : bucket.pct < 70 ? '#4caf50' : bucket.pct < 90 ? '#ff9800' : '#f44336',
              opacity: bucket.pct > 0 ? 0.7 : 0,
              transition: 'background-color 0.3s'
            }"
          >
            <q-tooltip class="bg-dark text-white text-caption" :delay="100">
              {{ bucket.timeLabel }} — {{ bucket.pct }}% saturazione ({{ bucket.occupied }}/{{ bucket.pool }} ruoli)
            </q-tooltip>
          </div>
        </div>
      </div>

      <!-- Body -->
      <div class="timeline-body">
        <div v-if="loading" class="q-pa-xl text-center text-grey-5">
          <q-spinner color="primary" size="2em" class="q-mb-sm"/>
          <div>Caricamento turni...</div>
        </div>

        <!-- ═══════════════════════════════════════════════════════ -->
        <!-- VISTA DISCESE (DISC) — pista = ride                    -->
        <!-- ═══════════════════════════════════════════════════════ -->
        <template v-else-if="store.timelineViewMode === 'DISC'">
          <div v-if="activeRides.length === 0" class="q-pa-xl text-center text-grey-5">
            <q-icon name="info" size="32px" class="q-mb-sm" />
            <div class="text-body1">Nessun turno schedulato in questa data.</div>
          </div>

          <div
            v-for="ride in activeRides"
            :key="ride.id"
            class="timeline-row row no-wrap"
          >
            <div class="timeline-sidebar column justify-center q-px-sm bg-grey-1 text-caption text-weight-bold">
              <div class="text-primary">{{ String(ride.time).substring(0,5) }}</div>
              <div class="ellipsis">{{ ride.activity_type || ride.activity_name }}</div>
            </div>

            <div class="timeline-track relative-position">
              <div v-for="hour in hoursScale" :key="'grid-'+hour" class="grid-line absolute-top-bottom" :style="{ left: calcLeftPercent(hour + ':00') + '%' }"></div>

              <template v-if="!settingsLoading">
                <div
                  v-for="(block, idx) in getComputedBlocks(ride)"
                  :key="idx"
                  class="gantt-block absolute row items-center shadow-1 overflow-hidden rounded-borders"
                  :class="getRideStatusClass(ride)"
                  :style="{
                    left: calcLeftPercent(block.startMin) + '%',
                    width: Math.max(0.5, calcWidthPercent(block.duration)) + '%',
                    backgroundColor: getRideStatusBgColor(ride),
                    top: getBlockTop(block) + '%',
                    height: getBlockHeight(block) + '%',
                    borderRadius: '3px',
                    opacity: block.isEnd ? 0.9 : 1,
                    backgroundImage: block.flowIndex > 0 ? 'repeating-linear-gradient(45deg, transparent, transparent 4px, rgba(255,255,255,0.15) 4px, rgba(255,255,255,0.15) 8px)' : 'none',
                    zIndex: 2,
                    minWidth: '2px'
                  }"
                >
                  <span class="ellipsis q-px-xs text-weight-bold" style="font-size: 9px; line-height: 1.2; white-space: nowrap; text-shadow: 0 1px 2px rgba(0,0,0,0.4);">
                    {{ block.name }}
                  </span>
                  <q-tooltip class="bg-indigo-10 text-white text-caption shadow-4" :delay="200">
                    <div class="text-weight-bold">{{ block.name }}</div>
                    <div>Durata: {{ block.duration }} min</div>
                    <div>Flusso: #{{ block.flowIndex }} ({{ block.flowName || '?' }})</div>
                    <div v-if="block.resourceClasses && block.resourceClasses.length">
                      Risorse: {{ block.resourceClasses.join(', ') }}
                    </div>
                  </q-tooltip>
                </div>
              </template>
            </div>
          </div>
        </template>

        <!-- ═══════════════════════════════════════════════════════ -->
        <!-- VISTA RUOLI (ROLE) — pista = tag ruolo con Multi-Lane  -->
        <!-- ═══════════════════════════════════════════════════════ -->
        <template v-else>
          <div v-if="roleTimelineRows.length === 0" class="q-pa-xl text-center text-grey-5">
            <q-icon name="badge" size="32px" class="q-mb-sm" />
            <div class="text-body1">Nessun ruolo assorbito nei turni di oggi.</div>
          </div>

          <div
            v-for="row in roleTimelineRows"
            :key="row.roleTag"
            class="timeline-row row no-wrap"
          >
            <!-- Sidebar: codice ruolo + conteggio lanes -->
            <div class="timeline-sidebar column justify-center q-px-sm text-caption text-weight-bold"
                 :class="row.isFleet ? 'bg-orange-1' : 'bg-blue-1'"
                 :style="{ minHeight: Math.max(60, row.lanesCount * 30) + 'px' }">
              <div class="row items-center no-wrap">
                <q-icon :name="row.isFleet ? 'local_shipping' : 'person'" size="16px"
                        :color="row.isFleet ? 'orange-8' : 'primary'" class="q-mr-xs" />
                <span class="text-weight-bold" style="font-size: 13px;">{{ row.roleTag }}</span>
                <q-badge v-if="row.lanesCount > 1" color="red-5" text-color="white" class="q-ml-xs" style="font-size: 10px;">
                  ×{{ row.lanesCount }}
                </q-badge>
              </div>
              <div class="text-grey-6" style="font-size: 9px;">
                {{ row.blocks.length }} impegni
              </div>
            </div>

            <!-- Pista del tempo — altezza adattiva -->
            <div class="timeline-track relative-position"
                 :style="{ height: Math.max(60, row.lanesCount * 30) + 'px' }">
              <div v-for="hour in hoursScale" :key="'rolegrid-'+hour" class="grid-line absolute-top-bottom" :style="{ left: calcLeftPercent(hour + ':00') + '%' }"></div>

              <div
                v-for="(block, bIdx) in row.blocks"
                :key="bIdx"
                class="gantt-block absolute row items-center shadow-1 overflow-hidden rounded-borders"
                :class="getRideStatusClassFromBlock(block)"
                :style="{
                  left: calcLeftPercent(block.startMin) + '%',
                  width: Math.max(0.5, calcWidthPercent(block.duration)) + '%',
                  backgroundColor: getRideStatusBgColorFromBlock(block),
                  top: getRoleLaneTop(block.laneIndex, row.lanesCount) + '%',
                  height: getRoleLaneHeight(row.lanesCount) + '%',
                  borderRadius: '3px',
                  zIndex: 2,
                  minWidth: '2px'
                }"
              >
                <span class="ellipsis q-px-xs text-weight-bold" style="font-size: 9px; line-height: 1.2; white-space: nowrap; text-shadow: 0 1px 2px rgba(0,0,0,0.4);">
                  {{ block.rideName }} · {{ block.name }}
                </span>
                <q-tooltip class="bg-indigo-10 text-white text-caption shadow-4" :delay="200">
                  <div class="text-weight-bold">{{ block.rideName }} — {{ block.name }}</div>
                  <div>Orario turno: {{ block.rideTime }}</div>
                  <div>Durata blocco: {{ block.duration }} min</div>
                  <div>Corsia: {{ block.laneIndex + 1 }} / {{ row.lanesCount }}</div>
                  <div>Ruoli assorbiti: {{ block.allRoleTags.join(', ') }}</div>
                </q-tooltip>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useResourceStore } from 'stores/resource-store'
import { useSettingsStore } from 'stores/settings-store'

const store = useResourceStore()
const settingsStore = useSettingsStore()
const router = useRouter()

// selectedDate: computed bidirezionale ancorato allo store centralizzato
// Formato Quasar QDate: YYYY-MM-DD (stesso del store, nessuna conversione necessaria)
const selectedDate = computed({
  get: () => store.selectedDate,
  set: (val) => {
    if (val && val !== store.selectedDate) {
      store.setSelectedDate(val)
    }
  }
})

const loading = computed(() => store.loading || settingsStore.loading)
const settingsLoading = computed(() => settingsStore.loading)

// Watcher su store.selectedDate (centralizzato — reagisce anche a cambi dalla PlanningPage)
watch(() => store.selectedDate, async (newVal) => {
  if (newVal) {
    if (store.activities.length === 0) await store.fetchCatalogs()
    if (settingsStore.settings.length === 0) await settingsStore.fetchSettings()
    if (store.staffList.length === 0) await store.fetchStaff() // Pool per Barra Saturazione
    const cleanDate = String(newVal).replace(/\//g, '-')
    await store.fetchDailySchedule(cleanDate)
  }
}, { immediate: true })

// Turni per la Timeline DISC: include TUTTI i turni con attività nota
const activeRides = computed(() => {
  return (store.dailySchedule || []).filter(r => {
    const act = store.activities.find(a => String(a.id) === String(r.activity_id))
    return !!act
  })
})

// ═══════════════════════════════════════════════════════════
// BARRA SATURAZIONE — Bucket da 5 minuti (08:00-20:00)
// Per ogni bucket: conta i ruoli occupati / pool staff attivo
// ═══════════════════════════════════════════════════════════
const BUCKET_SIZE = 5 // minuti per bucket
const BUCKET_COUNT = Math.ceil((1200 - 480) / BUCKET_SIZE) // 144 bucket

const saturationBuckets = computed(() => {
  const rides = activeRides.value
  const buckets = []

  // Pool: numero di staff attivi (guide), fallback a 6 se non caricati
  const activeGuides = (store.staffList || []).filter(s => s.is_active)
  const pool = Math.max(1, activeGuides.length || 6)

  // Pre-calcola tutti i blocchi BPMN con i loro tag
  const allBlocks = []
  for (const ride of rides) {
    const rideBlocks = getComputedBlocks(ride)
    for (const b of rideBlocks) {
      const tags = (b.resourceClasses || []).map(t => String(t).toUpperCase())
      if (tags.length === 0) continue
      allBlocks.push({
        startMin: b.startMin,
        endMin: b.startMin + b.duration,
        tagCount: tags.length, // Numero di ruoli assorbiti simultaneamente
      })
    }
  }

  // Genera i bucket
  for (let i = 0; i < BUCKET_COUNT; i++) {
    const bucketStart = 480 + i * BUCKET_SIZE
    const bucketEnd = bucketStart + BUCKET_SIZE
    const hh = String(Math.floor(bucketStart / 60)).padStart(2, '0')
    const mm = String(bucketStart % 60).padStart(2, '0')

    // Conta quanti ruoli sono occupati in questo intervallo
    let occupied = 0
    for (const block of allBlocks) {
      if (block.startMin < bucketEnd && block.endMin > bucketStart) {
        occupied += block.tagCount
      }
    }

    const pct = Math.min(100, Math.round((occupied / pool) * 100))

    buckets.push({
      timeLabel: `${hh}:${mm}`,
      occupied,
      pool,
      pct,
    })
  }

  return buckets
})

// ═══════════════════════════════════════════════════════════
// ROLE PIVOT — Vista per Tag Ruolo con Multi-Lane Packing
// Ogni riga = un tag ruolo. I blocchi sovrapposti vengono
// impilati in sub-lanes verticali per mostrare la concorrenza.
// ═══════════════════════════════════════════════════════════
const FLEET_TAGS = new Set(['RAFT', 'VAN', 'TRAILER', 'N', 'NC', 'C'])

/**
 * Algoritmo Greedy Lane Packing:
 * Ordina i blocchi per startMin. Per ogni blocco, trova la prima
 * sub-lane dove non c'è sovrapposizione (laneEndMin <= block.startMin).
 * Se nessuna lane è libera, crea una nuova sub-lane.
 */
function packBlocksIntoLanes(blocks) {
  // Ordina per inizio temporale
  const sorted = [...blocks].sort((a, b) => a.startMin - b.startMin)
  const laneEnds = [] // laneEnds[i] = minuto di fine dell'ultimo blocco nella lane i

  for (const block of sorted) {
    let assigned = false
    for (let i = 0; i < laneEnds.length; i++) {
      if (laneEnds[i] <= block.startMin) {
        // Questa lane è libera: assegna il blocco qui
        block.laneIndex = i
        laneEnds[i] = block.startMin + block.duration
        assigned = true
        break
      }
    }
    if (!assigned) {
      // Nessuna lane libera: crea una nuova sub-lane
      block.laneIndex = laneEnds.length
      laneEnds.push(block.startMin + block.duration)
    }
  }

  return { blocks: sorted, lanesCount: Math.max(1, laneEnds.length) }
}

const roleTimelineRows = computed(() => {
  const roleMap = {} // { tag: { roleTag, isFleet, blocks: [] } }
  const rides = activeRides.value

  for (const ride of rides) {
    const rideBlocks = getComputedBlocks(ride)
    const rideColor = getActivityColor(ride)
    const rideName = ride.activity_type || ride.activity_name || ''
    const rideTime = String(ride.time).substring(0, 5)

    for (const b of rideBlocks) {
      const tags = (b.resourceClasses || []).map(t => String(t).toUpperCase())
      if (tags.length === 0) continue

      const enrichedBlock = {
        ...b,
        rideColor,
        rideName,
        rideTime,
        rideStatus: _resolveStatus(ride),
        allRoleTags: tags,
        laneIndex: 0, // Default, verrà sovrascritto dal packer
      }

      for (const tag of tags) {
        if (!roleMap[tag]) {
          roleMap[tag] = {
            roleTag: tag,
            isFleet: FLEET_TAGS.has(tag),
            blocks: []
          }
        }
        // Crea una copia per evitare conflitti di laneIndex tra ruoli diversi
        roleMap[tag].blocks.push({ ...enrichedBlock })
      }
    }
  }

  // Applica lane packing a ogni gruppo di ruoli
  const rows = Object.values(roleMap).map(row => {
    const { blocks, lanesCount } = packBlocksIntoLanes(row.blocks)
    return {
      roleTag: row.roleTag,
      isFleet: row.isFleet,
      blocks,
      lanesCount,
    }
  })

  // Ordina: prima guide (non-fleet), poi fleet
  rows.sort((a, b) => {
    if (a.isFleet !== b.isFleet) return a.isFleet ? 1 : -1
    return a.roleTag.localeCompare(b.roleTag)
  })

  return rows
})

// Motore Matematico di Rendering
const START_MIN = 480 // 08:00
const END_MIN = 1200  // 20:00
const TOTAL_MIN = END_MIN - START_MIN // 720 minuti

const hoursScale = Array.from({ length: 13 }, (_, i) => i + 8) // [8, 9, ..., 20]

function timeToMinutes(timeStr) {
  if (!timeStr && timeStr !== 0) return 0
  // Se è già un numero (minuti grezzi), ritornalo direttamente
  if (typeof timeStr === 'number') return timeStr
  const parts = String(timeStr).split(':')
  const h = parseInt(parts[0], 10) || 0
  const m = parseInt(parts[1], 10) || 0
  return h * 60 + m
}

function calcLeftPercent(timeOrMinutes) {
  // Accetta sia "HH:MM" che numeri interi (minuti dall'inizio giornata)
  const mins = (typeof timeOrMinutes === 'number') ? timeOrMinutes : timeToMinutes(timeOrMinutes)
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

// ═══════════════════════════════════════════════════════════
// Obiettivo 3: Mappatura cromatica dinamica dal semaforo motore
// Elimina lo Split-Brain: il colore del blocco Gantt dipende
// ESCLUSIVAMENTE dallo status del turno, non dal catalogo.
// ═══════════════════════════════════════════════════════════
const STATUS_COLOR_MAP = {
  'A': { bg: '#c8e6c9', text: 'text-green-9' },   // VERDE
  'B': { bg: '#fff3e0', text: 'text-orange-9' },   // GIALLO
  'C': { bg: '#ef5350', text: 'text-white' },       // ROSSO
  'D': { bg: '#42a5f5', text: 'text-white' },       // BLU
  'VERDE': { bg: '#c8e6c9', text: 'text-green-9' },
  'GIALLO': { bg: '#fff3e0', text: 'text-orange-9' },
  'ROSSO': { bg: '#ef5350', text: 'text-white' },
  'BLU': { bg: '#42a5f5', text: 'text-white' },
}

function _resolveStatus(ride) {
  return ride?.engine_status || ride?.status || ride?.status_code || 'A'
}

function getRideStatusBgColor(ride) {
  const status = _resolveStatus(ride)
  return STATUS_COLOR_MAP[status]?.bg || getActivityColor(ride)
}

function getRideStatusClass(ride) {
  const status = _resolveStatus(ride)
  return STATUS_COLOR_MAP[status]?.text || 'text-white'
}

// Per la vista ROLE: i blocchi trasportano rideStatus dal builder
function getRideStatusBgColorFromBlock(block) {
  const status = block.rideStatus || 'A'
  return STATUS_COLOR_MAP[status]?.bg || block.rideColor || '#607d8b'
}

function getRideStatusClassFromBlock(block) {
  const status = block.rideStatus || 'A'
  return STATUS_COLOR_MAP[status]?.text || 'text-white'
}

// Posizionamento verticale per flussi paralleli
function getBlockTop(block) {
  const total = block.totalFlows || 1
  const idx = block.flowIndex || 0
  if (total <= 1) return 5                    // Flusso singolo: 5% top
  const gap = 4                               // Gap tra flussi in %
  const usable = 100 - gap * (total - 1) - 4  // Spazio disponibile meno margini
  const laneH = usable / total
  return 2 + idx * (laneH + gap)
}

function getBlockHeight(block) {
  const total = block.totalFlows || 1
  if (total <= 1) return 90                   // Flusso singolo: 90% altezza
  const gap = 4
  const usable = 100 - gap * (total - 1) - 4
  return usable / total
}

// Posizionamento verticale per sub-lanes nella Vista Ruoli
function getRoleLaneTop(laneIndex, lanesCount) {
  if (lanesCount <= 1) return 3
  const gap = 2  // Gap tra sub-lanes in %
  const usable = 100 - gap * (lanesCount - 1) - 4  // Margini 2% sopra e sotto
  const laneH = usable / lanesCount
  return 2 + laneIndex * (laneH + gap)
}

function getRoleLaneHeight(lanesCount) {
  if (lanesCount <= 1) return 94
  const gap = 2
  const usable = 100 - gap * (lanesCount - 1) - 4
  return usable / lanesCount
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

  // Fallback Monolitico (attività senza workflow BPMN)
  if (!schema || !schema.flows || schema.flows.length === 0) {
    const defaultDur = act.duration_hours ? (parseFloat(act.duration_hours) * 60) : 120
    let fallbackEndMin = baseStartMin + defaultDur
    if (ride.end_time) fallbackEndMin = timeToMinutes(ride.end_time)

    return [{
      name: act.name || ride.activity_type || 'Turno Singolo',
      startMin: baseStartMin,
      duration: fallbackEndMin - baseStartMin,
      isEnd: false,
      resourceClasses: [],
      flowIndex: 0,
      totalFlows: 1,
      flowName: 'Unico',
      color: null
    }]
  }

  const blocksOutput = []
  const totalFlows = schema.flows.length

  // Calcola durata totale teorica (se serve per stabilire sessionEndMin)
  const durH = parseFloat(act.duration_hours) || 2.0
  let sessionEndMin = baseStartMin + Math.round(durH * 60)
  if (ride.end_time) {
    sessionEndMin = timeToMinutes(ride.end_time)
  }

  for (let fIdx = 0; fIdx < schema.flows.length; fIdx++) {
    const flow = schema.flows[fIdx]
    const blocks = flow.blocks || []
    const flowName = flow.name || `Flusso ${fIdx + 1}`

    // Divide le categorie
    const startBlocks = blocks.filter(b => b.anchor !== 'end')
    const endBlocks = blocks.filter(b => b.anchor === 'end')

    // 1. Ciclo Forward (Acqua / Andata)
    let forwardCursor = baseStartMin
    for (const b of startBlocks) {
      const dur = resolveDuration(b.duration_min ?? b.duration)
      const blockName = b.name || b.code || 'Blocco'

      // Filtra i blocchi-spaziatore invisibili (es. "spazio vuoto")
      if (blockName.toLowerCase().includes('spazio vuoto')) {
        forwardCursor += dur
        continue
      }

      blocksOutput.push({
        name: blockName,
        startMin: forwardCursor,
        duration: dur,
        isEnd: false,
        resourceClasses: b.resources || [],
        flowIndex: fIdx,
        totalFlows: totalFlows,
        flowName: flowName,
        color: b.color || null
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
        name: b.name || b.code || 'Navetta',
        startMin: startMin,
        duration: dur,
        isEnd: true,
        resourceClasses: b.resources || [],
        flowIndex: fIdx,
        totalFlows: totalFlows,
        flowName: flowName,
        color: b.color || null
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
  height: 60px;
  overflow: hidden;
  min-width: 600px;
}
.grid-line {
  border-left: 1px dashed #e0e0e0;
  z-index: 0;
}
.gantt-block {
  z-index: 2;
  transition: opacity 0.2s ease, transform 0.15s ease;
  cursor: pointer;
}
.gantt-block:hover {
  opacity: 1 !important;
  transform: scaleY(1.08);
  z-index: 3;
}
</style>
