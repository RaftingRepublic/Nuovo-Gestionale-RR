<template>
  <q-page class="q-pa-md bg-grey-2">
    <!-- Header -->
    <div class="row items-center justify-between q-mb-md">
      <div>
        <div class="text-h5 text-weight-bold text-blue-grey-9">
          <q-icon name="point_of_sale" class="q-mr-sm" />
          Segreteria Operativa
        </div>
        <div class="text-caption text-grey-6">Desk POS — Gestione Pagamenti Multi-Metodo</div>
      </div>
    </div>

    <div class="row q-col-gutter-md">

      <!-- ═══════════════════════════════════════════════════════ -->
      <!-- COLONNA SX: RADAR TURNI                                -->
      <!-- ═══════════════════════════════════════════════════════ -->
      <div class="col-12 col-md-4">
        <q-card class="radar-card shadow-2">
          <q-card-section class="bg-blue-grey-9 text-white q-py-sm">
            <div class="text-subtitle1 text-weight-bold">
              <q-icon name="radar" class="q-mr-xs" /> Radar Turni
            </div>
          </q-card-section>

          <q-card-section class="q-pa-sm">
            <q-date
              v-model="selectedDate"
              mask="YYYY-MM-DD"
              minimal
              flat
              class="full-width q-mb-sm"
              color="primary"
              @update:model-value="loadDayRides"
            />
          </q-card-section>

          <q-separator />

          <!-- Lista turni -->
          <q-card-section class="scroll radar-list q-pa-none">
            <div v-if="radarLoading" class="flex flex-center q-pa-xl">
              <q-spinner size="2em" color="primary" />
            </div>

            <div v-else-if="dayRides.length === 0" class="text-center text-grey q-pa-lg">
              <q-icon name="event_busy" size="3em" />
              <div class="q-mt-sm text-body2">Nessun turno per questa data</div>
            </div>

            <q-list v-else separator>
              <q-item
                v-for="ride in dayRides"
                :key="ride.id"
                clickable
                v-ripple
                :class="{ 'bg-blue-1': selectedRide && selectedRide.id === ride.id }"
                @click="selectRide(ride)"
              >
                <q-item-section avatar>
                  <q-avatar
                    :style="{ backgroundColor: ride.color_hex }"
                    text-color="white"
                    size="42px"
                    font-size="12px"
                  >
                    {{ ride.ride_time?.slice(0,5) }}
                  </q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold text-body2">{{ ride.activity_name }}</q-item-label>
                  <q-item-label caption>
                    <q-badge
                      :color="getEngineColor(ride.engine_status)"
                      text-color="white"
                      class="q-mr-xs"
                    >
                      {{ ride.booked_pax }} / {{ ride.total_capacity || '—' }}
                    </q-badge>
                    <span class="text-grey-6">pax</span>
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-icon
                    name="circle"
                    :color="getEngineColor(ride.engine_status)"
                    size="14px"
                  />
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>
      </div>

      <!-- ═══════════════════════════════════════════════════════ -->
      <!-- COLONNA DX: AREA DI LAVORO                             -->
      <!-- ═══════════════════════════════════════════════════════ -->
      <div class="col-12 col-md-8">
        <!-- Placeholder se nessun turno selezionato -->
        <q-card v-if="!selectedRide" class="shadow-1 flex flex-center" style="min-height: 400px;">
          <div class="text-center text-grey-5">
            <q-icon name="touch_app" size="5em" />
            <div class="text-h6 q-mt-md">Seleziona un turno dal Radar</div>
            <div class="text-caption">Clicca su un turno a sinistra per gestire prenotazioni e pagamenti</div>
          </div>
        </q-card>

        <q-card v-else class="shadow-2 work-card">
          <!-- Header turno selezionato -->
          <q-card-section class="bg-primary text-white q-py-sm">
            <div class="row items-center justify-between">
              <div>
                <span class="text-subtitle1 text-weight-bold">{{ selectedRide.activity_name }}</span>
                <span class="q-ml-sm text-caption">
                  {{ selectedRide.ride_time?.slice(0,5) }} ·
                  {{ formatDateIT(selectedDate) }}
                </span>
              </div>
              <q-badge
                :color="getEngineColor(selectedRide.engine_status)"
                text-color="white"
                class="text-body2 q-pa-xs"
              >
                {{ selectedRide.booked_pax }} / {{ selectedRide.total_capacity || '—' }} pax
              </q-badge>
            </div>
          </q-card-section>

          <q-tabs v-model="workTab" class="text-grey-7 bg-white" active-color="primary" align="left" dense>
            <q-tab name="NEW" icon="add_circle" label="Nuova Prenotazione" />
            <q-tab name="ORDERS" icon="receipt_long" label="Ordini Esistenti" />
          </q-tabs>
          <q-separator />

          <q-tab-panels v-model="workTab" animated class="bg-grey-1">

            <!-- ─────────────────────────────────────────────── -->
            <!-- TAB: NUOVA PRENOTAZIONE                         -->
            <!-- ─────────────────────────────────────────────── -->
            <q-tab-panel name="NEW" class="q-pa-md">
              <div class="row q-col-gutter-md">
                <!-- Referente -->
                <div class="col-12">
                  <div class="text-subtitle2 text-blue-grey-8 q-mb-xs">
                    <q-icon name="person" class="q-mr-xs" /> Referente Gruppo
                  </div>
                </div>
                <div class="col-12 col-sm-4">
                  <q-input v-model="form.booker_name" label="Nome referente *" outlined dense />
                </div>
                <div class="col-12 col-sm-4">
                  <q-input v-model="form.booker_phone" label="Telefono" outlined dense />
                </div>
                <div class="col-12 col-sm-4">
                  <q-input v-model="form.booker_email" label="Email" outlined dense />
                </div>

                <!-- Pax -->
                <div class="col-12 col-sm-4">
                  <q-input
                    v-model.number="form.pax"
                    type="number"
                    label="Numero Partecipanti *"
                    outlined dense
                    :min="1"
                  />
                </div>

                <!-- Extra -->
                <div class="col-12">
                  <div class="text-subtitle2 text-blue-grey-8 q-mb-xs">
                    <q-icon name="add_shopping_cart" class="q-mr-xs" /> Extra
                  </div>
                  <div class="row q-gutter-md">
                    <q-checkbox
                      v-model="extraPhoto"
                      label="📸 Servizio Foto (15€)"
                      color="primary"
                    />
                    <q-checkbox
                      v-model="extraVideo"
                      label="🎥 Video (20€)"
                      color="primary"
                    />
                  </div>
                </div>

                <!-- Contabilità Ledger Misto -->
                <div class="col-12">
                  <q-separator class="q-my-sm" />
                  <div class="text-subtitle2 text-blue-grey-8 q-mb-sm">
                    <q-icon name="account_balance" class="q-mr-xs" /> Contabilità (Ledger Misto)
                  </div>

                  <!-- Riepilogo Totali -->
                  <div class="row q-gutter-md q-mb-md">
                    <q-chip icon="shopping_cart" color="blue-2" text-color="blue-9" square>
                      Totale: € {{ computedTotal.toFixed(2) }}
                    </q-chip>
                    <q-chip icon="payments" color="green-2" text-color="green-9" square>
                      Pagato: € {{ computedPaid.toFixed(2) }}
                    </q-chip>
                    <q-chip
                      icon="warning"
                      :color="computedRemaining > 0 ? 'orange-2' : 'green-2'"
                      :text-color="computedRemaining > 0 ? 'orange-9' : 'green-9'"
                      square
                    >
                      Rimane: € {{ computedRemaining.toFixed(2) }}
                    </q-chip>
                  </div>

                  <!-- Transazioni già aggiunte -->
                  <div v-if="form.transactions.length > 0" class="q-mb-md">
                    <q-list bordered separator class="rounded-borders">
                      <q-item v-for="(tx, idx) in form.transactions" :key="idx" dense>
                        <q-item-section avatar>
                          <q-icon :name="getMethodIcon(tx.method)" :color="getMethodColor(tx.method)" />
                        </q-item-section>
                        <q-item-section>
                          <q-item-label>€ {{ tx.amount.toFixed(2) }} — {{ tx.method }}</q-item-label>
                          <q-item-label caption>{{ tx.type }} {{ tx.note ? '· ' + tx.note : '' }}</q-item-label>
                        </q-item-section>
                        <q-item-section side>
                          <q-btn flat round dense icon="delete" color="red" size="sm" @click="removeTx(idx)" />
                        </q-item-section>
                      </q-item>
                    </q-list>
                  </div>

                  <!-- Form aggiunta transazione -->
                  <div class="row q-col-gutter-sm items-end">
                    <div class="col-3">
                      <q-input v-model.number="newTx.amount" type="number" label="Importo €" outlined dense :min="0" />
                    </div>
                    <div class="col-3">
                      <q-select
                        v-model="newTx.method"
                        :options="['CASH', 'SUMUP', 'BONIFICO', 'PARTNERS']"
                        label="Metodo"
                        outlined dense
                      />
                    </div>
                    <div class="col-2">
                      <q-select
                        v-model="newTx.type"
                        :options="['CAPARRA', 'SALDO']"
                        label="Tipo"
                        outlined dense
                      />
                    </div>
                    <div class="col-2">
                      <q-input v-model="newTx.note" label="Note" outlined dense placeholder="Es. Smartbox" />
                    </div>
                    <div class="col-2">
                      <q-btn
                        icon="add"
                        color="primary"
                        unelevated
                        class="full-width"
                        label="Aggiungi"
                        :disable="!newTx.amount || newTx.amount <= 0"
                        @click="addTransaction"
                      />
                    </div>
                  </div>

                  <!-- Calcolatrice Spacca-Conto -->
                  <q-separator class="q-my-md" />
                  <div class="text-subtitle2 text-blue-grey-8 q-mb-xs">
                    <q-icon name="calculate" class="q-mr-xs" /> Calcolatrice Spacca-Conto
                  </div>
                  <div class="row items-center q-gutter-md">
                    <q-input
                      v-model.number="splitCount"
                      type="number"
                      label="Dividi per X persone"
                      outlined dense
                      style="max-width: 200px;"
                      :min="1"
                    />
                    <div class="text-h4 text-weight-bold text-primary" v-if="splitCount > 0">
                      € {{ (computedRemaining / splitCount).toFixed(2) }}
                      <span class="text-body2 text-grey-6">a testa</span>
                    </div>
                  </div>
                </div>

                <!-- Note -->
                <div class="col-12">
                  <q-input v-model="form.notes" label="Note ordine" outlined dense type="textarea" rows="2" />
                </div>

                <!-- Bottone CONFERMA -->
                <div class="col-12">
                  <q-btn
                    icon="check_circle"
                    label="CONFERMA PRENOTAZIONE"
                    color="primary"
                    size="lg"
                    unelevated
                    class="full-width"
                    :loading="saving"
                    :disable="!form.booker_name || form.pax < 1"
                    @click="submitOrder"
                  />
                </div>
              </div>
            </q-tab-panel>

            <!-- ─────────────────────────────────────────────── -->
            <!-- TAB: ORDINI ESISTENTI                           -->
            <!-- ─────────────────────────────────────────────── -->
            <q-tab-panel name="ORDERS" class="q-pa-md">
              <div v-if="ordersLoading" class="flex flex-center q-pa-xl">
                <q-spinner size="2em" color="primary" />
              </div>

              <div v-else-if="rideOrders.length === 0" class="text-center text-grey q-pa-xl">
                <q-icon name="inbox" size="4em" />
                <div class="q-mt-sm text-body1">Nessun ordine per questo turno</div>
              </div>

              <div v-else>
                <q-expansion-item
                  v-for="order in rideOrders"
                  :key="order.id"
                  class="q-mb-sm bg-white rounded-borders shadow-1"
                  header-class="text-weight-bold"
                  expand-icon-class="text-primary"
                >
                  <template v-slot:header>
                    <q-item-section avatar>
                      <q-avatar
                        :color="order.order_status === 'PAGATO' ? 'green' : 'orange'"
                        text-color="white"
                        icon="receipt"
                        size="40px"
                      />
                    </q-item-section>
                    <q-item-section>
                      <q-item-label>{{ order.booker_name || order.customer_name || 'Senza nome' }}</q-item-label>
                      <q-item-label caption>
                        {{ order.total_pax }} pax · € {{ order.price_total?.toFixed(2) }}
                      </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                      <q-badge
                        :color="order.order_status === 'PAGATO' ? 'green' : 'orange'"
                        :label="order.order_status === 'PAGATO' ? '✅ SALDATO' : '⏳ DA SALDARE'"
                      />
                    </q-item-section>
                  </template>

                  <q-card-section>
                    <!-- 4 Bottoni Magici (Mockup Cantiere 3) -->
                    <div class="text-subtitle2 text-blue-grey-7 q-mb-sm">
                      <q-icon name="auto_awesome" class="q-mr-xs" /> Azioni Rapide
                    </div>
                    <div class="row q-gutter-sm q-mb-md">
                      <q-btn round outline icon="link" color="primary" size="md">
                        <q-tooltip>In arrivo: Cantiere 3 — Link Manleva</q-tooltip>
                      </q-btn>
                      <q-btn round outline icon="qr_code" color="primary" size="md">
                        <q-tooltip>In arrivo: Cantiere 3 — QR Code</q-tooltip>
                      </q-btn>
                      <q-btn round outline icon="chat" color="green" size="md">
                        <q-tooltip>In arrivo: Cantiere 3 - WhatsApp Link</q-tooltip>
                      </q-btn>
                      <q-btn round outline icon="group" color="purple" size="md">
                        <q-tooltip>In arrivo: Cantiere 3 — Gestione Partecipanti</q-tooltip>
                      </q-btn>
                    </div>

                    <q-separator class="q-my-sm" />

                    <!-- Drop-outs & Penali -->
                    <div class="text-subtitle2 text-blue-grey-7 q-mb-xs">
                      <q-icon name="person_remove" class="q-mr-xs" /> Drop-outs & Penali
                    </div>
                    <div class="text-caption text-grey-6 q-mb-sm">
                      Se il gruppo si presenta con meno persone, abbassa i pax e aggiungi le penali
                      per incamerare le caparre perse e far quadrare i conti.
                    </div>
                    <div class="row q-col-gutter-sm items-end q-mb-md">
                      <div class="col-3">
                        <q-input
                          v-model.number="editForms[order.id].pax"
                          type="number"
                          label="Pax"
                          outlined dense
                          :min="1"
                        />
                      </div>
                      <div class="col-4">
                        <q-input
                          v-model.number="editForms[order.id].adjustments"
                          type="number"
                          label="Penali / Trattenute (€)"
                          outlined dense
                        />
                      </div>
                      <div class="col-5">
                        <q-btn
                          icon="save"
                          label="Aggiorna Ordine"
                          color="blue-grey"
                          unelevated
                          :loading="editForms[order.id].saving"
                          @click="updateOrder(order.id)"
                        />
                      </div>
                    </div>

                    <q-separator class="q-my-sm" />

                    <!-- Libro Mastro Transazioni -->
                    <div class="text-subtitle2 text-blue-grey-7 q-mb-sm">
                      <q-icon name="account_balance" class="q-mr-xs" /> Libro Mastro Transazioni
                    </div>

                    <div class="row q-gutter-md q-mb-sm">
                      <q-chip icon="shopping_cart" color="blue-2" text-color="blue-9" square dense>
                        Totale: € {{ order.price_total?.toFixed(2) }}
                      </q-chip>
                      <q-chip icon="payments" color="green-2" text-color="green-9" square dense>
                        Pagato: € {{ order.total_paid?.toFixed(2) }}
                      </q-chip>
                      <q-chip
                        icon="warning"
                        :color="order.remaining > 0 ? 'red-2' : 'green-2'"
                        :text-color="order.remaining > 0 ? 'red-9' : 'green-9'"
                        square dense
                      >
                        Rimane: € {{ order.remaining?.toFixed(2) }}
                      </q-chip>
                    </div>

                    <!-- Lista transazioni esistenti -->
                    <q-list v-if="order.transactions && order.transactions.length > 0" bordered separator class="rounded-borders q-mb-md">
                      <q-item v-for="tx in order.transactions" :key="tx.id" dense>
                        <q-item-section avatar>
                          <q-icon :name="getMethodIcon(tx.method)" :color="getMethodColor(tx.method)" />
                        </q-item-section>
                        <q-item-section>
                          <q-item-label>€ {{ tx.amount?.toFixed(2) }} — {{ tx.method }}</q-item-label>
                          <q-item-label caption>{{ tx.type }} {{ tx.note ? '· ' + tx.note : '' }}</q-item-label>
                        </q-item-section>
                        <q-item-section side>
                          <span class="text-caption text-grey-5">
                            {{ tx.timestamp ? new Date(tx.timestamp).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }) : '' }}
                          </span>
                        </q-item-section>
                      </q-item>
                    </q-list>

                    <!-- Aggiungi pagamento -->
                    <div v-if="order.remaining > 0">
                      <div class="text-caption text-grey-7 q-mb-xs">Aggiungi pagamento:</div>
                      <div class="row q-col-gutter-sm items-end">
                        <div class="col-3">
                          <q-input
                            v-model.number="addTxForms[order.id].amount"
                            type="number"
                            label="€"
                            outlined dense
                          />
                        </div>
                        <div class="col-3">
                          <q-select
                            v-model="addTxForms[order.id].method"
                            :options="['CASH', 'SUMUP', 'BONIFICO', 'PARTNERS']"
                            label="Metodo"
                            outlined dense
                          />
                        </div>
                        <div class="col-3">
                          <q-input
                            v-model="addTxForms[order.id].note"
                            label="Note"
                            outlined dense
                          />
                        </div>
                        <div class="col-3">
                          <q-btn
                            icon="add"
                            label="Paga"
                            color="green"
                            unelevated
                            class="full-width"
                            :disable="!addTxForms[order.id].amount || addTxForms[order.id].amount <= 0"
                            :loading="addTxForms[order.id].saving"
                            @click="addPayment(order.id)"
                          />
                        </div>
                      </div>
                    </div>

                    <!-- Registrazioni (slot) -->
                    <q-separator class="q-my-sm" />
                    <div class="text-subtitle2 text-blue-grey-7 q-mb-xs">
                      <q-icon name="group" class="q-mr-xs" /> Partecipanti ({{ order.registrations?.length || 0 }})
                    </div>
                    <q-list dense separator v-if="order.registrations && order.registrations.length > 0">
                      <q-item v-for="reg in order.registrations" :key="reg.id" dense>
                        <q-item-section avatar>
                          <q-icon
                            :name="reg.is_lead ? 'star' : (reg.status === 'COMPLETED' ? 'check_circle' : 'radio_button_unchecked')"
                            :color="reg.is_lead ? 'amber' : (reg.status === 'COMPLETED' ? 'green' : 'grey-4')"
                            size="sm"
                          />
                        </q-item-section>
                        <q-item-section>
                          <q-item-label :class="{ 'text-grey-5': reg.status === 'EMPTY' && !reg.is_lead }">
                            {{ reg.nome }} {{ reg.cognome }}
                          </q-item-label>
                        </q-item-section>
                        <q-item-section side>
                          <q-badge
                            :color="reg.status === 'COMPLETED' ? 'green' : 'grey-4'"
                            :label="reg.status === 'COMPLETED' ? 'Compilato' : 'Vuoto'"
                            dense
                          />
                        </q-item-section>
                      </q-item>
                    </q-list>
                  </q-card-section>
                </q-expansion-item>
              </div>
            </q-tab-panel>
          </q-tab-panels>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useQuasar, date as qdate } from 'quasar'
