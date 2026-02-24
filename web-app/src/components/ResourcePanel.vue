<template>
  <q-dialog v-model="isOpen" position="right" maximized>
    <q-card style="width: 440px; max-width: 90vw; display: flex; flex-direction: column;" v-if="localSlot">
      <q-card-section class="bg-blue-grey-8 text-white row items-center q-pb-none">
        <div class="text-h6"><q-icon name="handyman" class="q-mr-sm" /> Assegna Risorse</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section class="bg-blue-grey-8 text-white q-pt-xs">
        <div class="text-subtitle2">{{ localSlot.time ? String(localSlot.time).substring(0,5) : '' }} — {{ localSlot.activity_type || localSlot.activity_name || '' }}</div>
        <div class="text-caption">Pax: {{ localSlot.booked_pax || 0 }} / {{ localSlot.total_capacity || 16 }}</div>
      </q-card-section>

      <q-card-section class="q-pt-md scroll" style="flex-grow: 1;">

        <!-- ═══ GUIDE E ISTRUTTORI ═══ -->
        <div class="text-subtitle2 text-primary q-mb-sm"><q-icon name="kayaking" /> Guide e Istruttori</div>
        <q-select
          v-model="localSlot.assigned_guides"
          multiple
          use-chips
          outlined
          dense
          emit-value
          map-options
          :options="filteredGuideOptions"
          option-label="label"
          option-value="value"
          label="Seleziona Guide"
          :option-disable="opt => isOptionBusy(opt) || isDisabledByName(opt, selectedDriverNames)"
        >
          <template #option="{ itemProps, opt, selected, toggleOption }">
            <q-item v-bind="itemProps">
              <q-item-section side>
                <q-checkbox :model-value="selected" @update:model-value="toggleOption(opt)" />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ opt.label }}</q-item-label>
                <q-item-label caption>
                  <q-chip v-for="r in getStaffRoles(opt.value, GUIDE_ROLES)" :key="r" :color="roleColor(r)" text-color="white" size="xs" dense class="q-mr-xs">{{ r }}</q-chip>
                </q-item-label>
              </q-item-section>
              <q-item-section side v-if="isOptionBusy(opt)">
                <q-badge color="red-7" text-color="white" label="Occupato" />
              </q-item-section>
              <q-item-section side v-else-if="isDisabledByName(opt, selectedDriverNames)">
                <q-badge color="orange" text-color="white" label="Autista" />
              </q-item-section>
            </q-item>
          </template>
        </q-select>

        <!-- ═══ AUTISTI / NAVETTE ═══ -->
        <div class="text-subtitle2 text-orange-9 q-mt-lg q-mb-sm"><q-icon name="directions_bus" /> Autisti Navetta</div>
        <q-select
          v-model="localSlot.assigned_drivers"
          multiple
          use-chips
          outlined
          dense
          emit-value
          map-options
          :options="filteredDriverOptions"
          option-label="label"
          option-value="value"
          label="Seleziona Autisti"
          :option-disable="opt => isOptionBusy(opt) || isDisabledByName(opt, selectedGuideNames)"
        >
          <template #option="{ itemProps, opt, selected, toggleOption }">
            <q-item v-bind="itemProps">
              <q-item-section side>
                <q-checkbox :model-value="selected" @update:model-value="toggleOption(opt)" />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ opt.label }}</q-item-label>
                <q-item-label caption>
                  <q-chip v-for="r in getStaffRoles(opt.value, DRIVER_ROLES)" :key="r" :color="roleColor(r)" text-color="white" size="xs" dense class="q-mr-xs">{{ r }}</q-chip>
                </q-item-label>
              </q-item-section>
              <q-item-section side v-if="isOptionBusy(opt)">
                <q-badge color="red-7" text-color="white" label="Occupato" />
              </q-item-section>
              <q-item-section side v-else-if="isDisabledByName(opt, selectedGuideNames)">
                <q-badge color="teal" text-color="white" label="Guida" />
              </q-item-section>
            </q-item>
          </template>
        </q-select>

        <q-separator class="q-my-lg" />

        <!-- ═══ FLOTTA ACQUATICA (Gommoni) ═══ -->
        <div class="text-subtitle2 text-light-blue-8 q-mb-sm"><q-icon name="sailing" /> Flotta Acquatica (Gommoni)</div>
        <q-select
          v-model="localSlot.assigned_boats"
          multiple
          use-chips
          outlined
          dense
          emit-value
          map-options
          :options="filteredRaftOptions"
          option-label="label"
          option-value="value"
          label="Seleziona Gommoni"
          :option-disable="opt => isOptionBusy(opt)"
        />

        <!-- ═══ FURGONI ═══ -->
        <div class="text-subtitle2 text-orange-7 q-mt-lg q-mb-sm"><q-icon name="local_shipping" /> Furgoni e Navette</div>
        <q-select
          v-model="localSlot.assigned_vans"
          multiple
          use-chips
          outlined
          dense
          emit-value
          map-options
          :options="filteredVanOptions"
          option-label="label"
          option-value="value"
          label="Seleziona Furgoni"
          :option-disable="opt => isOptionBusy(opt)"
        />

        <!-- ═══ CARRELLI ═══ -->
        <div class="text-subtitle2 text-brown-8 q-mt-lg q-mb-sm"><q-icon name="rv_hookup" /> Carrelli Rimorchio</div>
        <q-select
          v-model="localSlot.assigned_trailers"
          multiple
          use-chips
          outlined
          dense
          emit-value
          map-options
          :options="filteredTrailerOptions"
          option-label="label"
          option-value="value"
          label="Seleziona Carrelli"
          :option-disable="opt => isOptionBusy(opt)"
        />

        <!-- Anti-ubiquità Info (intra-ride: guida/autista) -->
        <div class="q-mt-lg q-pa-sm bg-amber-1 rounded-borders" v-if="ubiquityConflicts.length > 0">
          <div class="text-caption text-orange-9">
            <q-icon name="warning" class="q-mr-xs" />
            <strong>Anti-Ubiquità:</strong> {{ ubiquityConflicts.join(', ') }}
            {{ ubiquityConflicts.length === 1 ? 'è' : 'sono' }} selezionato come Guida e quindi non disponibile come Autista (e viceversa).
          </div>
        </div>

        <!-- Anti-ubiquità Info (cross-ride: sovrapposizione temporale) -->
        <div class="q-mt-sm q-pa-sm bg-red-1 rounded-borders" v-if="busyResourceNames.size > 0">
          <div class="text-caption text-red-9">
            <q-icon name="block" class="q-mr-xs" />
            <strong>Occupate (altri turni):</strong> {{ busyResourceNames.size }} risorse impegnate in turni sovrapposti.
          </div>
        </div>

        <div class="q-mt-md text-caption text-grey-6">
          Le risorse assegnate vengono salvate nella tabella ride_allocations su Supabase.
        </div>
      </q-card-section>

      <q-card-actions align="right" class="bg-white">
        <q-btn flat label="CHIUDI" color="blue-grey" v-close-popup />
        <q-btn unelevated label="SALVA RISORSE" color="primary" icon="cloud_upload" @click="saveAllocations" :loading="saving" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useResourceStore } from 'stores/resource-store'

