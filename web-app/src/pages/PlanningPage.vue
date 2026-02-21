<template>
  <q-page class="q-pa-md bg-grey-2">
    <div class="row items-center justify-between q-mb-md">
      <div class="text-h5 text-weight-bold text-blue-grey-9">Pianificazione Attività</div>
      <div class="row q-gutter-sm items-center">
        <q-btn color="blue-grey" icon="tune" label="Configura Stagione" outline @click="seasonDialog.isOpen = true" />
        <q-btn color="primary" icon="add" label="Nuova Prenotazione" unelevated @click="wizardOpen = true" />
      </div>
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
                v-model="selectedDate" minimal flat color="primary"
                @update:model-value="loadSchedule"
                :events="calendarEvents" :event-color="calendarEventColor"
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
                  <q-card bordered class="slot-card transition-generic cursor-pointer" @click="openRideDialog(slot)" v-ripple>
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
                    <q-card-section class="q-pa-sm text-center" :class="slot.engine_status === 'ROSSO' ? 'bg-red-1' : (slot.engine_status === 'GIALLO' ? 'bg-orange-1' : 'bg-green-1')">
                      <span class="text-h5 text-weight-bold" :style="{ color: slot.color_hex }">{{ slot.booked_pax }}</span>
                      <span class="text-caption text-grey-6 q-ml-xs">/ {{ slot.total_capacity || '—' }} pax</span>
                      <q-linear-progress :value="slot.booked_pax / Math.max(1, slot.total_capacity || 1)" :color="getStatusColorName(slot.engine_status)" class="q-mt-xs" rounded />
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
            <q-btn color="primary" icon="add" label="Nuova Regola" unelevated @click="ruleDialogOpen = true" />
          </div>
          <q-table :rows="store.activityRules" :columns="ruleCols" row-key="id" flat bordered class="bg-white">
            <template v-slot:body-cell-days="props">
              <q-td :props="props">
                <q-badge v-for="d in props.row.days_of_week" :key="d" color="grey-3" text-color="black" class="q-mr-xs">{{ getDayName(d) }}</q-badge>
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

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- LIVELLO 1 — DETTAGLIO TURNO (Ride Dialog)                         -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <q-dialog v-model="showRideDialog" position="right" full-height>
      <q-card style="width: 520px; max-width: 95vw;" class="column full-height">
        <!-- Header con bottoni override -->
        <q-card-section class="bg-primary text-white q-py-sm">
          <div class="row items-center justify-between">
            <div>
              <div class="text-h6">{{ rideData?.activity_name }}</div>
              <div class="text-caption">
                {{ rideData?.ride_date }} · {{ rideData?.ride_time }}
                <q-badge :color="getStatusColorName(rideData?.status)" class="q-ml-sm">
                  {{ rideData?.booked_pax || 0 }} pax
                </q-badge>
              </div>
            </div>
            <q-btn flat round dense icon="close" v-close-popup />
          </div>
          <!-- Override Buttons -->
          <div class="row q-gutter-xs q-mt-sm">
            <q-btn dense unelevated size="sm" color="green-8" label="VERDE" @click="setOverride('A')" />
            <q-btn dense unelevated size="sm" color="blue-8" label="BLU" @click="setOverride('D')" />
            <q-btn dense unelevated size="sm" color="amber-8" label="GIALLO" @click="setOverride('B')" />
            <q-btn dense unelevated size="sm" color="red-8" label="ROSSO" @click="setOverride('C')" />
            <q-btn dense outline size="sm" color="white" label="AUTO" @click="clearOverride()" />
          </div>
        </q-card-section>

        <q-separator />

        <!-- Loading -->
        <div v-if="rideLoading" class="flex flex-center q-pa-xl col">
          <q-spinner size="3em" color="primary" />
        </div>

        <!-- Corpo: Lista Ordini -->
        <q-card-section v-else-if="rideData" class="scroll col q-pa-none">
          <div v-if="!rideData.orders || rideData.orders.length === 0" class="text-center text-grey q-pa-xl">
            <q-icon name="event_seat" size="4em" />
            <div class="q-mt-sm">Nessun ordine</div>
          </div>

          <q-list separator v-else>
            <q-item v-for="order in rideData.orders" :key="order.id" clickable v-ripple @click="openOrderDialog(order)">
              <q-item-section avatar>
                <q-avatar :color="orderStatusColor(order.order_status)" text-color="white" icon="receipt" size="40px" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-bold">
                  {{ order.customer_name || 'Senza nome' }}
                </q-item-label>
                <q-item-label caption>
                  {{ order.total_pax }} pax · € {{ order.price_total?.toFixed(2) }}
                  <span v-if="order.discount_applied > 0" class="text-green-8">(-{{ (order.discount_applied * 100).toFixed(0) }}%)</span>
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <div class="column items-end q-gutter-xs">
                  <q-badge :color="orderStatusColor(order.order_status)">{{ order.order_status }}</q-badge>
                  <q-badge v-if="order.order_status === 'IN_ATTESA'" color="orange-2" text-color="orange-10" class="text-caption">
                    <q-icon name="visibility_off" size="12px" class="q-mr-xs" />Fantasma
                  </q-badge>
                  <q-badge v-if="order.is_exclusive_raft" color="purple-2" text-color="purple-10" class="text-caption">
                    🚣 Esclusiva
                  </q-badge>
                </div>
              </q-item-section>
              <q-item-section side>
                <q-icon name="chevron_right" color="grey-5" />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- LIVELLO 2 — DETTAGLI PRENOTAZIONE (Order Dialog)                  -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <q-dialog v-model="showOrderDialog">
      <q-card style="width: 500px; max-width: 95vw;" v-if="selectedOrder">
        <q-card-section class="bg-blue-grey-9 text-white row items-center justify-between q-py-sm">
          <div class="text-h6">Dettagli Prenotazione</div>
          <div class="row q-gutter-xs">
            <q-btn flat round dense icon="group" color="white" @click="openParticipantsDialog()"
              :disable="!selectedOrder.registrations || selectedOrder.registrations.length === 0">
              <q-tooltip>Lista partecipanti</q-tooltip>
            </q-btn>
            <q-btn flat round dense icon="close" v-close-popup />
          </div>
        </q-card-section>

        <q-separator />

        <q-card-section class="q-gutter-sm">
          <!-- Stato -->
          <div class="row items-center q-mb-sm">
            <div class="text-caption text-grey-6 col-4">Stato</div>
            <div class="col">
              <q-badge :color="orderStatusColor(selectedOrder.order_status)" class="text-body2 q-pa-xs">
                {{ selectedOrder.order_status }}
              </q-badge>
              <q-badge v-if="selectedOrder.order_status === 'IN_ATTESA'" color="orange-2" text-color="orange-10" class="q-ml-sm">
                <q-icon name="visibility_off" size="14px" class="q-mr-xs" />Fantasma
              </q-badge>
            </div>
          </div>
          <!-- Pax -->
          <div class="row items-center q-mb-sm">
            <div class="text-caption text-grey-6 col-4">Partecipanti</div>
            <div class="col text-weight-bold">{{ selectedOrder.total_pax }} pax</div>
          </div>
          <!-- Prezzo -->
          <div class="row items-center q-mb-sm">
            <div class="text-caption text-grey-6 col-4">Prezzo Totale</div>
            <div class="col text-weight-bold">
              € {{ selectedOrder.price_total?.toFixed(2) }}
              <span v-if="selectedOrder.discount_applied > 0" class="text-green-8 text-caption">
                (sconto -{{ (selectedOrder.discount_applied * 100).toFixed(0) }}%)
              </span>
            </div>
          </div>
          <!-- Referente -->
          <div class="row items-center q-mb-sm">
            <div class="text-caption text-grey-6 col-4">Referente</div>
            <div class="col">{{ selectedOrder.customer_name || '—' }}</div>
          </div>
          <!-- Email -->
          <div class="row items-center q-mb-sm">
            <div class="text-caption text-grey-6 col-4">Email</div>
            <div class="col">{{ selectedOrder.customer_email || '—' }}</div>
          </div>
          <!-- Esclusiva -->
          <div v-if="selectedOrder.is_exclusive_raft" class="row items-center q-mb-sm">
            <div class="text-caption text-grey-6 col-4">Gommone</div>
            <div class="col"><q-badge color="purple" text-color="white">🚣 Esclusiva</q-badge></div>
          </div>
          <!-- Registrazioni -->
          <div class="row items-center q-mb-sm">
            <div class="text-caption text-grey-6 col-4">Iscritti</div>
            <div class="col">
              <q-btn flat dense color="primary" :label="`${selectedOrder.registrations?.length || 0} partecipanti`"
                icon="group" @click="openParticipantsDialog()"
                :disable="!selectedOrder.registrations || selectedOrder.registrations.length === 0" />
            </div>
          </div>
        </q-card-section>

        <q-separator />

        <!-- Azioni L2 -->
        <q-card-actions align="right" class="bg-grey-1 q-pa-md">
          <q-btn v-if="selectedOrder.order_status === 'IN_ATTESA'"
            label="Conferma Bonifico" color="secondary" icon="check_circle" unelevated
            :loading="confirmingOrderId === selectedOrder.id"
            @click="confirmBonifico(selectedOrder.id)" />
          <q-btn flat label="Chiudi" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- LIVELLO 3 — LISTA PARTECIPANTI (Participants Dialog)              -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <q-dialog v-model="showParticipantsDialog">
      <q-card style="width: 550px; max-width: 95vw;" v-if="selectedOrder">
        <q-card-section class="bg-teal-8 text-white row items-center justify-between q-py-sm">
          <div>
            <div class="text-h6">Lista Partecipanti</div>
            <div class="text-caption">{{ selectedOrder.registrations?.length || 0 }} / {{ selectedOrder.total_pax }}</div>
          </div>
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>

        <q-separator />

        <!-- Lista -->
        <q-card-section class="scroll q-pa-none" style="max-height: 60vh;">
          <q-list separator>
            <q-item v-for="reg in selectedOrder.registrations" :key="reg.id" clickable v-ripple
              @click="openParticipantForm(reg)">
              <!-- Checkbox tesseramento -->
              <q-item-section side v-if="reg.firaft_status === 'DA_TESSERARE'">
                <q-checkbox
                  :model-value="selectedRegistrations.includes(reg.id)"
                  @update:model-value="toggleRegistration(reg.id)"
                  @click.stop
                  dense color="primary"
                />
              </q-item-section>
              <q-item-section side v-else>
                <div style="width: 40px"></div>
              </q-item-section>

              <!-- Nome e Email -->
              <q-item-section>
                <q-item-label class="text-weight-bold">{{ reg.nome }} {{ reg.cognome }}</q-item-label>
                <q-item-label caption>{{ reg.email || '—' }}</q-item-label>
              </q-item-section>

              <!-- Badge Consenso (placeholder) -->
              <q-item-section side>
                <q-icon name="thumb_up" :color="reg.nome ? 'green' : 'grey-4'" size="sm">
                  <q-tooltip>Consenso informato</q-tooltip>
                </q-icon>
              </q-item-section>

              <!-- Badge FiRaft -->
              <q-item-section side>
                <q-icon
                  :name="firaftIcon(reg.firaft_status)"
                  :color="firaftColor(reg.firaft_status)"
                  size="sm"
                >
                  <q-tooltip>{{ firaftLabel(reg.firaft_status) }}</q-tooltip>
                </q-icon>
              </q-item-section>

              <q-item-section side>
                <q-icon name="chevron_right" color="grey-5" />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>

        <q-separator />

        <!-- Footer: Bottone Tessera -->
        <q-card-actions class="bg-grey-2 q-pa-md">
          <div class="text-caption text-grey-7 q-mr-auto" v-if="selectedRegistrations.length > 0">
            {{ selectedRegistrations.length }} selezionat{{ selectedRegistrations.length > 1 ? 'i' : 'o' }}
          </div>
          <q-btn
            label="Tessera Selezionati" color="primary" icon="card_membership" unelevated
            :disable="selectedRegistrations.length === 0"
            :loading="tesseringInProgress"
            @click="tesseraSelezionati"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- LIVELLO 4 — MODIFICA PARTECIPANTE (Participant Form Dialog)       -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <q-dialog v-model="showParticipantFormDialog">
      <q-card style="width: 550px; max-width: 95vw;" v-if="selectedParticipant">
        <q-card-section class="bg-indigo-8 text-white row items-center justify-between q-py-sm">
          <div class="text-h6">Dettaglio Partecipante</div>
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>

        <q-separator />

        <q-card-section class="q-gutter-md scroll" style="max-height: 70vh;">
          <!-- Anagrafica -->
          <div class="text-subtitle2 text-blue-grey-8 q-mb-xs">Anagrafica</div>
          <div class="row q-col-gutter-sm">
            <div class="col-6">
              <q-input v-model="partForm.nome" label="Nome" outlined dense readonly />
            </div>
            <div class="col-6">
              <q-input v-model="partForm.cognome" label="Cognome" outlined dense readonly />
            </div>
          </div>
          <div class="row q-col-gutter-sm">
            <div class="col-6">
              <q-input v-model="partForm.email" label="Email" outlined dense readonly />
            </div>
            <div class="col-6">
              <q-input v-model="partForm.telefono" label="Telefono" outlined dense readonly />
            </div>
          </div>
          <div class="row q-col-gutter-sm">
            <div class="col-4">
              <q-input v-model="partForm.data_nascita" label="Data Nascita" outlined dense readonly />
            </div>
            <div class="col-4">
              <q-input v-model="partForm.sesso" label="Sesso" outlined dense readonly />
            </div>
            <div class="col-4">
              <q-input :model-value="partForm.is_minor ? 'Sì' : 'No'" label="Minore" outlined dense readonly />
            </div>
          </div>
          <q-input v-model="partForm.residenza" label="Residenza" outlined dense readonly />

          <q-separator class="q-my-sm" />

          <!-- Stato FiRaft -->
          <div class="text-subtitle2 text-blue-grey-8 q-mb-xs">Stato Tesseramento</div>
          <div class="row items-center q-gutter-sm">
            <q-icon :name="firaftIcon(partForm.firaft_status)" :color="firaftColor(partForm.firaft_status)" size="md" />
            <span class="text-weight-bold">{{ firaftLabel(partForm.firaft_status) }}</span>
          </div>

          <q-separator class="q-my-sm" />

          <!-- Consensi -->
          <div class="text-subtitle2 text-blue-grey-8 q-mb-xs">Consensi</div>
          <div class="column q-gutter-xs">
            <q-toggle v-model="partForm.consenso_privacy" label="Privacy" disable dense />
            <q-toggle v-model="partForm.consenso_foto" label="Autorizzazione foto/video" disable dense />
            <q-toggle v-model="partForm.consenso_medico" label="Dichiarazione medica" disable dense />
          </div>
        </q-card-section>

        <q-separator />

        <q-card-actions align="right" class="bg-grey-1 q-pa-md">
          <q-btn flat label="Chiudi" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Dialog Nuova Regola -->
    <q-dialog v-model="ruleDialogOpen" persistent>
      <q-card style="min-width: 500px">
        <q-card-section class="bg-primary text-white row items-center justify-between">
          <div class="text-h6">Nuova Regola</div>
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-card-section class="q-gutter-md q-mt-sm">
          <q-input v-model="newRule.name" label="Nome" outlined dense />
          <q-select v-model="newRule.activity_type" :options="['FAMILY', 'CLASSICA', 'ADVANCED', 'SELECTION', 'HYDRO_L1', 'HYDRO_L2']" label="Tipo" outlined dense />
          <div class="row q-col-gutter-md">
            <div class="col-6"><q-input v-model="newRule.valid_from" label="Dal" type="date" outlined dense /></div>
            <div class="col-6"><q-input v-model="newRule.valid_to" label="Al" type="date" outlined dense /></div>
          </div>
          <div>
            <div class="text-caption">Giorni:</div>
            <q-btn-group outline spread>
              <q-btn v-for="(l, i) in weekDays" :key="i" :label="l"
                :color="newRule.days_of_week.includes(i) ? 'primary' : 'white'"
                :text-color="newRule.days_of_week.includes(i) ? 'white' : 'grey'"
                @click="toggleDay(i)" dense size="sm" />
            </q-btn-group>
          </div>
          <div>
            <div class="text-caption">Orari:</div>
            <q-select v-model="newRule.start_times" use-input use-chips multiple hide-dropdown-icon new-value-mode="add-unique" label="es. 09:00" outlined dense />
          </div>
          <div class="row justify-end q-mt-lg"><q-btn label="Salva" color="primary" unelevated @click="saveRule" /></div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <ReservationWizard v-model="wizardOpen" :defaults="wizardDefaults" @saved="onReservationSaved" />
    <SeasonConfigDialog ref="seasonDialog" />
  </q-page>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useResourceStore } from 'stores/resource-store'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'