import { api } from 'boot/axios'

const $q = useQuasar()

// ─── STATE ───────────────────────────────────────────────
const selectedDate = ref(qdate.formatDate(Date.now(), 'YYYY-MM-DD'))
const radarLoading = ref(false)
const dayRides = ref([])
const selectedRide = ref(null)
const workTab = ref('NEW')

// Ordini esistenti
const ordersLoading = ref(false)
const rideOrders = ref([])
const editForms = reactive({})
const addTxForms = reactive({})

// Form nuovo ordine
const saving = ref(false)
const extraPhoto = ref(false)
const extraVideo = ref(false)
const splitCount = ref(1)
const form = reactive({
  booker_name: '',
  booker_phone: '',
  booker_email: '',
  pax: 1,
  notes: '',
  transactions: [],
})
const newTx = reactive({
  amount: null,
  method: 'CASH',
  type: 'SALDO',
  note: '',
})

// ─── COMPUTED ────────────────────────────────────────────
const computedExtras = computed(() => {
  const extras = []
  if (extraPhoto.value) extras.push({ name: 'Servizio Foto', price: 15 })
  if (extraVideo.value) extras.push({ name: 'Video', price: 20 })
  return extras
})

const computedTotal = computed(() => {
  if (!selectedRide.value) return 0
  // Usiamo un prezzo base (ottenuto dall'activity). Approssimazione frontend — il backend ricalcola.
  const base = form.pax * (selectedRide.value._unit_price || 0)
  const extrasSum = computedExtras.value.reduce((a, e) => a + e.price, 0)
  return base + extrasSum
})

