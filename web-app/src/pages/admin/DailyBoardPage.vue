<template>
  <q-page class="q-pa-xs bg-grey-3">
    <!-- Header compatto -->
    <div class="row items-center justify-between q-mb-xs">
      <div class="text-subtitle1 text-weight-bold text-blue-grey-9 q-ml-sm">
        <q-btn flat dense icon="arrow_back" color="primary" label="Torna al Calendario" @click="goToStandardView" class="q-mr-sm" />
        <q-icon name="view_column" size="sm" class="q-mr-xs" color="primary" />
        Lavagna Operativa
      </div>
      <div>
        <q-input v-model="selectedDate" mask="date" :rules="['date']" outlined dense label="Data" class="bg-white" style="width: 150px">
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

    <!-- Container Lavagna -->
    <div v-if="loading" class="q-pa-xl text-center">
      <q-spinner color="primary" size="2em" />
    </div>
    <div v-else-if="sortedRides.length === 0" class="q-pa-xl text-center text-grey-6 text-subtitle2">
      Lavagna vuota per questa data.
    </div>

    <div v-else class="column q-gutter-y-xs">
      <!-- Riga per ogni turno (Ride) -->
      <q-card v-for="ride in sortedRides" :key="ride.id" flat bordered class="q-pa-xs">
        <div class="row items-stretch">

          <!-- COLONNA 1: INFO TURNO (col-md-3) -->
          <div class="col-12 col-md-3 column justify-between border-right-md q-pr-sm">
             <div class="row items-center justify-between">
                <div class="text-h5 text-bold">{{ String(ride.time).substring(0, 5) }}</div>
                <q-badge :style="{ backgroundColor: ride.color_hex || '#607d8b' }" class="q-px-sm">
                  {{ ride.activity_type || ride.activity_name }}
                </q-badge>
             </div>

             <div class="row items-center justify-between q-mt-xs">
                <div class="text-caption text-weight-medium">PAX: {{ ride.booked_pax || 0 }} / {{ ride.total_capacity || 'N/A' }}</div>
                <q-btn outline dense size="sm" icon="edit" label="Assegna" color="primary" @click="openAssignmentPanel(ride)" />
             </div>
          </div>

          <!-- COLONNA 2: ACQUA (col-md-5) -->
          <div class="col-12 col-md-5 q-px-sm border-right-md column justify-center">
            <div class="text-caption text-grey-6 text-bold q-mb-xs" style="font-size: 10px"><q-icon name="water" /> ACQUA</div>
            <div class="row q-gutter-xs">
              <q-chip
                v-for="(w, i) in getWaterAllocations(ride)"
                :key="'w-'+i"
                dense size="sm"
                :color="w.type === 'RAFT' ? 'blue' : 'teal'"
                text-color="white"
                :icon="w.type === 'RAFT' ? 'sailing' : 'person'"
                class="q-ma-none q-mr-xs q-mb-xs text-weight-medium"
              >
                {{ w.name }}
              </q-chip>
              <span v-if="getWaterAllocations(ride).length === 0" class="text-caption text-grey-4">Nessun assegnamento acqua</span>
            </div>
          </div>

          <!-- COLONNA 3: TERRA / LOGISTICA (col-md-4) -->
          <div class="col-12 col-md-4 q-pl-sm column justify-center">
            <div class="text-caption text-grey-6 text-bold q-mb-xs" style="font-size: 10px"><q-icon name="landscape" /> TERRA / LOGISTICA</div>
            <div class="row q-gutter-xs">
              <q-chip
                v-for="(l, i) in getLandAllocations(ride)"
                :key="'l-'+i"
                dense size="sm"
                :color="l.type === 'VAN' ? 'deep-orange' : (l.type === 'FOTO' ? 'purple' : 'orange-9')"
                text-color="white"
                :icon="l.type === 'VAN' ? 'local_shipping' : (l.type === 'FOTO' ? 'photo_camera' : 'directions_bus')"
                class="q-ma-none q-mr-xs q-mb-xs text-weight-medium relative-position"
              >
                {{ l.name }}
                <q-badge v-if="l.hasTrailer" color="red" floating translucent>+C</q-badge>
              </q-chip>
              <span v-if="getLandAllocations(ride).length === 0" class="text-caption text-grey-4">Nessuna logistica terra</span>
            </div>
          </div>

        </div>
      </q-card>
    </div>

    <!-- Innesto Diretto ResourcePanel -->
    <ResourcePanel v-if="selectedRide" v-model="isPanelOpen" :ride="selectedRide" @update:model-value="onPanelClose" />
  </q-page>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useResourceStore } from 'stores/resource-store'
import ResourcePanel from 'components/ResourcePanel.vue'

const store = useResourceStore()
const route = useRoute()
const router = useRouter()

