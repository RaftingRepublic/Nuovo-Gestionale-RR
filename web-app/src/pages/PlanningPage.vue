<template>
  <q-page class="q-pa-md bg-grey-2">
    <div class="row items-center justify-between q-mb-md">
      <div class="text-h5 text-weight-bold text-blue-grey-9">Pianificazione Attività</div>
      <q-btn color="primary" icon="add" label="Nuova Prenotazione" unelevated @click="wizardOpen = true" />
    </div>

    <q-card class="shadow-1 fit-height-card my-rounded">
      <q-tabs v-model="tab" class="text-grey-7 bg-white border-bottom" active-color="primary" align="left">
        <q-tab name="CALENDAR" icon="event" label="Calendario Operativo" />
        <q-tab name="CONFIG" icon="settings" label="Configurazione Regole" />
      </q-tabs>
      <q-separator />

      <q-tab-panels v-model="tab" animated class="bg-grey-1 h-full-panels">
        
        <q-tab-panel name="CALENDAR" class="q-pa-md h-full mobile-no-padding">
          
          <!-- FULL CALENDAR MODE -->
          <div v-if="viewMode === 'MONTH'" class="h-full column">
             <CalendarComponent 
                :year="currentYear" 
                :month="currentMonth"
                :month-data="monthOverview"
                v-model:viewMode="calendarDisplayMode"
                @update:month="changeMonth"
                @day-click="openDayDetail"
             />
          </div>

          <!-- DETAIL VIEW MODE -->
          <div v-else class="row q-col-gutter-lg h-full">
            <div class="col-auto border-right bg-white rounded-borders q-pa-sm">
              <q-btn flat icon="arrow_back" label="Torna al Mese" color="primary" class="full-width q-mb-md" @click="goToMonthView" />
              
              <q-date  
                v-model="selectedDate" 
                minimal 
                flat 
                color="primary" 
                @update:model-value="loadSchedule"
                :events="calendarEvents"
                :event-color="calendarEventColor"
                @navigation="onNavigation"
              />
              <div class="q-mt-md text-center text-weight-bold text-primary">
                {{ formatDate(selectedDate) }}
              </div>
              <q-separator class="q-my-md" />
              <div class="q-px-sm">
                <div class="text-caption text-grey-7 q-mb-xs">Legenda Stati:</div>
                <div class="row items-center q-mb-xs"><q-badge color="green" class="q-mr-sm" /> Da Caricare</div>
                <div class="row items-center q-mb-xs"><q-badge color="blue" class="q-mr-sm" /> Confermato</div>
                <div class="row items-center q-mb-xs"><q-badge color="amber" class="q-mr-sm" /> Quasi Pieno</div>
                <div class="row items-center"><q-badge color="red" class="q-mr-sm" /> Pieno / Chiuso</div>
              </div>
            </div>
            
            <div class="col scroll">
              <div v-if="store.loading" class="flex flex-center h-full"><q-spinner size="3em" color="primary" /></div>
              <div v-else-if="store.dailySchedule.length === 0" class="flex flex-center h-full text-grey-5 column">
                <q-icon name="event_busy" size="4em" />
                <div class="text-h6 q-mt-sm">Nessuna attività programmata per oggi.</div>
              </div>
              
              <div v-else class="row q-col-gutter-md">
                <div class="col-12 col-sm-6 col-md-4" v-for="(slot, idx) in store.dailySchedule" :key="idx">
                  <q-card bordered class="slot-card transition-generic cursor-pointer" @click="openSlotDetails(slot)" v-ripple>
                    <q-item>
                      <q-item-section avatar>
                        <q-avatar :style="{ backgroundColor: slot.color_hex }" text-color="white" font-size="16px" font-weight="bold">{{ slot.time }}</q-avatar>
                      </q-item-section>
                      <q-item-section>
                        <q-item-label class="text-weight-bold">{{ slot.activity_type }}</q-item-label>
                        <q-item-label caption class="row items-center">
                          <span :style="{ color: slot.color_hex, fontWeight: 'bold' }">{{ slot.status_desc }}</span>
                          <q-icon v-if="slot.is_overridden" name="lock" size="xs" color="grey-6" class="q-ml-xs" />
                        </q-item-label>
                      </q-item-section>
                      <q-item-section side>
                        <div class="row items-center q-gutter-sm">
                           <q-btn icon="more_vert" flat round dense @click.stop>
                          <q-menu>
                            <q-list dense style="min-width: 150px">
                              <q-item-label header>Forza Stato</q-item-label>
                              <q-item clickable v-close-popup @click="setOverride(slot, 'A')">
                                <q-item-section avatar><q-icon name="circle" color="green" /></q-item-section>
                                <q-item-section>Da Caricare</q-item-section>
                              </q-item>
                              <q-item clickable v-close-popup @click="setOverride(slot, 'D')">
                                <q-item-section avatar><q-icon name="circle" color="blue" /></q-item-section>
                                <q-item-section>Confermato</q-item-section>
                              </q-item>
                              <q-item clickable v-close-popup @click="setOverride(slot, 'B')">
                                <q-item-section avatar><q-icon name="circle" color="amber" /></q-item-section>
                                <q-item-section>Quasi Pieno</q-item-section>
                              </q-item>
                              <q-item clickable v-close-popup @click="setOverride(slot, 'C')">
                                <q-item-section avatar><q-icon name="circle" color="red" /></q-item-section>
                                <q-item-section>Chiuso</q-item-section>
                              </q-item>
                              <q-separator />
                              <q-item clickable v-close-popup @click="deleteOverride(slot)">
                                <q-item-section avatar><q-icon name="replay" /></q-item-section>
                                <q-item-section>Reset (Auto)</q-item-section>
                              </q-item>
                            </q-list>
                          </q-menu>
                        </q-btn>
                        </div>
                      </q-item-section>
                    </q-item>
                    
                    <q-separator />
                    
                    <q-card-section class="q-pa-sm bg-grey-1 text-center">
                        <div class="row justify-center items-baseline">
                            <span class="text-h5 text-weight-bold" :style="{ color: slot.color_hex }">{{ slot.booked_pax }}</span>
                            <span class="text-caption text-grey-6 q-ml-xs">/ {{ Math.min(slot.cap_guides_pax, slot.cap_rafts_pax) }} pax</span>
                        </div>
                        <q-linear-progress :value="slot.booked_pax / Math.max(1, Math.min(slot.cap_guides_pax, slot.cap_rafts_pax))" :color="getStatusColorName(slot.status)" class="q-mt-xs" rounded />
                    </q-card-section>

                    <q-separator />

                    <q-card-section class="q-pa-sm">
                      <div class="row items-center justify-between text-caption q-mb-xs">
                         <div class="row items-center"><q-icon name="sports_rafting" size="xs" class="q-mr-xs"/>Guide:</div>
                         <div class="text-weight-bold">{{ slot.avail_guides }}</div>
                      </div>
                      <div class="row items-center justify-between text-caption q-mb-xs">
                         <div class="row items-center"><q-icon name="sailing" size="xs" class="q-mr-xs"/>Gommoni:</div>
                         <div class="text-weight-bold">{{ slot.avail_rafts }}</div>
                      </div>
                      <div class="row items-center justify-between text-caption">
                         <div class="row items-center"><q-icon name="airport_shuttle" size="xs" class="q-mr-xs"/>Furgoni:</div>
                         <div class="text-weight-bold">{{ slot.avail_vans }}</div>
                      </div>
                    </q-card-section>
                  </q-card>
                </div>
              </div>
            </div>
          </div>
        </q-tab-panel>

        <q-tab-panel name="CONFIG" class="q-pa-md scroll">
          <div class="row justify-between items-center q-mb-md">
            <div class="text-h6">Regole Attive</div>
            <q-btn color="primary" icon="add" label="Nuova Regola" unelevated @click="dialogOpen = true" />
          </div>
          <q-table :rows="store.activityRules" :columns="ruleCols" row-key="id" flat bordered class="bg-white">
            <template v-slot:body-cell-days="props">
              <q-td :props="props">
                <q-badge v-for="d in props.row.days_of_week" :key="d" color="grey-3" text-color="black" class="q-mr-xs">
                  {{ getDayName(d) }}
                </q-badge>
              </q-td>
            </template>
            <template v-slot:body-cell-times="props">
              <q-td :props="props">
                <q-chip v-for="t in props.row.start_times" :key="t" dense color="blue-1" text-color="blue-9" icon="schedule">{{ t }}</q-chip>
              </q-td>
            </template>
            <template v-slot:body-cell-actions="props">
              <q-td :props="props" align="right">
                <q-btn flat round dense icon="delete" color="negative" @click="deleteRule(props.row.id)" />
              </q-td>
            </template>
          </q-table>
        </q-tab-panel>
      </q-tab-panels>
    </q-card>

    <!-- Slot Details Dialog -->
    <q-dialog v-model="slotDetailDialog.open">
       <q-card style="min-width: 600px; max-width: 90vw;">
         <q-card-section class="bg-primary text-white row items-center justify-between">
            <div class="text-h6">
              <q-icon name="group" class="q-mr-sm" /> 
              {{ slotDetailDialog.slot?.time }} - {{ slotDetailDialog.slot?.activity_type }}
            </div>
            <q-btn flat round dense icon="close" v-close-popup />
         </q-card-section>
         
         <q-card-section>
            <div class="row items-center justify-between q-mb-md">
               <div class="text-subtitle1">Prenotazioni Attive</div>
               <q-btn color="primary" icon="add" label="Aggiungi" size="sm" @click="openWizardForSlot(slotDetailDialog.slot)" />
            </div>

            <div v-if="slotRezList.length === 0" class="text-center text-grey q-py-lg">
               <q-icon name="event_seat" size="3em" />
               <div class="q-mt-sm">Nessuna prenotazione</div>
            </div>

            <q-list v-else bordered separator class="rounded-borders">
               <q-item v-for="rez in slotRezList" :key="rez.id">
                 <q-item-section>
                    <q-item-label class="text-weight-bold">
                      {{ rez.first_name || rez.last_name ? `${rez.first_name || ''} ${rez.last_name || ''}`.trim() : rez.customer_name }}
                    </q-item-label>
                    <q-item-label caption>{{ rez.pax }} pax | {{ rez.email || rez.phone || rez.contact_info || '—' }}</q-item-label>
                    <q-item-label caption v-if="rez.price_total">€{{ rez.price_total }} (pagato: €{{ rez.price_paid || 0 }})</q-item-label>
                    <q-item-label caption v-if="rez.notes" class="text-orange-9"><q-icon name="sticky_note_2"/> {{ rez.notes }}</q-item-label>
                 </q-item-section>
                 <q-item-section side top>
                    <q-badge :color="statusColor(rez.order_status)" class="q-mb-xs">{{ rez.order_status || 'IN_ATTESA' }}</q-badge>
                    <q-btn flat round color="negative" icon="delete" size="sm" @click="deleteRez(rez.id)" />
                 </q-item-section>
               </q-item>
            </q-list>
         </q-card-section>
       </q-card>
    </q-dialog>

    <q-dialog v-model="dialogOpen" persistent>
      <q-card style="min-width: 500px">
        <q-card-section class="bg-primary text-white row items-center justify-between">
          <div class="text-h6">Nuova Regola</div>
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-card-section class="q-gutter-md q-mt-sm">
          <q-input v-model="newRule.name" label="Nome" outlined dense />
          <q-select v-model="newRule.activity_type" :options="['FAMILY', 'CLASSICA', 'ADVANCED', 'SELECTION', 'HYDRO_L1', 'HYDRO_L2']" label="Tipo" outlined dense />
          <div class="row q-col-gutter-md">
            <div class="col-6"><q-input v-model="newRule.valid_from" label="Dal" type="date" outlined dense InputLabelProps="{ shrink: true }" /></div>
            <div class="col-6"><q-input v-model="newRule.valid_to" label="Al" type="date" outlined dense InputLabelProps="{ shrink: true }" /></div>
          </div>
          <div>
            <div class="text-caption">Giorni:</div>
            <q-btn-group outline spread>
              <q-btn v-for="(l, i) in weekDays" :key="i" :label="l" :color="newRule.days_of_week.includes(i) ? 'primary' : 'white'" :text-color="newRule.days_of_week.includes(i) ? 'white' : 'grey'" @click="toggleDay(i)" dense size="sm" />
            </q-btn-group>
          </div>
          <div>
            <div class="text-caption">Orari (Scrivi e invio):</div>
            <q-select v-model="newRule.start_times" use-input use-chips multiple hide-dropdown-icon new-value-mode="add-unique" label="es. 09:00" outlined dense />
          </div>
          <div class="row justify-end q-mt-lg"><q-btn label="Salva" color="primary" unelevated @click="saveRule" /></div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <ReservationWizard v-model="wizardOpen" :defaults="wizardDefaults" @saved="onReservationSaved" />
  </q-page>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useResourceStore } from 'stores/resource-store'
