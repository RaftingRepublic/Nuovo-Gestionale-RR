<template>
  <q-dialog v-model="isOpen" persistent full-width>
    <q-card style="max-width: 1000px; width: 100%;">
      <q-card-section class="bg-primary text-white row items-center justify-between q-py-sm">
        <div class="text-h6">{{ isEdit ? 'Modifica prenotazione' : 'Aggiungi prenotazione' }}</div>
        <q-btn flat round dense icon="close" v-close-popup />
      </q-card-section>

      <q-separator />

      <q-card-section class="scroll" style="max-height: 75vh;">
        <q-form ref="formRef" class="row q-col-gutter-md">
          <!-- Stato ordine -->
          <div class="col-12">
            <q-select
              v-model="form.order_status"
              :options="orderStatusOptions"
              label="Stato ordine"
              outlined dense
              emit-value map-options
            />
          </div>

          <!-- Numero partecipanti + Tipo attività -->
          <div class="col-12 col-md-6">
            <q-input v-model.number="form.pax" type="number" label="Numero partecipanti" outlined dense min="1" :rules="[val => val > 0 || 'Minimo 1']" />
          </div>
          <div class="col-12 col-md-6">
            <q-select v-model="form.activity_type" :options="activityOptions" label="Tipo attività*" outlined dense emit-value map-options :rules="[val => !!val || 'Obbligatorio']" />
          </div>

          <!-- Data + Ora -->
          <div class="col-12 col-md-6">
            <q-input v-model="form.date" type="date" label="Data" outlined dense :rules="[val => !!val || 'Data obbligatoria']">
              <template v-slot:prepend>
                <q-icon name="event" />
              </template>
            </q-input>
          </div>
          <div class="col-12 col-md-6">
            <q-select
              v-model="form.time"
              :options="timeOptions"
              label="Ora"
              outlined dense
              emit-value map-options
              :loading="loadingSlots"
            >
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section avatar>
                    <q-icon name="circle" :color="scope.opt.qColor" size="sm" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label class="text-weight-bold">
                      {{ scope.opt.timeLabel }}
                      <q-icon v-if="scope.opt.isFull" name="warning" color="orange" size="xs" class="q-ml-xs" />
                    </q-item-label>
                    <q-item-label caption>{{ scope.opt.desc }}</q-item-label>
                  </q-item-section>
                  <q-item-section side>
                    <q-badge :color="scope.opt.qColor" text-color="white">
                      {{ scope.opt.remaining }} posti
                    </q-badge>
                  </q-item-section>
                </q-item>
              </template>
              <template v-slot:no-option>
                <q-item><q-item-section class="text-grey">Nessuno slot disponibile</q-item-section></q-item>
              </template>
            </q-select>
          </div>

          <!-- Prezzo totale + Prezzo pagato -->
          <div class="col-12 col-md-6">
            <q-input v-model.number="form.price_total" type="number" label="Prezzo totale" outlined dense step="0.01" min="0" prefix="€" />
          </div>
          <div class="col-12 col-md-6">
            <q-input v-model.number="form.price_paid" type="number" label="Prezzo pagato" outlined dense step="0.01" min="0" prefix="€" />
          </div>

          <q-separator class="col-12" />

          <!-- Nome + Cognome -->
          <div class="col-12 col-md-6">
            <q-input v-model="form.first_name" label="Nome*" outlined dense :rules="[val => !!val || 'Nome obbligatorio']" />
          </div>
          <div class="col-12 col-md-6">
            <q-input v-model="form.last_name" label="Cognome*" outlined dense :rules="[val => !!val || 'Cognome obbligatorio']" />
          </div>

          <!-- Email + Telefono -->
          <div class="col-12 col-md-6">
            <q-input v-model="form.email" label="Email" outlined dense type="email" />
          </div>
          <div class="col-12 col-md-6">
            <q-input v-model="form.phone" label="Telefono" outlined dense />
          </div>

          <q-separator class="col-12" />

          <!-- Tipo pagamento + Data e ora del pagamento -->
          <div class="col-12 col-md-6">
            <q-select
              v-model="form.payment_type"
              :options="paymentTypeOptions"
              label="Tipo pagamento"
              outlined dense
              emit-value map-options
              clearable
            />
          </div>
          <div class="col-12 col-md-6">
            <q-input v-model="form.payment_datetime" label="Data e ora del pagamento" outlined dense type="datetime-local">
              <template v-slot:prepend>
                <q-icon name="event" />
              </template>
              <template v-slot:append>
                <q-icon name="schedule" />
              </template>
            </q-input>
          </div>

          <!-- Regalo + Codice buono -->
          <div class="col-12 col-md-6">
            <q-input v-model="form.gift_recipient" label="Regalo (nome e cognome)" outlined dense />
          </div>
          <div class="col-12 col-md-6">
            <q-input v-model="form.gift_code" label="Codice buono regalo" outlined dense />
          </div>

          <!-- Note + Lingua -->
          <div class="col-12 col-md-6">
            <q-input v-model="form.notes" label="Note" outlined dense type="textarea" rows="1" autogrow />
          </div>
          <div class="col-12 col-md-6">
            <q-select
              v-model="form.language"
              :options="languageOptions"
              label="Lingua"
              outlined dense
              emit-value map-options
            />
          </div>
        </q-form>
      </q-card-section>

      <q-separator />

      <q-card-actions align="right" class="q-pa-md bg-grey-1">
        <q-btn flat label="ANNULLA" v-close-popup class="q-mr-sm" />
        <q-btn color="primary" label="SALVA ORDINE" @click="save" :loading="saving" unelevated />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

