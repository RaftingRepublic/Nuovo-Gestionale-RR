<template>
  <q-page class="q-pa-md bg-grey-2">
    <!-- Header Pagina -->
    <div class="row items-center justify-between q-mb-md">
      <div class="text-h5 text-weight-bold text-blue-grey-9">
        {{ isSegreteria ? 'Segreteria (POS)' : 'Calendario Operativo' }}
      </div>
      <div class="row q-gutter-sm items-center">
        <!-- Filtri Visivi Globali -->
        <q-btn-group outline>
          <q-btn :color="viewFilter === 'discese' ? 'primary' : 'white'" :text-color="viewFilter === 'discese' ? 'white' : 'grey-8'" label="DISCESE" @click="viewFilter = 'discese'" size="sm" />
          <q-btn :color="viewFilter === 'staff' ? 'primary' : 'white'" :text-color="viewFilter === 'staff' ? 'white' : 'grey-8'" label="STAFF" @click="viewFilter = 'staff'" size="sm" />
          <q-btn :color="viewFilter === 'tutto' ? 'primary' : 'white'" :text-color="viewFilter === 'tutto' ? 'white' : 'grey-8'" label="TUTTO" @click="viewFilter = 'tutto'" size="sm" />
        </q-btn-group>
        <q-btn color="blue-grey" icon="tune" label="Configura Stagione" outline @click="seasonDialog.isOpen = true" />

      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- VISTA MESE — Calendario mensile con mattoncini cliccabili         -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <div v-if="viewMode === 'MONTH'" class="fit-height-card">
      <CalendarComponent
        :year="currentYear"
        :month="currentMonth"
        :month-data="monthOverview"
        :view-filter="viewFilter"
        v-model:viewMode="calendarDisplayMode"
        @update:month="changeMonth"
        @day-click="openDayDetail"
        @ride-click="onRideClickFromMonth"
        @quick-book="onQuickBookFromMonth"
      />
    </div>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- VISTA GIORNO — Dettaglio turni                                    -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <div v-else class="column" style="min-height: calc(100vh - 140px);">
      <!-- Header navigazione giornaliera -->
      <div class="row items-center q-mb-md q-gutter-sm">
        <q-btn flat icon="arrow_back" label="Torna al Mese" color="primary" @click="goToMonthView" />
        <q-separator vertical class="q-mx-sm" />
        <q-btn round flat icon="chevron_left" @click="prevDay" color="primary" />
        <span class="text-h6 text-weight-bold text-uppercase q-mx-md">{{ formatSelectedDate }}</span>
        <q-btn round flat icon="chevron_right" @click="nextDay" color="primary" />
        <q-btn outline icon="view_column" label="Lavagna Operativa" color="primary" size="sm" class="q-ml-sm" @click="goToBoard" />
        <q-btn outline icon="auto_graph" label="Timeline Flussi" color="indigo-7" size="sm" class="q-ml-xs" @click="router.push('/admin/timeline')" />
        <q-space />
        <q-btn outline icon="download" label="Export FIRAFT (CSV)" color="teal" size="sm" @click="exportFiraft" />
      </div>

      <!-- Griglia turni — OPERATIVO -->
      <div v-if="!isSegreteria" class="col scroll">
        <div v-if="store.loading" class="flex flex-center" style="min-height: 300px;"><q-spinner size="3em" color="primary" /></div>
        <div v-else-if="!filteredDailySchedule || filteredDailySchedule.length === 0" class="flex flex-center text-grey-5 column" style="min-height: 300px;">
          <q-icon name="event_busy" size="4em" />
          <div class="text-h6 q-mt-sm">Nessuna attività programmata per oggi.</div>
        </div>

        <div v-else class="row q-col-gutter-md justify-center">
          <div class="col-12 col-sm-6 col-md-4 col-lg-3" v-for="(slot, idx) in filteredDailySchedule" :key="idx">
            <q-card bordered class="slot-card transition-generic cursor-pointer" :style="{ opacity: slot.booked_pax === 0 ? 0.85 : 1 }" @click="openRideDialog(slot)" v-ripple>
              <q-item>
                <q-item-section avatar>
                  <q-avatar :style="{ backgroundColor: slot.color_hex }" text-color="white" size="48px" font-size="13px">{{ slot.time?.slice(0,5) }}</q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">{{ slot.activity_type }}</q-item-label>
                  <q-item-label caption>
                    <div class="row items-center q-gutter-x-xs q-mt-xs">
                       <q-icon v-if="slot.engine_status === 'ROSSO'" name="warning" color="negative" size="sm" title="Blocco: Guide o Gommoni esauriti" />
                       <q-icon v-if="slot.engine_status === 'GIALLO'" name="local_shipping" color="warning" size="sm" title="Yield Warning: Mancano sedili furgone (Eccezione di Sarre)" />
                       <q-icon v-if="slot.engine_status === 'VERDE'" name="check_circle" color="positive" size="sm" />

                       <div class="text-caption text-weight-bold" :class="{
                          'text-negative': slot.engine_status === 'ROSSO',
                          'text-warning': slot.engine_status === 'GIALLO',
                          'text-primary': slot.engine_status === 'VERDE' || !slot.engine_status
                       }">
                          {{ slot.engine_status === 'ROSSO' ? 'Al Completo / Blocco' : (slot.engine_status === 'GIALLO' ? 'Attenzione: Spola' : 'Disponibile') }}
                       </div>
                       <q-icon v-if="slot.is_overridden" name="lock" size="xs" color="grey-6" class="q-ml-xs" />
                    </div>
                  </q-item-label>
                </q-item-section>
                <q-item-section side v-if="slot.booked_pax === 0">
                  <q-btn flat round dense icon="delete_outline" color="red-4" size="sm" @click.stop="confirmCloseRide(slot)">
                    <q-tooltip>Chiudi turno vuoto</q-tooltip>
                  </q-btn>
                </q-item-section>
              </q-item>
              <q-separator />
              <q-card-section class="q-pa-sm text-center" :class="getSlotBgClass(slot)" v-show="viewFilter === 'tutto' || viewFilter === 'discese'">
                <div class="column items-center justify-center q-my-md">
                   <div class="row items-baseline">
                      <span class="text-h3 text-weight-bold" :class="(slot.engine_status === 'ROSSO' || slot.status_code === 'C') ? 'text-negative' : 'text-primary'">
                         {{ slot.booked_pax || 0 }}
                      </span>
                      <!-- NIMITZ: Nascondi denominatore se capacità >= 1000 (attività senza vincoli) -->
                      <template v-if="!isNimitz(slot)">
                        <span class="text-h5 text-grey-6 q-ml-sm">
                           / {{ slot.total_capacity !== undefined ? slot.total_capacity : '?' }}
                        </span>
                      </template>
                      <span class="text-subtitle1 text-grey-8 q-ml-sm">{{ isNimitz(slot) ? 'pax confermati' : 'pax' }}</span>
                   </div>

                   <!-- Remaining Seats — Riga reattiva con icona Sarre (nascosta per NIMITZ) -->
                   <div v-if="!isNimitz(slot)" class="row items-center justify-center q-mt-xs q-gutter-x-xs">
                      <q-icon
                        v-if="slot.engine_status === 'GIALLO'"
                        name="warning"
                        color="warning"
                        size="18px"
                        title="Eccezione di Sarre: sedili furgone insufficienti, spola necessaria"
                      />
                      <span
                        class="text-caption text-weight-medium"
                        :class="{
                          'text-negative': getRemainingSeats(slot) <= 0,
                          'text-warning': getRemainingSeats(slot) > 0 && getRemainingSeats(slot) <= 4,
                          'text-positive': getRemainingSeats(slot) > 4
                        }"
                      >
                        {{ getRemainingSeats(slot) >= 0 ? getRemainingSeats(slot) : 0 }} posti residui
                      </span>
                   </div>

                   <div style="min-height: 24px;" class="q-mt-sm">
                      <q-badge v-if="slot.arr_bonus_seats > 0" color="info" outline title="Posti ereditati dal fiume (River Ledger)">
                         🌊 +{{ slot.arr_bonus_seats }} ARR Bonus
                      </q-badge>
                   </div>
                </div>
                <!-- NIMITZ: Nascondi progress bar se capacità >= 1000 -->
                <q-linear-progress v-if="slot.total_capacity && !isNimitz(slot)" :value="Math.min(1, (slot.booked_pax || 0) / Math.max(1, slot.total_capacity))" :color="getProgressBarColor(slot.booked_pax, slot.total_capacity)" class="q-mt-xs" rounded />
              </q-card-section>
              <!-- Badge Risorse Assegnate — Visualizzazione Individuale -->
              <q-card-section class="q-pa-xs q-pt-none" v-show="viewFilter === 'tutto' || viewFilter === 'staff'">
                <!-- Risorse da Supabase (assegnate via ride_allocations) -->
                <div class="row q-gutter-xs q-mb-xs wrap" v-if="hasAnyResources(slot)">
                  <!-- Guide individuali (filtrate anti-fantasma) -->
                  <q-chip
                    v-for="g in filterKnownResources(slot.guides)" :key="'g-' + g.id"
                    size="sm" color="teal" text-color="white" icon="person" dense
                  >{{ g.name }}</q-chip>
                  <!-- Autisti / Staff assegnati -->
                  <q-chip
                    v-for="s in filterKnownResources(getDriversFromStaff(slot))" :key="'d-' + s.id"
                    size="sm" color="orange" text-color="white" icon="directions_bus" dense
                  >{{ s.name }}</q-chip>
                  <!-- Gommoni -->
                  <q-chip
                    v-for="r in filterKnownResources(slot.rafts)" :key="'r-' + r.id"
                    size="sm" color="blue" text-color="white" icon="sailing" dense
                  >{{ r.name }}</q-chip>
                  <!-- Furgoni -->
                  <q-chip
                    v-for="v in filterKnownResources(slot.vans)" :key="'v-' + v.id"
                    size="sm" color="deep-orange" text-color="white" icon="local_shipping" dense
                  >{{ v.name }}</q-chip>
                  <!-- Carrelli -->
                  <q-chip
                    v-for="t in filterKnownResources(slot.trailers)" :key="'t-' + t.id"
                    size="sm" color="brown" text-color="white" icon="rv_hookup" dense
                  >{{ t.name }}</q-chip>
                </div>
                <!-- Nessuna risorsa -->
                <div v-else class="text-caption text-grey-4 q-mb-xs text-center" style="font-size: 11px;">
                  Nessuna risorsa assegnata
                </div>
                <q-btn flat dense icon="groups" label="Assegna Risorse" color="primary" class="full-width" size="sm" @click.stop="openResourcePanel(slot)" />
              </q-card-section>
            </q-card>
          </div>
        </div>
        <!-- Legenda Stati -->
        <div class="q-mt-lg q-pa-sm">
          <div class="row wrap justify-center q-gutter-md items-center text-caption text-grey-7">
            <div class="row items-center"><q-badge color="green" class="q-mr-xs" /> Da Caricare</div>
            <div class="row items-center"><q-badge color="blue" class="q-mr-xs" /> Confermato</div>
            <div class="row items-center"><q-badge color="amber" class="q-mr-xs" /> Quasi Pieno</div>
            <div class="row items-center"><q-badge color="red" class="q-mr-xs" /> Pieno / Chiuso</div>
          </div>
        </div>
      </div>

      <!-- Contenuto SEGRETERIA — Migrato nell'Omni-Board (RideDialog tabs) -->
      <div v-else class="col scroll flex flex-center">
        <div class="text-center text-grey-6 q-pa-xl">
          <q-icon name="info" size="3em" class="q-mb-md" />
          <div class="text-h6">La Segreteria è integrata nel Calendario Operativo</div>
          <div class="text-subtitle2 q-mt-sm">Clicca su un turno per aprire la modale POS (tab "Nuova Prenotazione")</div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════ -->
    <!-- COMPONENTI ISOLATI (dialoghi estratti)                    -->
    <!-- ═══════════════════════════════════════════════════════════ -->

    <SeasonConfigDialog ref="seasonDialog" @saved="onSeasonConfigSaved" />

    <ResourcePanel v-model="resourcePanelOpen" :ride="activeResourceSlot" @saved="onResourcePanelSaved" />

    <FiraftDialog
      v-model="firaftModalOpen"
      :order="activeFiraftOrder"
      :ride-context="rideDialogSlot"
      @registered="onFiraftRegistered"
    />

    <RideDialog
      v-model="showRideDialog"
      :ride="rideDialogSlot"
      @delete-order="deleteOrderLocally"
      @open-resources="openResourcePanel"
      @open-firaft="openFiraftModal"
      @refresh="onRideDialogRefresh"
    />

  </q-page>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useResourceStore } from 'stores/resource-store'