const computedPaid = computed(() => {
  return form.transactions.reduce((a, tx) => a + tx.amount, 0)
})

const computedRemaining = computed(() => {
  return Math.max(computedTotal.value - computedPaid.value, 0)
})

// ─── LOAD TURNI ──────────────────────────────────────────
async function loadDayRides () {
  radarLoading.value = true
  selectedRide.value = null
  rideOrders.value = []
  try {
    // selectedDate è già in formato ISO YYYY-MM-DD grazie a mask="YYYY-MM-DD"
    const res = await api.get('/calendar/daily-rides', { params: { date: selectedDate.value } })
    dayRides.value = res.data

    // Arricchisci con prezzo attività (per la calcolatrice frontend)
    const actRes = await api.get('/calendar/activities')
    const actMap = {}
    for (const a of actRes.data) { actMap[a.id] = a }
    for (const r of dayRides.value) {
      const act = actMap[r.activity_id]
      r._unit_price = act ? act.price : 0
      r._manager = act ? act.manager : 'Grape'
    }
  } catch (err) {
    console.error('loadDayRides error:', err)
    const detail = err?.response?.data?.detail || err.message || 'Errore sconosciuto'
    $q.notify({ type: 'negative', message: 'Errore caricamento turni: ' + detail })
  } finally {
    radarLoading.value = false
  }
}