import CalendarComponent from 'components/CalendarComponent.vue'
import ReservationWizard from 'components/ReservationWizard.vue'
import SeasonConfigDialog from 'components/SeasonConfigDialog.vue'

const store = useResourceStore()
const $q = useQuasar()
const seasonDialog = ref(null)
const tab = ref('CALENDAR')
const selectedDate = ref(new Date().toISOString().split('T')[0].replace(/-/g, '/'))
const wizardOpen = ref(false)
const wizardDefaults = ref(null)
const ruleDialogOpen = ref(false)

// Calendar view state
const viewMode = ref('MONTH')
const calendarDisplayMode = ref('DESCENTS')
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const monthOverview = ref([])

// ═══ LIVELLO 1: Ride Dialog State ═══
const showRideDialog = ref(false)
const rideData = ref(null)
const rideLoading = ref(false)
const currentSlotId = ref(null)

// ═══ LIVELLO 2: Order Dialog State ═══
const showOrderDialog = ref(false)
const selectedOrder = ref(null)
const confirmingOrderId = ref(null)

// ═══ LIVELLO 3: Participants Dialog State ═══
const showParticipantsDialog = ref(false)
const selectedRegistrations = ref([])
const tesseringInProgress = ref(false)

// ═══ LIVELLO 4: Participant Form State ═══
const showParticipantFormDialog = ref(false)
const selectedParticipant = ref(null)
const partForm = reactive({
  nome: '', cognome: '', email: '', telefono: '',
  data_nascita: '', sesso: '', is_minor: false, residenza: '',
  firaft_status: 'NON_RICHIESTO',
  consenso_privacy: false, consenso_foto: false, consenso_medico: false,
})

