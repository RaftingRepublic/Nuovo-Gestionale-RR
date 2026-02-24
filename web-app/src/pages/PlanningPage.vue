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
        <q-btn color="deep-purple" icon="calculate" label="Simulatore" unelevated @click="yieldSimOpen = true">
          <q-tooltip>Motore Matematico Yield</q-tooltip>
        </q-btn>
        <q-btn color="primary" icon="add" label="Nuova Prenotazione" unelevated @click="openBookingForm(null, null)" />
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
                    <span :style="{ color: slot.color_hex, fontWeight: 'bold' }">{{ slot.status_desc }}</span>
                    <q-icon v-if="slot.is_overridden" name="lock" size="xs" color="grey-6" class="q-ml-xs" />
                  </q-item-label>
                </q-item-section>
              </q-item>
              <q-separator />
              <q-card-section class="q-pa-sm text-center" :class="getSlotBgClass(slot)" v-show="viewFilter === 'tutto' || viewFilter === 'discese'">
                <span class="text-h5 text-weight-bold" :style="{ color: slot.color_hex }">{{ slot.booked_pax || 0 }}</span>
                <span v-if="slot.total_capacity" class="text-caption text-grey-6 q-ml-xs">/ {{ slot.total_capacity }} pax</span>
                <span v-else class="text-caption text-grey-6 q-ml-xs">pax</span>
                <q-linear-progress v-if="slot.total_capacity" :value="Math.min(1, (slot.booked_pax || 0) / Math.max(1, slot.total_capacity))" :color="getProgressBarColor(slot.booked_pax, slot.total_capacity)" class="q-mt-xs" rounded />
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
                <!-- Fallback: risorse assegnate via SQLite (assigned_staff / assigned_fleet) -->
                <div class="row q-gutter-xs q-mb-xs wrap" v-else-if="slot.assigned_staff?.length || slot.assigned_fleet?.length">
                  <q-chip v-for="s in slot.assigned_staff" :key="'as'+s.id" dense icon="person" color="teal" text-color="white" size="sm">{{ s.name }}</q-chip>
                  <q-chip v-for="f in slot.assigned_fleet" :key="'af'+f.id" dense :icon="f.category === 'RAFT' ? 'sailing' : 'local_shipping'" :color="f.category === 'RAFT' ? 'blue' : 'orange'" text-color="white" size="sm">{{ f.name }}</q-chip>
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

      <!-- Contenuto SEGRETERIA -->
      <div v-else class="col scroll">
        <DeskDashboardPage :external-date="selectedDate ? selectedDate.replace(/\//g, '-') : null" :hide-calendar="true" />
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════ -->
    <!-- COMPONENTI ISOLATI (dialoghi estratti)                    -->
    <!-- ═══════════════════════════════════════════════════════════ -->

    <SeasonConfigDialog ref="seasonDialog" @saved="onSeasonConfigSaved" />

    <ResourcePanel v-model="resourcePanelOpen" :ride="activeResourceSlot" @saved="onResourcePanelSaved" />

    <BookingDialog
      v-model="bookingDialogOpen"
      :ride-context="bookingRideContext"
      :edit-order="bookingEditOrder"
      :selected-date="selectedDate"
      @saved="onBookingSaved"
    />

    <FiraftDialog
      v-model="firaftModalOpen"
      :order="activeFiraftOrder"
      :ride-context="rideDialogSlot"
      @registered="onFiraftRegistered"
    />

    <RideDialog
      v-model="showRideDialog"
      :ride="rideDialogSlot"
      @edit-order="(order, ride) => openBookingForm(order, ride)"
      @delete-order="deleteOrderLocally"
      @open-resources="openResourcePanel"
      @open-firaft="openFiraftModal"
      @refresh="onRideDialogRefresh"
    />

    <YieldSimulatorDialog
      v-model="yieldSimOpen"
      :initial-date="selectedDate"
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
import BookingDialog from 'components/BookingDialog.vue'
import FiraftDialog from 'components/FiraftDialog.vue'
import RideDialog from 'components/RideDialog.vue'
import DeskDashboardPage from 'pages/DeskDashboardPage.vue'
import YieldSimulatorDialog from 'components/YieldSimulatorDialog.vue'

const route = useRoute()
const router = useRouter()
const store = useResourceStore()
const $q = useQuasar()
const seasonDialog = ref(null)
const selectedDate = ref(route.query.date ? String(route.query.date).replace(/-/g, '/') : new Date().toISOString().split('T')[0].replace(/-/g, '/'))
const yieldSimOpen = ref(false)