import { useQuasar, date as qdate } from 'quasar'
import { supabase } from 'src/supabase'
import CalendarComponent from 'components/CalendarComponent.vue'
import SeasonConfigDialog from 'components/SeasonConfigDialog.vue'
import ResourcePanel from 'components/ResourcePanel.vue'
import FiraftDialog from 'components/FiraftDialog.vue'
import RideDialog from 'components/RideDialog.vue'

const route = useRoute()
const router = useRouter()
const store = useResourceStore()
const $q = useQuasar()
const seasonDialog = ref(null)
// selectedDate: computed bidirezionale ancorato allo store centralizzato
// Formato interno PlanningPage: YYYY/MM/DD (compatibilità Quasar)
// Formato store: YYYY-MM-DD
const selectedDate = computed({
  get: () => store.selectedDate.replace(/-/g, '/'),
  set: (val) => {
    const clean = String(val).replace(/\//g, '-')
    store.selectedDate = clean  // set diretto (senza fetch) per navigazione calendario
  }
})

// Inizializza lo store se c'è un query param
if (route.query.date) {
  store.selectedDate = String(route.query.date).replace(/\//g, '-')
}
// Ambiente determinato dalla rotta
const isSegreteria = computed(() => route.path.includes('segreteria'))

// ═══════════════════════════════════════════════════════════
// CHILD COMPONENT STATE — Variabili di apertura modali
// ═══════════════════════════════════════════════════════════

// Resource Panel
const resourcePanelOpen = ref(false)
const activeResourceSlot = ref(null)

// FIRAFT
const firaftModalOpen = ref(false)
const activeFiraftOrder = ref(null)

// Ride Dialog
const showRideDialog = ref(false)
const rideDialogSlot = ref(null)

// ═══════════════════════════════════════════════════════════
// CALENDAR STATE
// ═══════════════════════════════════════════════════════════
const viewMode = ref(route.query.date ? 'DETAIL' : 'MONTH')
const calendarDisplayMode = ref('DESCENTS')
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const monthOverview = ref([])

// Filtri visivi (DISCESE / STAFF / TUTTO)
const viewFilter = ref('discese')
const filteredDailySchedule = computed(() => {
  if (viewFilter.value === 'discese') {
    return store.dailySchedule.filter(slot => slot.booked_pax > 0 || (slot.orders && slot.orders.length > 0))
  }
  return store.dailySchedule
})

watch(viewMode, (newMode) => {
  // Sincronizza il filtro visivo: in MONTH mostra solo mattoncini, in DETAIL mostra tutto
  viewFilter.value = newMode === 'MONTH' ? 'discese' : 'tutto'
}, { immediate: true })

// WATCHER su store.selectedDate (centralizzato)
watch(() => store.selectedDate, async (newDate) => {
  if (!newDate) return
  if (viewMode.value === 'DETAIL') {
    console.log('[PlanningPage] Watcher store.selectedDate ->', newDate)
    await loadSchedule()
  }
}, { immediate: true })

// ═══════════════════════════════════════════════════════════
// COMPUTED
// ═══════════════════════════════════════════════════════════
const formatSelectedDate = computed(() => {
  if (!selectedDate.value) return ''
  const d = new Date(selectedDate.value.replace(/\//g, '-'))
  return d.toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
})

// ═══════════════════════════════════════════════════════════
// LIFECYCLE
// ═══════════════════════════════════════════════════════════
onMounted(async () => {
  try {
    await store.fetchCatalogs()
    console.log('[SQLite] Attività:', store.activities.length, '| Risorse Supabase:', store.resources.length)

    await Promise.all([
      store.fetchActivityRules(),
      store.fetchStaff(),
      store.fetchFleet(),
    ])
    const [y, m] = selectedDate.value.split('/')
    currentYear.value = parseInt(y)
    currentMonth.value = parseInt(m)
    await updateMonthOverview(currentYear.value, currentMonth.value)

    $q.notify({ type: 'positive', message: '🔄 Sincronizzazione completata', position: 'top', timeout: 2000 })
  } catch(e) {
    console.error('Error in PlanningPage mounted', e)
    $q.notify({
      type: 'negative',
      message: `Errore inizializzazione: ${e.message || 'sconosciuto'}`,
      position: 'top',
      timeout: 0,
      actions: [{ icon: 'close', color: 'white' }]
    })
  }
})

// ═══════════════════════════════════════════════════════════
// CALENDAR NAVIGATION
// ═══════════════════════════════════════════════════════════
async function updateMonthOverview(year, month) {
  try {
    const data = await store.fetchMonthOverview(year, month)
    monthOverview.value = Array.isArray(data) ? data : []
    console.log('[PlanningPage] monthOverview aggiornato:', monthOverview.value.length, 'giorni')
  } catch(e) {
    console.error(e)
    monthOverview.value = []
    $q.notify({ type: 'negative', message: 'Errore caricamento calendario' })
  }
}

function changeMonth(m, y) { currentMonth.value = m; currentYear.value = y; updateMonthOverview(y, m) }
function goToMonthView() { viewMode.value = 'MONTH'; updateMonthOverview(currentYear.value, currentMonth.value) }
function openDayDetail(data) {
  if (!data) return
  const dateStr = data?.scope?.timestamp?.date || data?.timestamp?.date || data?.date || data
  if (dateStr && typeof dateStr === 'string') {
    selectedDate.value = String(dateStr).replace(/-/g, '/')
    viewMode.value = 'DETAIL'
    loadSchedule()
  }
}

async function onRideClickFromMonth({ date, ride }) {
  selectedDate.value = date.replace(/-/g, '/')
  viewMode.value = 'DETAIL'
  await loadSchedule()
  const slot = store.dailySchedule.find(s =>
    s.time?.startsWith(ride.time) || s.activity_type === ride.activity_code
  )
  if (slot) {
    openRideDialog(slot)
  }
}

// ═══════════════════════════════════════════════════════════
// DAY NAVIGATION
// ═══════════════════════════════════════════════════════════
function prevDay() {
  const current = new Date(store.selectedDate)
  const prev = qdate.subtractFromDate(current, { days: 1 })
  const newDate = qdate.formatDate(prev, 'YYYY-MM-DD')
  currentYear.value = prev.getFullYear()
  currentMonth.value = prev.getMonth() + 1
  store.setSelectedDate(newDate)  // Centralizzato: aggiorna store + fetch
}

function nextDay() {
  const current = new Date(store.selectedDate)
  const next = qdate.addToDate(current, { days: 1 })
  const newDate = qdate.formatDate(next, 'YYYY-MM-DD')
  currentYear.value = next.getFullYear()
  currentMonth.value = next.getMonth() + 1
  store.setSelectedDate(newDate)  // Centralizzato: aggiorna store + fetch
}

async function loadSchedule() {
  try {
    const d = selectedDate.value.replace(/\//g, '-')
    await store.fetchDailySchedule(d)
  } catch(e) { console.error(e); $q.notify({ type: 'negative', message: 'Errore caricamento' }) }
}

function goToBoard() {
  const dateParams = selectedDate.value ? String(selectedDate.value).replace(/\//g, '-') : null
  if (dateParams) router.push({ path: '/admin/board', query: { date: dateParams } })
}

// ═══════════════════════════════════════════════════════════
// KILL-SWITCH — Chiudi turno vuoto
// ═══════════════════════════════════════════════════════════
function confirmCloseRide(slot) {
  $q.dialog({
    title: 'Chiudi Turno',
    message: `Confermi la chiusura del turno "${slot.activity_type}" alle ${slot.time?.slice(0,5)}? Il turno scomparirà dal calendario e dalla timeline.`,
    cancel: 'Annulla',
    ok: { label: 'Chiudi Turno', color: 'negative', icon: 'delete' },
    persistent: true,
  }).onOk(async () => {
    try {
      const resp = await fetch('/api/v1/calendar/daily-rides/close', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ride_id: slot.id }),
      })
      if (!resp.ok) {
        const err = await resp.json()
        throw new Error(err.detail || 'Errore chiusura turno')
      }

      // Rimozione reattiva immediata dallo store (senza ricaricare la pagina)
      const idx = store.dailySchedule.findIndex(r => r.id === slot.id)
      if (idx !== -1) store.dailySchedule.splice(idx, 1)

      console.log(`✅ [KILL-SWITCH] Turno ${slot.activity_type} ${slot.time} rimosso (ride: ${slot.id})`)
      $q.notify({ type: 'positive', message: `Turno ${slot.activity_type} ${slot.time?.slice(0,5)} chiuso ✅`, icon: 'check' })

      // Background sync per coerenza
      const cleanDate = String(selectedDate.value).replace(/\//g, '-')
      store.fetchDailySchedule(cleanDate) // Non await — async in background
    } catch (e) {
      console.error(e)
      $q.notify({ type: 'negative', message: e.message || 'Errore chiusura turno' })
    }
  })
}

// ═══════════════════════════════════════════════════════════
// RIDE DIALOG — Apertura
// ═══════════════════════════════════════════════════════════
function openRideDialog(slot) {
  // Prepara il ride_date dal selectedDate per il figlio
  slot.ride_date = selectedDate.value ? String(selectedDate.value).replace(/\//g, '-') : ''
  rideDialogSlot.value = slot
  showRideDialog.value = true
}

// ═══════════════════════════════════════════════════════════
// QUICK-BOOK — Click su Ghost Slot dal calendario mensile
// ═══════════════════════════════════════════════════════════
function onQuickBookFromMonth(ride, dateStr) {
  // Apri il giorno e poi il RideDialog per lo slot corrispondente
  selectedDate.value = dateStr.replace(/-/g, '/')
  viewMode.value = 'DETAIL'
  loadSchedule()
}

// ═══════════════════════════════════════════════════════════
// RESOURCE PANEL — Apertura
// ═══════════════════════════════════════════════════════════
function openResourcePanel(slot) {
  activeResourceSlot.value = slot
  resourcePanelOpen.value = true
}

// ═══════════════════════════════════════════════════════════
// FIRAFT — Apertura
// ═══════════════════════════════════════════════════════════
function openFiraftModal(order) {
  if (!order) return
  activeFiraftOrder.value = order
  firaftModalOpen.value = true
}

// ═══════════════════════════════════════════════════════════
// EXPORT FIRAFT CSV
// ═══════════════════════════════════════════════════════════
function exportFiraft() {
  const d = selectedDate.value.replace(/\//g, '-')
  window.open(`/api/v1/calendar/daily-rides/export-firaft?date=${d}`, '_blank')
}

// ═══════════════════════════════════════════════════════════
// CANCELLAZIONE ORDINE SU SUPABASE (con cleanup ride vuota)
// ═══════════════════════════════════════════════════════════
function deleteOrderLocally(ride, order) {
  $q.dialog({
    title: 'Cancella Prenotazione',
    message: `Confermi la cancellazione dell'ordine di ${order.customer_name || 'Senza nome'} (${order.total_pax || 1} pax)? L'azione è irreversibile.`,
    cancel: { flat: true, label: 'Annulla' },
    ok: { color: 'negative', label: 'Cancella', unelevated: true },
    persistent: true,
  }).onOk(async () => {
    try {
      if (order.id && typeof order.id === 'string' && order.id.length > 10) {
        const { error } = await supabase.from('orders').delete().eq('id', order.id)
        if (error) throw error
      }

      const remainingOrders = (ride?.orders || []).filter(o => o.id !== order.id)
      if (remainingOrders.length === 0 && ride?.id && typeof ride.id === 'string' && ride.id.length > 10) {
        await supabase.from('ride_allocations').delete().eq('ride_id', ride.id)
        const { error: rideErr } = await supabase.from('rides').delete().eq('id', ride.id)
        if (rideErr) console.warn('Errore cleanup ride:', rideErr)
      }

      await reloadCalendarData()

      if (showRideDialog.value && rideDialogSlot.value?.id === ride?.id) {
        const freshSlot = store.dailySchedule.find(s => s.id === ride.id)
        if (freshSlot) {
          rideDialogSlot.value = freshSlot
        } else {
          showRideDialog.value = false
        }
      }

      $q.notify({ type: 'positive', message: 'Prenotazione eliminata dal cloud ✅', icon: 'delete' })
    } catch (err) {
      console.error('Delete order error:', err)
      $q.notify({ type: 'negative', message: 'Errore eliminazione: ' + err.message })
    }
  })
}

// ═══════════════════════════════════════════════════════════
// CALLBACK: Reload dopo azioni dai figli
// ═══════════════════════════════════════════════════════════
async function reloadCalendarData() {
  const dateStr = selectedDate.value.replace(/\//g, '-')
  await store.fetchDailySchedule(dateStr)
  const [yyyy, mm] = dateStr.split('-')
  const monthData = await store.fetchMonthOverview(parseInt(yyyy), parseInt(mm))
  monthOverview.value = Array.isArray(monthData) ? monthData : []
}

async function onSeasonConfigSaved() {
  // Quando vengono salvate le impostazioni della stagione o le eccezioni,
  // dobbiamo forzare un reload completo per rigenerare anche i Ghost Slots
  await store.fetchActivities() // Aggiorna i metadati base
  await reloadCalendarData()    // Rigenera la UI del calendario
}



async function onResourcePanelSaved() {
  const dateStr = selectedDate.value.replace(/\//g, '-')
  await store.fetchDailySchedule(dateStr)
  if (showRideDialog.value && rideDialogSlot.value && activeResourceSlot.value) {
    const freshSlot = store.dailySchedule.find(s => s.id === activeResourceSlot.value.id)
    if (freshSlot) rideDialogSlot.value = freshSlot
  }
  updateMonthOverview(currentYear.value, currentMonth.value)
}

async function onFiraftRegistered() {
  const dateStr = selectedDate.value.replace(/\//g, '-')
  await store.fetchDailySchedule(dateStr)
  if (showRideDialog.value && rideDialogSlot.value) {
    const freshSlot = store.dailySchedule.find(s => s.id === rideDialogSlot.value.id)
    if (freshSlot) rideDialogSlot.value = freshSlot
  }
}

async function onRideDialogRefresh() {
  await reloadCalendarData()
  if (showRideDialog.value && rideDialogSlot.value) {
    // Cerca per ID diretto
    let freshSlot = store.dailySchedule.find(s => s.id === rideDialogSlot.value.id)

    // Fallback: Firma Operativa (activity + time) — gestisce ghost→real ID change post-booking
    if (!freshSlot) {
      const targetName = rideDialogSlot.value.activity_type || rideDialogSlot.value.activity_name || ''
      const targetTime = String(rideDialogSlot.value.time || '').substring(0, 5)
      if (targetName && targetTime) {
        freshSlot = store.dailySchedule.find(s =>
          (s.activity_type === targetName || s.activity_name === targetName) &&
          String(s.time || '').substring(0, 5) === targetTime
        )
      }
    }

    if (freshSlot) rideDialogSlot.value = freshSlot
  }
}

// ═══════════════════════════════════════════════════════════
// HELPERS VISIVI (usati solo nella griglia slot)
// ═══════════════════════════════════════════════════════════

/**
 * Controlla se il turno ha almeno una risorsa assegnata dalla sorgente Supabase.
 */
function hasAnyResources(slot) {
  return (slot.guides?.length > 0) ||
         (slot.drivers?.length > 0) ||
         (slot.rafts?.length > 0) ||
         (slot.vans?.length > 0) ||
         (slot.trailers?.length > 0)
}

/**
 * Estrae le risorse "driver" (autisti) dall'array risorse assegnate.
 * I driver possono essere sia risorse di tipo 'driver' che staff con ruolo NC.
 */
function getDriversFromStaff(slot) {
  // Se il turno ha un array 'drivers' specifico, usalo
  if (slot.drivers && slot.drivers.length > 0) return slot.drivers
  // Altrimenti cerca tra assigned_staff chi ha type 'driver'
  if (slot.assigned_staff) {
    return slot.assigned_staff.filter(s => s.type === 'driver')
  }
  return []
}

/**
 * Filtro Anti-Fantasmi: mostra solo risorse il cui nome esiste
 * nell'anagrafica SQLite corrente (staffList + fleetList).
 */
function filterKnownResources(resources) {
  if (!resources || !Array.isArray(resources)) return []
  const knownNames = new Set([
    ...store.staffList.map(s => (s.name || '').trim().toLowerCase()),
    ...store.fleetList.map(f => (f.name || '').trim().toLowerCase()),
  ])
  return resources.filter(r => {
    if (!r || !r.name) return false
    return knownNames.has(r.name.trim().toLowerCase())
  })
}

// ── NIMITZ THRESHOLD: Soglia capacità oltre la quale si nasconde il denominatore ──
const NIMITZ_THRESHOLD = 1000

function isNimitz(slot) {
  return (slot.total_capacity || 0) >= NIMITZ_THRESHOLD
}

function getProgressBarColor(pax, max = null) {
  if (!max || max >= NIMITZ_THRESHOLD) return 'grey-4'
  if (pax >= max) return 'negative'
  if (pax >= max - 4 && pax > 0) return 'warning'
  return 'primary'
}

function getSlotBgClass(slot) {
  const pax = slot.booked_pax || 0
  const max = slot.total_capacity
  if (!max || max >= NIMITZ_THRESHOLD) return pax > 0 ? 'bg-green-1' : 'bg-white'
  if (pax >= max) return 'bg-red-1'
  if (pax >= max - 4 && pax > 0) return 'bg-orange-1'
  return 'bg-green-1'
}

function getRemainingSeats(slot) {
  // NIMITZ: Non mostrare seats per attività senza vincoli logistici
  if (isNimitz(slot)) return 0
  // Calcolo deterministico: SEMPRE total_capacity - booked_pax (non fidarsi del backend)
  const cap = Number(slot.total_capacity || 0)
  const pax = Number(slot.booked_pax || 0)
  return Math.max(0, cap - pax)
}
</script>

<style scoped>
.fit-height-card { min-height: calc(100vh - 140px); }
.slot-card { transition: transform 0.2s; }
.slot-card:hover { transform: translateY(-3px); box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
.transition-generic { transition: all 0.3s ease; }

@media (max-width: 600px) {
  .q-pa-md { padding: 8px; }
}
</style>