import { useReservationStore } from 'stores/reservation-store'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'
import CalendarComponent from 'components/CalendarComponent.vue'
import ReservationWizard from 'components/ReservationWizard.vue'

const store = useResourceStore()
const rezStore = useReservationStore()
const $q = useQuasar()
const tab = ref('CALENDAR')
const selectedDate = ref(new Date().toISOString().split('T')[0].replace(/-/g, '/'))
const dialogOpen = ref(false)
const wizardOpen = ref(false)

// VIEW MODES
const viewMode = ref('MONTH') // 'MONTH' or 'DETAIL'
const calendarDisplayMode = ref('DESCENTS') // 'DESCENTS', 'STAFF', 'BOTH'
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)

// State for Slot Details
const slotDetailDialog = reactive({ open: false, slot: null })
const wizardDefaults = ref(null) // { date, time, activity_type }

// Filter reservations for current slot
const slotRezList = computed(() => {
  if (!slotDetailDialog.slot) return []
  const d = selectedDate.value.replace(/\//g, '-')
  return rezStore.getBySlot(d, slotDetailDialog.slot.time, slotDetailDialog.slot.activity_type)
})

const newRule = reactive({ name: '', activity_type: 'CLASSICA', valid_from: '2026-04-01', valid_to: '2026-09-30', days_of_week: [0,1,2,3,4,5,6], start_times: ['10:00', '14:00'] })
const weekDays = ['L', 'M', 'M', 'G', 'V', 'S', 'D']
const ruleCols = [
  { name: 'name', label: 'Nome', field: 'name', align: 'left' },
  { name: 'type', label: 'Attività', field: 'activity_type', align: 'left' },
  { name: 'period', label: 'Periodo', field: row => `${row.valid_from} -> ${row.valid_to}`, align: 'left' },
  { name: 'days', label: 'Giorni', field: 'days_of_week', align: 'left' },
  { name: 'times', label: 'Orari', field: row => row.start_times.join(', '), align: 'left' },
  { name: 'actions', label: '', field: 'actions', align: 'right' }
]

const monthOverview = ref([])

onMounted(async () => {
  $q.loading.show({ message: 'Inizializzazione...' })
  try {
    await store.fetchActivityRules() 
    const [y, m] = selectedDate.value.split('/')
    currentYear.value = parseInt(y)
    currentMonth.value = parseInt(m)
    await updateMonthOverview(currentYear.value, currentMonth.value)
  } catch(e) {
    console.error('Error in PlanningPage mounted', e)
    $q.notify({ type: 'negative', message: 'Errore inizializzazione pagina' })
  } finally {
    $q.loading.hide()
  }
})

async function updateMonthOverview(year, month) {
  $q.loading.show({ message: 'Aggiornamento calendario...' })
  try {
     const isDetailed = viewMode.value === 'MONTH'
     monthOverview.value = await store.fetchMonthOverview(year, month, isDetailed)
  } catch(e) { 
      console.error('Error fetching month overview', e) 
      $q.notify({ type: 'negative', message: 'Errore caricamento calendario' })
  } finally {
      $q.loading.hide()
  }
}

function changeMonth(m, y) {
    currentMonth.value = m
    currentYear.value = y
    updateMonthOverview(y, m)
}

function goToMonthView() {
    viewMode.value = 'MONTH'
    updateMonthOverview(currentYear.value, currentMonth.value)
}

function openDayDetail(dateStr) {
    selectedDate.value = dateStr.replace(/-/g, '/')
    viewMode.value = 'DETAIL'
    loadSchedule()
}

function onNavigation(view) {
  // Only update overview if we are in detail view (sidebar calendar navigation)
  if (viewMode.value === 'DETAIL') {
      currentYear.value = view.year
      currentMonth.value = view.month
      updateMonthOverview(view.year, view.month)
  }
}

function calendarEvents(date) {
  // QDate format: YYYY/MM/DD. API: YYYY-MM-DD
  const d = date.replace(/\//g, '-')
  const day = monthOverview.value.find(o => o.date === d)
  return day && !day.is_closed
}

function calendarEventColor(date) {
  const d = date.replace(/\//g, '-')
  const day = monthOverview.value.find(o => o.date === d)
  return day ? day.color : 'grey'
}

function formatDate(val) {
  if (!val) return ''
  const d = new Date(val.replace(/\//g, '-'))
  return d.toLocaleDateString('it-IT', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}

async function loadSchedule() {  
  $q.loading.show({ message: 'Caricamento giornata...' })
  try {
      const d = selectedDate.value.replace(/\//g, '-')
      await Promise.all([
          store.fetchDailySchedule(d),
          rezStore.fetchReservations(d)
      ])
  } catch(e) {
      console.error(e)
      $q.notify({ type: 'negative', message: 'Errore caricamento giornata' })
  } finally {
      $q.loading.hide()
  }
}

async function onReservationSaved() {
  loadSchedule()
  await updateMonthOverview(currentYear.value, currentMonth.value)
}

function openSlotDetails(slot) {
  slotDetailDialog.slot = slot
  slotDetailDialog.open = true
}

function openWizardForSlot(slot) {
  // Pre-fill wizard
  const d = selectedDate.value.replace(/\//g, '-')
  wizardDefaults.value = {
    date: d,
    time: slot.time, // Wizard might need to handle time pre-select
    activity_type: slot.activity_type
  }
  slotDetailDialog.open = false
  wizardOpen.value = true
}

async function deleteRez(id) {
    if(!confirm('Eliminare prenotazione?')) return
    try {
        await rezStore.deleteReservation(id)
        $q.notify({ type: 'positive', message: 'Cancellata' })
        loadSchedule() // Update counts
    } catch(e) {
        console.error(e)
        $q.notify({ type: 'negative', message: 'Errore cancellazione' })
    }
}


function getDayName(i) { return weekDays[i] }
function toggleDay(i) { const idx = newRule.days_of_week.indexOf(i); if(idx>-1) newRule.days_of_week.splice(idx,1); else newRule.days_of_week.push(i) }

async function saveRule() { 
  try {
    await store.addActivityRule({...newRule})
    dialogOpen.value = false
    $q.notify({ type: 'positive', message: 'Regola salvata con successo' })
    // If in detailed mode, we should refresh month overview too
    await updateMonthOverview(currentYear.value, currentMonth.value)
  } catch (e) {
    console.error(e)
    $q.notify({ type: 'negative', message: 'Errore salvataggio regola' })
  }
}

async function deleteRule(id) { 
  if(confirm('Eliminare questa regola?')) { 
    try {
      await store.deleteActivityRule(id)
      $q.notify({ type: 'positive', message: 'Regola eliminata' })
      await updateMonthOverview(currentYear.value, currentMonth.value)
    } catch (e) {
      console.error(e)
      $q.notify({ type: 'negative', message: 'Errore eliminazione' })
    }
  } 
}

function getStatusColorName(code) {
  if (code === 'A') return 'green'
  if (code === 'B') return 'amber'
  if (code === 'C') return 'red'
  if (code === 'D') return 'blue'
  return 'grey'
}

function statusColor(status) {
  if (status === 'CONFERMATO') return 'green'
  if (status === 'CANCELLATO') return 'red'
  if (status === 'COMPLETATO') return 'blue'
  return 'orange' // IN_ATTESA
}

async function setOverride(slot, status) {
  try {
     const d = selectedDate.value.replace(/\//g, '-')
     await api.post('/reservations/overrides', {
       date: d,
       time: slot.time,
       activity_type: slot.activity_type,
       forced_status: status
     })
     $q.notify({ type: 'positive', message: 'Stato forzato con successo' })
     loadSchedule()
     // Update calendar too
     updateMonthOverview(currentYear.value, currentMonth.value)
  } catch(e) {
     console.error(e)
     $q.notify({ type: 'negative', message: 'Errore override' })
  }
}

async function deleteOverride(slot) {
  try {
      const d = selectedDate.value.replace(/\//g, '-')
      const res = await api.get('/reservations/overrides', { params: { date: d } })
      const ovr = res.data.find(o => o.time === slot.time && o.activity_type === slot.activity_type)
      if (ovr) {
          await api.delete(`/reservations/overrides/${ovr.id}`)
          $q.notify({ type: 'positive', message: 'Reset completato' })
          loadSchedule()
          updateMonthOverview(currentYear.value, currentMonth.value)
      } else {
          $q.notify({ type: 'info', message: 'Nessuna forzatura attiva' })
      }
  } catch(e) {
      console.error(e)
      $q.notify({ type: 'negative', message: 'Errore reset' })
  }
}
</script>

<style scoped>
.my-rounded { border-radius: 12px; }
.fit-height-card { height: calc(100vh - 100px); min-height: 500px; }
.h-full-panels { height: calc(100% - 50px); }
.border-right { border-right: 1px solid #ddd; }
.slot-card { transition: transform 0.2s; }
.slot-card:hover { transform: translateY(-3px); box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
.transition-generic { transition: all 0.3s ease; }
.h-full { height: 100%; }
.mobile-no-padding { padding: 16px; }
@media (max-width: 600px) {
    .mobile-no-padding { padding: 8px; }
}
</style>