// Ambiente determinato dalla rotta
const isSegreteria = computed(() => route.path.includes('segreteria'))

// ═══════════════════════════════════════════════════════════
// CHILD COMPONENT STATE — Variabili di apertura modali
// ═══════════════════════════════════════════════════════════

// Booking Dialog
const bookingDialogOpen = ref(false)
const bookingRideContext = ref(null)
const bookingEditOrder = ref(null)

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
  $q.loading.show({ message: 'Inizializzazione...' })
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

    if (viewMode.value === 'DETAIL') {
      await loadSchedule()
    }

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
  } finally {
    $q.loading.hide()
  }
})

// ═══════════════════════════════════════════════════════════
// CALENDAR NAVIGATION
// ═══════════════════════════════════════════════════════════
async function updateMonthOverview(year, month) {
  $q.loading.show({ message: 'Aggiornamento calendario...' })
  try {
    const data = await store.fetchMonthOverview(year, month)
    monthOverview.value = Array.isArray(data) ? data : []
    console.log('[PlanningPage] monthOverview aggiornato:', monthOverview.value.length, 'giorni')
  } catch(e) {
    console.error(e)
    monthOverview.value = []
    $q.notify({ type: 'negative', message: 'Errore caricamento calendario' })
  } finally {
    $q.loading.hide()
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
  const current = new Date(selectedDate.value.replace(/\//g, '-'))
  const prev = qdate.subtractFromDate(current, { days: 1 })
  selectedDate.value = qdate.formatDate(prev, 'YYYY/MM/DD')
  currentYear.value = prev.getFullYear()
  currentMonth.value = prev.getMonth() + 1
  loadSchedule()
}

function nextDay() {
  const current = new Date(selectedDate.value.replace(/\//g, '-'))
  const next = qdate.addToDate(current, { days: 1 })
  selectedDate.value = qdate.formatDate(next, 'YYYY/MM/DD')
  currentYear.value = next.getFullYear()
  currentMonth.value = next.getMonth() + 1
  loadSchedule()
}

async function loadSchedule() {
  $q.loading.show({ message: 'Caricamento giornata...' })
  try {
    const d = selectedDate.value.replace(/\//g, '-')
    await store.fetchDailySchedule(d)
  } catch(e) { console.error(e); $q.notify({ type: 'negative', message: 'Errore caricamento' }) }
  finally { $q.loading.hide() }
}

function goToBoard() {
  const dateParams = selectedDate.value ? String(selectedDate.value).replace(/\//g, '-') : null
  if (dateParams) router.push({ path: '/admin/board', query: { date: dateParams } })
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
  // Costruisci un contextRide con i dati del ghost per pre-popolare il BookingDialog
  const contextRide = {
    id: ride.id,
    activity_id: ride.activity_id || null,
    activity_name: ride.title || ride.activity_code || '',
    time: ride.time ? String(ride.time).substring(0, 5) : '',
    ride_date: dateStr,
    date: dateStr,
    isGhost: true,
  }
  openBookingForm(null, contextRide)
}

// ═══════════════════════════════════════════════════════════
// BOOKING DIALOG — Apertura
// ═══════════════════════════════════════════════════════════
function openBookingForm(order, contextRide) {
  if (order instanceof Event || (order && typeof order === 'object' && order.type === 'click')) order = null
  if (contextRide instanceof Event || (contextRide && typeof contextRide === 'object' && contextRide.type === 'click')) contextRide = null

  bookingEditOrder.value = order || null
  bookingRideContext.value = contextRide || rideDialogSlot.value || null
  bookingDialogOpen.value = true
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

async function onBookingSaved() {
  await reloadCalendarData()
  if (showRideDialog.value && rideDialogSlot.value) {
    const freshSlot = store.dailySchedule.find(s => s.id === rideDialogSlot.value.id)
    if (freshSlot) rideDialogSlot.value = freshSlot
  }
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
    const freshSlot = store.dailySchedule.find(s => s.id === rideDialogSlot.value.id)
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

function getProgressBarColor(pax, max = null) {
  if (!max) return 'grey-4'
  if (pax >= max) return 'negative'
  if (pax >= max - 4 && pax > 0) return 'warning'
  return 'primary'
}

function getSlotBgClass(slot) {
  const pax = slot.booked_pax || 0
  const max = slot.total_capacity
  if (!max) return pax > 0 ? 'bg-green-1' : 'bg-white'
  if (pax >= max) return 'bg-red-1'
  if (pax >= max - 4 && pax > 0) return 'bg-orange-1'
  return 'bg-green-1'
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