const props = defineProps({
  modelValue: Boolean,
  ride: Object
})
const emit = defineEmits(['update:modelValue', 'saved'])

const $q = useQuasar()
const store = useResourceStore()
const saving = ref(false)

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const GUIDE_ROLES = ['RAF4', 'RAF3', 'SK', 'HYD', 'SH', 'CB']
const DRIVER_ROLES = ['N', 'NC']  // NC = legacy transitorio

// ═══ Helper: parsing sicuro orari per overlap detection ═══
const parseTime = (t) => {
  if (!t || typeof t !== 'string' || !t.includes(':')) return 0
  try {
    const [h, m] = t.split(':').map(Number)
    if (isNaN(h) || isNaN(m)) return 0
    return (h * 60) + m
  } catch { return 0 }
}

// ═══ Anti-Ubiquità CROSS-RIDE: risorse occupate in turni sovrapposti ═══
const busyResourceNames = computed(() => {
  const busy = new Set()
  const currentRide = props.ride
  if (!currentRide || !currentRide.time) return busy

  // Durata del turno corrente (da SQLite activity o fallback 2h)
  const currentDur = currentRide.duration_hours || localSlot.duration_hours || 2
  const currentStart = parseTime(currentRide.time)
  const currentEnd = currentStart + (currentDur * 60)

  // Itera sui turni del giorno dallo store (dailySchedule)
  const schedule = store.dailySchedule || []
  for (const ride of schedule) {
    // Escludi i ghost slots — cerchiamo solo turni reali allocati
    if (!ride || ride.isGhost) continue

    // Escludi il turno correntemente aperto nel pannello
    if (currentRide.id && String(ride.id) === String(currentRide.id)) continue

    const rideStart = parseTime(ride.time)
    const rideDur = ride.duration_hours || 2
    const rideEnd = rideStart + (rideDur * 60)

    // Check sovrapposizione rigorosa: Start_A < End_B && End_A > Start_B
    if (currentStart < rideEnd && currentEnd > rideStart) {
      // Raccogli tutti i nomi delle risorse allocate a questo ride
      const allNames = [
        ...(ride.guides || []).map(g => typeof g === 'string' ? g : g?.name),
        ...(ride.drivers || []).map(d => typeof d === 'string' ? d : d?.name),
        ...(ride.rafts || []).map(r => typeof r === 'string' ? r : r?.name),
        ...(ride.vans || []).map(v => typeof v === 'string' ? v : v?.name),
        ...(ride.trailers || []).map(t => typeof t === 'string' ? t : t?.name),
      ]
      for (const name of allNames) {
        if (name) busy.add(name)
      }
    }
  }
  return busy
})