const props = defineProps(['modelValue', 'defaults'])
const emit = defineEmits(['update:modelValue', 'saved'])
const $q = useQuasar()

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isEdit = ref(false)
const formRef = ref(null)
const saving = ref(false)
const loadingSlots = ref(false)
const slots = ref([])

const activityOptions = [
  { label: 'Family', value: 'FAMILY' },
  { label: 'Classica', value: 'CLASSICA' },
  { label: 'Advanced', value: 'ADVANCED' },
  { label: 'Selection', value: 'SELECTION' },
  { label: 'Hydro L1', value: 'HYDRO_L1' },
  { label: 'Hydro L2', value: 'HYDRO_L2' }
]

const orderStatusOptions = [
  { label: 'In Attesa', value: 'IN_ATTESA' },
  { label: 'Confermato', value: 'CONFERMATO' },
  { label: 'Cancellato', value: 'CANCELLATO' },
  { label: 'Completato', value: 'COMPLETATO' }
]

const paymentTypeOptions = [
  { label: 'Contanti', value: 'CONTANTI' },
  { label: 'Carta', value: 'CARTA' },
  { label: 'Bonifico', value: 'BONIFICO' },
  { label: 'Satispay', value: 'SATISPAY' },
  { label: 'Buono Regalo', value: 'BUONO_REGALO' },
  { label: 'Altro', value: 'ALTRO' }
]

const languageOptions = [
  { label: 'Italiano', value: 'it' },
  { label: 'English', value: 'en' },
  { label: 'Français', value: 'fr' }
]

function slotQColor(status) {
  if (status === 'A') return 'green'
  if (status === 'B') return 'amber'
  if (status === 'C') return 'red'
  if (status === 'D') return 'blue'
  return 'grey'
}

const timeOptions = computed(() => {
  const requestedPax = form.pax || 1
  return slots.value.map(s => {
    const cap = Math.min(s.cap_guides_pax, s.cap_rafts_pax)
    const remaining = cap - s.booked_pax
    const isFull = remaining < requestedPax || s.status === 'C'
    return {
      label: `${s.time} — ${s.status_desc} (${remaining} posti)`,
      value: s.time,
      timeLabel: s.time,
      desc: isFull ? `⚠️ Posti insufficienti per ${requestedPax} pax` : `${s.status_desc} — OK per ${requestedPax} pax`,
      remaining,
      isFull,
      qColor: slotQColor(s.status)
    }
  })
})

const defaultForm = () => ({
  date: new Date().toISOString().split('T')[0],
  time: null,
  activity_type: 'CLASSICA',
  pax: 1,
  order_status: 'IN_ATTESA',
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  price_total: 0,
  price_paid: 0,
  payment_type: null,
  payment_datetime: '',
  gift_recipient: '',
  gift_code: '',
  language: 'it',
  notes: ''
})

const form = reactive(defaultForm())

function resetForm() {
  Object.assign(form, defaultForm())
}

// When dialog opens, apply defaults and fetch slots
watch(() => props.modelValue, async (val) => {
  if (val) {
    resetForm()
    if (props.defaults) {
      if (props.defaults.date) form.date = props.defaults.date
      if (props.defaults.activity_type) form.activity_type = props.defaults.activity_type
      if (props.defaults.time) form.time = props.defaults.time
    }
    await fetchSlots()
  }
})

// When date or activity changes, reload available slots
watch(() => form.date, () => { if (isOpen.value) fetchSlots() })
watch(() => form.activity_type, () => { if (isOpen.value) fetchSlots() })

async function fetchSlots() {
  if (!form.date) return
  loadingSlots.value = true
  try {
    const res = await api.get('/resources/daily-schedule', { params: { date: form.date } })
    slots.value = res.data.filter(s => s.activity_type === form.activity_type)
  } catch (e) {
    console.error('Error fetching slots:', e)
  } finally {
    loadingSlots.value = false
  }
}

async function save() {
  const valid = await formRef.value?.validate()
  if (!valid) return

  if (!form.time) {
    $q.notify({ type: 'warning', message: 'Seleziona un orario' })
    return
  }

  saving.value = true
  try {
    // Compose customer_name for backward compat
    const payload = {
      ...form,
      customer_name: `${form.first_name} ${form.last_name}`.trim(),
      contact_info: form.email || form.phone || ''
    }
    await api.post('/reservations/', payload)
    $q.notify({ type: 'positive', message: 'Prenotazione salvata con successo' })
    emit('saved')
    isOpen.value = false
    resetForm()
  } catch (e) {
    console.error(e)
    $q.notify({ type: 'negative', message: 'Errore durante il salvataggio' })
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.q-separator.col-12 {
  margin-top: 4px;
  margin-bottom: 4px;
}
</style>