const isPanelOpen = ref(false)
const selectedRide = ref(null)

const getTodayStr = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
const selectedDate = ref(route.query.date ? String(route.query.date).replace(/-/g, '/') : getTodayStr())
const loading = computed(() => store.loading)

watch(selectedDate, async (newVal) => {
  if (newVal) {
    if (store.activities.length === 0) await store.fetchCatalogs()
    const queryDate = String(newVal).replace(/\//g, '-')
    await store.fetchDailySchedule(queryDate)
  }
}, { immediate: true })

const sortedRides = computed(() => {
  const rides = (store.dailySchedule || []).filter(r => r && !r.isGhost)
  return rides.sort((a, b) => {
    return String(a.time || '').localeCompare(String(b.time || ''))
  })
})

function openAssignmentPanel(ride) {
  selectedRide.value = ride
  isPanelOpen.value = true
}

function goToStandardView() {
  const d = selectedDate.value ? String(selectedDate.value).replace(/\//g, '-') : null
  if (d) router.push({ path: '/admin/operativo', query: { date: d } })
}

async function onPanelClose(isOpen) {
  if (!isOpen && selectedDate.value) {
    const queryDate = String(selectedDate.value).replace(/\//g, '-')
    await store.fetchDailySchedule(queryDate)
  }
}

function getWaterAllocations(ride) {
  const waterResources = []
  if (!ride) return waterResources

  // Da Supabase relations (priorità over assigned_staff) se presenti
  const guides = ride.guides || []
  guides.forEach(g => { waterResources.push({ type: 'STAFF', name: g.name || 'Guida' }) })

  const rafts = ride.rafts || []
  rafts.forEach(r => { waterResources.push({ type: 'RAFT', name: r.name || 'Gommone' }) })

  // Fallback SQLite / Se non ci sono risorse Supabase, prova a pescare da assigned_staff/assigned_fleet
  if (!guides.length && !rafts.length) {
    const astaff = ride.assigned_staff || []
    astaff.forEach(s => {
       const roles = s.roles || []
       const isWater = s.is_guide || roles.some(r => {
           const rt = String(r).toUpperCase()
           return rt.includes('RAF') || rt.includes('HYD') || rt.includes('SK')
       })
       if (isWater) waterResources.push({ type: 'STAFF', name: s.name })
    })

    const afleet = ride.assigned_fleet || []
    afleet.forEach(f => {
      if (f.category === 'RAFT') waterResources.push({ type: 'RAFT', name: f.name })
    })
  }

  return waterResources
}

function getLandAllocations(ride) {
  const landResources = []
  if (!ride) return landResources

  // Da Supabase relations
  const drivers = ride.drivers || []
  drivers.forEach(d => { landResources.push({ type: 'STAFF', name: d.name || 'Autista' }) })

  const vans = ride.vans || []
  vans.forEach(v => { landResources.push({ type: 'VAN', name: v.name || 'Furgone', hasTrailer: false }) })

  const trailers = ride.trailers || []
  const hasTrailer = trailers.length > 0;

  // Usa logica visuale viscerale: se c'è un carrello, appiccica un badge rosso al primo van
  if (hasTrailer && landResources.some(l => l.type === 'VAN')) {
     const van = landResources.find(l => l.type === 'VAN')
     van.hasTrailer = true
  } else if (hasTrailer) {
     trailers.forEach(t => { landResources.push({ type: 'TRAILER', name: t.name, hasTrailer: true }) })
  }

  // Fallback se nessuna delle nuove relazioni Supabase popolata
  if (!drivers.length && !vans.length && !trailers.length) {
    const astaff = ride.assigned_staff || []
    astaff.forEach(s => {
       const roles = s.roles || []
       const isLand = s.is_driver || roles.some(r => {
           const rt = String(r).toUpperCase()
           return rt.includes('DRIV') || rt.includes('FOTO')
       })
       if (isLand) {
           const type = roles.some(r => String(r).toUpperCase().includes('FOTO')) ? 'FOTO' : 'STAFF'
           landResources.push({ type, name: s.name })
       }
    })

    const afleet = ride.assigned_fleet || []
    let hTrailer = false;
    afleet.forEach(f => {
      if (f.category === 'TRAILER') hTrailer = true;
    })

    afleet.forEach(f => {
      if (f.category === 'VAN') landResources.push({ type: 'VAN', name: f.name, hasTrailer: hTrailer })
    })
  }

  return landResources
}
</script>

<style scoped>
.border-right-md {
  border-right: 1px solid #e0e0e0;
}
@media (max-width: 1023px) {
  .border-right-md { border-right: none; border-bottom: 1px solid #eee; margin-bottom: 4px; padding-bottom: 4px; }
}
</style>