// ─── SELEZIONA TURNO ─────────────────────────────────────
function selectRide (ride) {
  selectedRide.value = ride
  workTab.value = 'NEW'
  resetForm()
  loadOrders(ride.id)
}

// ─── CARICA ORDINI ───────────────────────────────────────
async function loadOrders (rideId) {
  ordersLoading.value = true
  try {
    const res = await api.get(`/orders/by-ride/${rideId}`)
    rideOrders.value = res.data

    // Inizializza edit forms per ogni ordine
    for (const o of rideOrders.value) {
      if (!editForms[o.id]) {
        editForms[o.id] = { pax: o.total_pax, adjustments: o.adjustments || 0, saving: false }
      }
      if (!addTxForms[o.id]) {
        addTxForms[o.id] = { amount: null, method: 'CASH', note: '', saving: false }
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    ordersLoading.value = false
  }
}

// ─── TRANSAZIONE INLINE (form nuovo ordine) ──────────────
function addTransaction () {
  if (!newTx.amount || newTx.amount <= 0) return
  form.transactions.push({
    amount: newTx.amount,
    method: newTx.method,
    type: newTx.type,
    note: newTx.note || null,
  })
  newTx.amount = null
  newTx.note = ''
}

function removeTx (idx) {
  form.transactions.splice(idx, 1)
}

// ─── SUBMIT ORDINE ───────────────────────────────────────
async function submitOrder () {
  if (!form.booker_name || form.pax < 1) return
  saving.value = true

  try {
    const payload = {
      activity_id: selectedRide.value.activity_id,
      date: selectedDate.value,
      time: selectedRide.value.ride_time,
      booker_name: form.booker_name,
      booker_phone: form.booker_phone || null,
      booker_email: form.booker_email || null,
      pax: form.pax,
      adjustments: 0,
      extras: computedExtras.value,
      transactions: form.transactions,
      notes: form.notes || null,
    }

    await api.post('/orders/desk', payload)

    $q.notify({
      type: 'positive',
      message: `✅ Prenotazione confermata! ${form.pax} pax (1 Referente + ${form.pax - 1} Slot Vuoti)`,
      icon: 'check_circle',
    })

    resetForm()
    // Ricarica radar e ordini
    await loadDayRides()
    if (selectedRide.value) {
      // Ri-seleziona lo stesso turno
      const sameRide = dayRides.value.find(r => r.id === selectedRide.value.id)
      if (sameRide) {
        selectedRide.value = sameRide
        await loadOrders(sameRide.id)
      }
    }
  } catch (e) {
    const msg = e?.response?.data?.detail || 'Errore creazione ordine'
    $q.notify({ type: 'negative', message: msg })
  } finally {
    saving.value = false
  }
}

// ─── UPDATE ORDINE (Drop-outs) ───────────────────────────
async function updateOrder (orderId) {
  const ef = editForms[orderId]
  if (!ef) return
  ef.saving = true

  try {
    await api.patch(`/orders/${orderId}`, {
      pax: ef.pax,
      adjustments: ef.adjustments,
    })

    $q.notify({ type: 'positive', message: 'Ordine aggiornato!', icon: 'check' })

    // Ricarica
    if (selectedRide.value) {
      await loadOrders(selectedRide.value.id)
      await loadDayRides()
      const sameRide = dayRides.value.find(r => r.id === selectedRide.value.id)
      if (sameRide) selectedRide.value = sameRide
    }
  } catch (e) {
    const msg = e?.response?.data?.detail || 'Errore aggiornamento'
    $q.notify({ type: 'negative', message: msg })
  } finally {
    ef.saving = false
  }
}

// ─── AGGIUNGI PAGAMENTO A ORDINE ESISTENTE ───────────────
async function addPayment (orderId) {
  const af = addTxForms[orderId]
  if (!af || !af.amount || af.amount <= 0) return
  af.saving = true

  try {
    await api.post(`/orders/${orderId}/transactions`, {
      amount: af.amount,
      method: af.method,
      type: 'SALDO',
      note: af.note || null,
    })

    $q.notify({ type: 'positive', message: 'Pagamento registrato!', icon: 'payments' })

    // Reset form
    af.amount = null
    af.note = ''

    // Ricarica ordini
    if (selectedRide.value) {
      await loadOrders(selectedRide.value.id)
      await loadDayRides()
      const sameRide = dayRides.value.find(r => r.id === selectedRide.value.id)
      if (sameRide) selectedRide.value = sameRide
    }
  } catch (e) {
    const msg = e?.response?.data?.detail || 'Errore pagamento'
    $q.notify({ type: 'negative', message: msg })
  } finally {
    af.saving = false
  }
}

// ─── RESET FORM ──────────────────────────────────────────
function resetForm () {
  form.booker_name = ''
  form.booker_phone = ''
  form.booker_email = ''
  form.pax = 1
  form.notes = ''
  form.transactions = []
  extraPhoto.value = false
  extraVideo.value = false
  splitCount.value = 1
  newTx.amount = null
  newTx.note = ''
}

// ─── HELPERS ─────────────────────────────────────────────
function getEngineColor (status) {
  if (status === 'ROSSO') return 'red'
  if (status === 'GIALLO') return 'amber'
  if (status === 'ARANCIONE') return 'orange'
  if (status === 'VERDE') return 'green'
  if (status === 'BLU') return 'blue'
  return 'grey'
}

function getMethodIcon (method) {
  if (method === 'CASH') return 'payments'
  if (method === 'SUMUP') return 'credit_card'
  if (method === 'BONIFICO') return 'account_balance'
  if (method === 'PARTNERS') return 'handshake'
  return 'attach_money'
}

function getMethodColor (method) {
  if (method === 'CASH') return 'green'
  if (method === 'SUMUP') return 'blue'
  if (method === 'BONIFICO') return 'orange'
  if (method === 'PARTNERS') return 'purple'
  return 'grey'
}

function formatDateIT (val) {
  if (!val) return ''
  const d = new Date(val)
  return d.toLocaleDateString('it-IT', { weekday: 'short', day: 'numeric', month: 'short' })
}

// ─── LIFECYCLE ───────────────────────────────────────────
onMounted(() => {
  loadDayRides()
})
</script>

<style scoped>
.radar-card {
  border-radius: 12px;
  overflow: hidden;
}
.radar-list {
  max-height: calc(100vh - 380px);
  overflow-y: auto;
}
.work-card {
  border-radius: 12px;
  overflow: hidden;
  min-height: 500px;
}
</style>
