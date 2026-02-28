<template>
  <div class="desk-booking-form">
    <div class="row q-col-gutter-md">
      <!-- Referente -->
      <div class="col-12">
        <div class="text-subtitle2 text-blue-grey-8 q-mb-xs">
          <q-icon name="person" class="q-mr-xs" /> Referente Gruppo
        </div>
      </div>
      <div class="col-12 col-sm-4">
        <q-input
          ref="bookerNameRef"
          v-model="form.booker_name"
          label="Nome referente *"
          outlined dense
          lazy-rules
          :rules="[val => !!val && val.trim().length > 0 || 'Il nome è obbligatorio per la cassa']"
        />
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
        <div class="row q-col-gutter-sm items-end wrap">
          <div class="col-12 col-sm-3">
            <q-input v-model.number="newTx.amount" type="number" label="Importo €" outlined dense :min="0" />
          </div>
          <div class="col-12 col-sm-2">
            <q-select
              v-model="newTx.method"
              :options="['CASH', 'SUMUP', 'BONIFICO', 'PARTNERS']"
              label="Metodo"
              outlined dense
            />
          </div>
          <div class="col-12 col-sm-2">
            <q-select
              v-model="newTx.type"
              :options="['CAPARRA', 'SALDO']"
              label="Tipo"
              outlined dense
            />
          </div>
          <div class="col-12 col-sm-3">
            <q-input v-model="newTx.note" label="Note" outlined dense placeholder="Es. Smartbox" />
          </div>
          <div class="col-12 col-sm-2">
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
          :disable="!form.booker_name || !form.booker_name.trim() || form.pax < 1"
          @click="submitOrder"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'

const $q = useQuasar()

// ─── PROPS (iniettate dal turno cliccato nel Calendario) ───
const props = defineProps({
    activityId: String,
    date: String,
    time: String,
    unitPrice: { type: Number, default: 0 }
})

const emit = defineEmits(['success'])

// ─── STATE ─────────────────────────────────────────────────
const saving = ref(false)
const bookerNameRef = ref(null)
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

// ─── COMPUTED ──────────────────────────────────────────────
const computedExtras = computed(() => {
    const extras = []
    if (extraPhoto.value) extras.push({ name: 'Servizio Foto', price: 15 })
    if (extraVideo.value) extras.push({ name: 'Video', price: 20 })
    return extras
})

const computedTotal = computed(() => {
    const base = form.pax * (props.unitPrice || 0)
    const extrasSum = computedExtras.value.reduce((a, e) => a + e.price, 0)
    return base + extrasSum
})

const computedPaid = computed(() => {
    return form.transactions.reduce((a, tx) => a + tx.amount, 0)
})

const computedRemaining = computed(() => {
    return Math.max(computedTotal.value - computedPaid.value, 0)
})

// ─── TRANSAZIONE INLINE ────────────────────────────────────
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

// ─── SUBMIT ORDINE ─────────────────────────────────────────
async function submitOrder () {
    if (!form.booker_name || !form.booker_name.trim() || form.pax < 1) return
    // Forza validazione Quasar per mostrare errore visivo
    if (bookerNameRef.value) {
      bookerNameRef.value.validate()
      if (bookerNameRef.value.hasError) return
    }
    saving.value = true

    try {
        const payload = {
            activity_id: props.activityId,
            date: props.date,
            time: props.time,
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
        emit('success')
    } catch (e) {
        const msg = e?.response?.data?.detail || 'Errore creazione ordine'
        $q.notify({ type: 'negative', message: typeof msg === 'object' ? JSON.stringify(msg) : msg })
    } finally {
        saving.value = false
    }
}

// ─── RESET FORM ────────────────────────────────────────────
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

// ─── HELPERS ───────────────────────────────────────────────
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
</script>