// Config
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

// ═══════════════════════════════════════════════════════════
// LIFECYCLE
// ═══════════════════════════════════════════════════════════
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

// ═══════════════════════════════════════════════════════════
// CALENDAR NAVIGATION
// ═══════════════════════════════════════════════════════════
async function updateMonthOverview(year, month) {
  $q.loading.show({ message: 'Aggiornamento calendario...' })
  try {
    monthOverview.value = await store.fetchMonthOverview(year, month)
  } catch(e) {
    console.error(e)
    $q.notify({ type: 'negative', message: 'Errore caricamento calendario' })
  } finally {
    $q.loading.hide()
  }
}

function changeMonth(m, y) { currentMonth.value = m; currentYear.value = y; updateMonthOverview(y, m) }
function goToMonthView() { viewMode.value = 'MONTH'; updateMonthOverview(currentYear.value, currentMonth.value) }
function openDayDetail(dateStr) { selectedDate.value = dateStr.replace(/-/g, '/'); viewMode.value = 'DETAIL'; loadSchedule() }
function onNavigation(view) { if (viewMode.value === 'DETAIL') { currentYear.value = view.year; currentMonth.value = view.month; updateMonthOverview(view.year, view.month) } }
function calendarEvents(date) { const d = date.replace(/\//g, '-'); const day = monthOverview.value.find(o => o.date === d); return day && day.booked_rides && day.booked_rides.length > 0 }
function calendarEventColor(date) { const d = date.replace(/\//g, '-'); const day = monthOverview.value.find(o => o.date === d); return day && day.booked_rides && day.booked_rides.length > 0 ? 'primary' : 'grey' }
function formatDate(val) { if (!val) return ''; const d = new Date(val.replace(/\//g, '-')); return d.toLocaleDateString('it-IT', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) }

async function loadSchedule() {
  $q.loading.show({ message: 'Caricamento giornata...' })
  try {
    const d = selectedDate.value.replace(/\//g, '-')
    await store.fetchDailySchedule(d)
  } catch(e) { console.error(e); $q.notify({ type: 'negative', message: 'Errore caricamento' }) }
  finally { $q.loading.hide() }
}

function onReservationSaved() { loadSchedule(); updateMonthOverview(currentYear.value, currentMonth.value) }

// ═══════════════════════════════════════════════════════════
// LIVELLO 1 — Apertura Ride Dialog (Matrioska)
// ═══════════════════════════════════════════════════════════
async function openRideDialog(slot) {
  showRideDialog.value = true
  rideLoading.value = true
  rideData.value = null
  currentSlotId.value = slot.id
  try {
    const res = await api.get(`/calendar/daily-rides/${slot.id}`)
    rideData.value = res.data
  } catch(e) {
    console.error(e)
    $q.notify({ type: 'negative', message: 'Errore caricamento dettagli discesa' })
  } finally {
    rideLoading.value = false
  }
}

async function reloadRideData() {
  if (!currentSlotId.value) return
  try {
    const res = await api.get(`/calendar/daily-rides/${currentSlotId.value}`)
    rideData.value = res.data
  } catch(e) { console.error(e) }
}

// Override di L1
async function setOverride(status) {
  if (!currentSlotId.value) return
  try {
    await api.patch(`/calendar/daily-rides/${currentSlotId.value}/override`, { forced_status: status, clear_override: false })
    $q.notify({ type: 'positive', message: 'Stato forzato' })
    await reloadRideData()
    loadSchedule()
    updateMonthOverview(currentYear.value, currentMonth.value)
  } catch(e) { console.error(e); $q.notify({ type: 'negative', message: 'Errore override' }) }
}

async function clearOverride() {
  if (!currentSlotId.value) return
  try {
    await api.patch(`/calendar/daily-rides/${currentSlotId.value}/override`, { forced_status: 'A', clear_override: true })
    $q.notify({ type: 'positive', message: 'Semaforo automatico ripristinato' })
    await reloadRideData()
    loadSchedule()
    updateMonthOverview(currentYear.value, currentMonth.value)
  } catch(e) { console.error(e); $q.notify({ type: 'negative', message: 'Errore reset' }) }
}

// ═══════════════════════════════════════════════════════════
// LIVELLO 2 — Order Dialog
// ═══════════════════════════════════════════════════════════
function openOrderDialog(order) {
  selectedOrder.value = order
  showOrderDialog.value = true
}

async function confirmBonifico(orderId) {
  confirmingOrderId.value = orderId
  try {
    await api.patch(`/orders/${orderId}/confirm`)
    $q.notify({ type: 'positive', message: 'Bonifico confermato! 👻→✅', icon: 'check_circle' })
    showOrderDialog.value = false
    await reloadRideData()
    loadSchedule()
    updateMonthOverview(currentYear.value, currentMonth.value)
  } catch(e) {
    const msg = e?.response?.data?.detail || 'Errore nella conferma'
    $q.notify({ type: 'negative', message: msg })
  } finally {
    confirmingOrderId.value = null
  }
}

// ═══════════════════════════════════════════════════════════
// LIVELLO 3 — Participants Dialog
// ═══════════════════════════════════════════════════════════
function openParticipantsDialog() {
  selectedRegistrations.value = []
  showParticipantsDialog.value = true
}

function toggleRegistration(regId) {
  const idx = selectedRegistrations.value.indexOf(regId)
  if (idx > -1) selectedRegistrations.value.splice(idx, 1)
  else selectedRegistrations.value.push(regId)
}

async function tesseraSelezionati() {
  if (selectedRegistrations.value.length === 0) return
  tesseringInProgress.value = true
  try {
    const res = await api.post('/firaft/register-bulk', { registration_ids: selectedRegistrations.value })
    $q.notify({ type: 'positive', message: `Tesserati ${res.data.updated_count} partecipanti! 🎫`, caption: res.data.details?.join(', ') })
    selectedRegistrations.value = []
    // Ricarica dati per aggiornare badge FiRaft
    await reloadRideData()
    // Aggiorna l'ordine selezionato con i dati freschi
    if (selectedOrder.value && rideData.value) {
      const fresh = rideData.value.orders.find(o => o.id === selectedOrder.value.id)
      if (fresh) selectedOrder.value = fresh
    }
  } catch {
    $q.notify({ type: 'negative', message: 'Errore tesseramento' })
  } finally {
    tesseringInProgress.value = false
  }
}

// ═══════════════════════════════════════════════════════════
// LIVELLO 4 — Participant Form
// ═══════════════════════════════════════════════════════════
function openParticipantForm(reg) {
  selectedParticipant.value = reg
  partForm.nome = reg.nome || ''
  partForm.cognome = reg.cognome || ''
  partForm.email = reg.email || ''
  partForm.telefono = reg.telefono || ''
  partForm.data_nascita = reg.data_nascita || ''
  partForm.sesso = reg.sesso || ''
  partForm.is_minor = reg.is_minor || false
  partForm.residenza = reg.residenza || ''
  partForm.firaft_status = reg.firaft_status || 'NON_RICHIESTO'
  partForm.consenso_privacy = reg.consenso_privacy || false
  partForm.consenso_foto = reg.consenso_foto || false
  partForm.consenso_medico = reg.consenso_medico || false
  showParticipantFormDialog.value = true
}

// ═══════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════
function getStatusColorName(code) {
  if (code === 'ROSSO' || code === 'C') return 'red'
  if (code === 'GIALLO' || code === 'B') return 'amber'
  if (code === 'VERDE' || code === 'A') return 'green'
  if (code === 'D') return 'blue'
  return 'grey'
}

function orderStatusColor(status) {
  if (status === 'CONFERMATO') return 'green'
  if (status === 'CANCELLATO') return 'red'
  if (status === 'COMPLETATO') return 'blue'
  return 'orange'
}

function firaftIcon(status) {
  if (status === 'TESSERATO') return 'verified'
  if (status === 'DA_TESSERARE') return 'hourglass_empty'
  if (status === 'RIFIUTATO') return 'cancel'
  return 'remove_circle_outline'
}

function firaftColor(status) {
  if (status === 'TESSERATO') return 'green'
  if (status === 'DA_TESSERARE') return 'grey'
  if (status === 'RIFIUTATO') return 'red'
  return 'blue-grey'
}

function firaftLabel(status) {
  if (status === 'TESSERATO') return 'Tesserato ✅'
  if (status === 'DA_TESSERARE') return 'Da tesserare'
  if (status === 'RIFIUTATO') return 'Rifiutato'
  return 'Non richiesto'
}

// Rules
function getDayName(i) { return weekDays[i] }
function toggleDay(i) { const idx = newRule.days_of_week.indexOf(i); if(idx>-1) newRule.days_of_week.splice(idx,1); else newRule.days_of_week.push(i) }

async function saveRule() {
  try {
    await store.addActivityRule({...newRule})
    ruleDialogOpen.value = false
    $q.notify({ type: 'positive', message: 'Regola salvata' })
    await updateMonthOverview(currentYear.value, currentMonth.value)
  } catch(e) { console.error(e); $q.notify({ type: 'negative', message: 'Errore salvataggio' }) }
}

async function deleteRule(id) {
  if(!confirm('Eliminare questa regola?')) return
  try {
    await store.deleteActivityRule(id)
    $q.notify({ type: 'positive', message: 'Regola eliminata' })
    await updateMonthOverview(currentYear.value, currentMonth.value)
  } catch(e) { console.error(e); $q.notify({ type: 'negative', message: 'Errore eliminazione' }) }
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
@media (max-width: 600px) { .mobile-no-padding { padding: 8px; } }
</style>