// Helper: controlla se un'opzione è occupata in un altro turno
function isOptionBusy(opt) {
  const name = typeof opt === 'string' ? opt : (opt?.name || opt?.value || opt?.label)
  return busyResourceNames.value.has(name)
}

// Slot locale reattivo — clone del ride passato dal padre
const localSlot = reactive({
  id: null,
  time: '',
  date: '',
  activity_id: null,
  activity_type: '',
  activity_name: '',
  booked_pax: 0,
  total_capacity: 16,
  duration_hours: 2,
  assigned_guides: [],    // Array di nomi (stringhe)
  assigned_drivers: [],
  assigned_boats: [],
  assigned_vans: [],
  assigned_trailers: [],
})

// Assicura che i dati siano caricati
onMounted(async () => {
  if (!store.staffList.length) await store.fetchStaff()
  if (!store.fleetList.length) await store.fetchFleet()
  if (!store.resources.length || !store.activities.length) await store.fetchCatalogs()
})

// ═══════════════════════════════════════════════════════════
// COMPUTED — Opzioni tendine basate su SQLite (store Pinia)
// I value sono NOMI (stringhe) per compatibilità Yield Engine
// ═══════════════════════════════════════════════════════════

// Ruoli specifici per classe attività
const HYDRO_GUIDE_ROLES = ['HYD', 'SH', 'SK', 'CB']
const RAFT_GUIDE_ROLES = ['RAF4', 'RAF3', 'SK', 'CB']

/**
 * Determina la classe dell'attività corrente (HYDRO o RAFTING).
 * Lookup: 1) activity_class dal backend SQLite (se caricata)
 *         2) Fallback: se il titolo contiene "hydro" → HYDRO, altrimenti RAFTING
 */
const currentActivityClass = computed(() => {
  const actId = localSlot.activity_id
  const actName = localSlot.activity_type || localSlot.activity_name || ''

  // Lookup nelle attività SQLite (hanno activity_class, code, color_hex)
  if (actId) {
    const act = store.activities.find(a => String(a.id) === String(actId))
    if (act?.activity_class) return act.activity_class
  }

  // Fallback: deduzione dal nome
  if (actName.toLowerCase().includes('hydro')) return 'HYDRO'
  return 'RAFTING'
})

/**
 * Ruoli guida validi per l'attività corrente.
 * HYDRO: solo brevetti acquatici (HYD, SH, SK, CB)
 * RAFTING: solo brevetti raft (RAF4, RAF3, SK, CB)
 */
const validGuideRoles = computed(() => {
  return currentActivityClass.value === 'HYDRO' ? HYDRO_GUIDE_ROLES : RAFT_GUIDE_ROLES
})

const filteredGuideOptions = computed(() => {
  const roles = validGuideRoles.value
  const conflicts = ubiquityConflicts.value
  return store.staffList
    .filter(s =>
      s.is_active !== false &&
      (s.roles || []).some(r => roles.includes(r)) &&
      !conflicts.includes(s.name)
    )
    .map(s => ({ label: s.name, value: s.name, _roles: s.roles || [] }))
})

const filteredDriverOptions = computed(() => {
  return store.staffList
    .filter(s => s.is_active !== false && (s.roles || []).some(r => DRIVER_ROLES.includes(r)))
    .map(s => ({ label: s.name, value: s.name, _roles: s.roles || [] }))
})

const filteredRaftOptions = computed(() => {
  return store.fleetList
    .filter(f => f.category === 'RAFT' && f.is_active !== false)
    .map(f => ({
      label: f.name + ' (' + (f.capacity || 0) + ' pax)',
      value: f.name,
    }))
})

const filteredVanOptions = computed(() => {
  return store.fleetList
    .filter(f => f.category === 'VAN' && f.is_active !== false)
    .map(f => ({
      label: f.name + ' (' + (f.capacity || 0) + ' posti)' + (f.has_tow_hitch ? ' [🪝 Gancio]' : ''),
      value: f.name,
    }))
})

const filteredTrailerOptions = computed(() => {
  return store.fleetList
    .filter(f => f.category === 'TRAILER' && f.is_active !== false)
    .map(f => ({
      label: f.name + ' (Max ' + (f.max_rafts || 0) + ' gommoni)',
      value: f.name,
    }))
})

// ═══ ANTI-UBIQUITÀ ═══
// Ora lavoriamo con nomi puri
const selectedGuideNames = computed(() => {
  return (localSlot.assigned_guides || []).filter(Boolean)
})

const selectedDriverNames = computed(() => {
  return (localSlot.assigned_drivers || []).filter(Boolean)
})

function isDisabledByName(opt, otherSelectedNames) {
  const name = typeof opt === 'string' ? opt : opt?.value
  return otherSelectedNames.includes(name)
}

// Trova conflitti multi-ruolo (chi è sia guida che autista e compare in una delle due liste)
const ubiquityConflicts = computed(() => {
  const conflicts = []
  const allStaff = store.staffList.filter(s => s.is_active !== false)

  for (const s of allStaff) {
    const roles = s.roles || []
    const isMultiRole = roles.some(r => GUIDE_ROLES.includes(r)) && roles.some(r => DRIVER_ROLES.includes(r))
    if (isMultiRole && (selectedGuideNames.value.includes(s.name) || selectedDriverNames.value.includes(s.name))) {
      conflicts.push(s.name)
    }
  }
  return conflicts
})

// Trova i ruoli di uno staff per nome (per i chip nel dropdown)
function getStaffRoles(name, roleFilter) {
  const staff = store.staffList.find(s => s.name === name)
  if (!staff) return []
  return (staff.roles || []).filter(r => roleFilter.includes(r))
}

// Colori ruoli (coerente con ResourcesPage)
function roleColor(r) {
  if (r === 'RAF4' || r === 'RAF3') return 'teal'
  if (r === 'SK' || r === 'HYD' || r === 'SH') return 'cyan-8'
  if (r === 'N' || r === 'NC') return 'orange'
  if (r === 'C') return 'deep-orange'
  if (r === 'F' || r === 'FOT') return 'purple'
  if (r === 'SEG') return 'pink'
  if (r === 'CB') return 'dark'
  return 'grey'
}

// Pre-popola quando il dialog si apre con le risorse già assegnate al turno
watch(isOpen, (val) => {
  if (val && props.ride) {
    localSlot.id = props.ride.id
    localSlot.time = props.ride.time || ''
    localSlot.date = props.ride.date || ''
    localSlot.activity_id = props.ride.activity_id || null
    localSlot.activity_type = props.ride.activity_type || ''
    localSlot.activity_name = props.ride.activity_name || ''
    localSlot.booked_pax = props.ride.booked_pax || 0
    localSlot.total_capacity = props.ride.total_capacity || 16
    localSlot.duration_hours = props.ride.duration_hours || 2

    // Le risorse tornano da Supabase join come oggetti { id, name, type }
    // → estraiamo i NOMI per allinearci al nuovo sistema name-based
    const extractNames = (arr) => (arr || []).map(item =>
      typeof item === 'string' ? item : (item?.name || '')
    ).filter(Boolean)

    localSlot.assigned_guides = extractNames(props.ride.guides)
    localSlot.assigned_drivers = extractNames(props.ride.drivers)
    localSlot.assigned_boats = extractNames(props.ride.rafts)
    localSlot.assigned_vans = extractNames(props.ride.vans)
    localSlot.assigned_trailers = extractNames(props.ride.trailers)
  }
})

/**
 * Salva le allocazioni su Supabase.
 * Usa ensureSupabaseIds per Auto-Healing: nome → UUID (upsert JIT).
 */
async function saveAllocations() {
  if (!localSlot.id) return
  saving.value = true
  try {
    // Costruisci payload tipizzato: { name, type } per ogni risorsa selezionata
    const buildPayload = (names, type) =>
      (names || []).filter(Boolean).map(name => ({ name, type }))

    const payload = [
      ...buildPayload(localSlot.assigned_guides, 'guide'),
      ...buildPayload(localSlot.assigned_drivers, 'driver'),
      ...buildPayload(localSlot.assigned_boats, 'raft'),
      ...buildPayload(localSlot.assigned_vans, 'van'),
      ...buildPayload(localSlot.assigned_trailers, 'trailer'),
    ]

    console.log('[ResourcePanel] ensureSupabaseIds payload:', payload)

    // Auto-Healing: trova UUID esistenti o crea risorse mancanti
    const allIds = await store.ensureSupabaseIds(payload)

    console.log('[ResourcePanel] UUID risolti:', allIds)

    await store.saveRideAllocations({
      id: localSlot.id,
      date: localSlot.date,
      time: localSlot.time,
      activity_id: localSlot.activity_id,
    }, allIds)

    isOpen.value = false
    $q.notify({ type: 'positive', message: 'Logistica aggiornata nel cloud! ☁️', position: 'top' })
    emit('saved')
  } catch (err) {
    console.error('[ResourcePanel] Save allocations error:', err)
    $q.notify({ type: 'negative', message: 'Errore salvataggio risorse: ' + err.message })
  } finally {
    saving.value = false
  }
}
</script>
