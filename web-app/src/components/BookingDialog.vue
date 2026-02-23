<template>
  <q-dialog v-model="isOpen">
    <q-card style="width: 900px; max-width: 90vw;">
      <q-card-section class="bg-primary text-white row items-center justify-between q-py-sm">
        <div class="text-h6"><q-icon :name="isEdit ? 'edit' : 'add_circle'" class="q-mr-sm" />{{ isEdit ? 'Modifica Prenotazione' : 'Nuova Prenotazione' }}</div>
        <q-btn flat round dense icon="close" v-close-popup />
      </q-card-section>
      <q-separator />
      <q-card-section class="scroll" style="max-height: 70vh;">
        <div class="q-gutter-md">
          <!-- Riga 1: Stato, Pax, Attività -->
          <div class="row q-col-gutter-md">
            <div class="col-12 col-sm-4">
              <q-select v-model="form.order_status" :options="orderStatusOptions" label="Stato Ordine" dense outlined emit-value map-options />
            </div>
            <div class="col-12 col-sm-4">
              <q-input v-model.number="form.total_pax" type="number" label="N° Partecipanti" dense outlined />
            </div>
            <div class="col-12 col-sm-4">
              <q-select v-model="form.activity" :options="store.activities" option-label="name" option-value="id" emit-value map-options label="Tipo Attività" dense outlined />
            </div>
          </div>
          <!-- Riga 2: Data, Ora -->
          <div class="row q-col-gutter-md">
            <div class="col-12 col-sm-4">
              <q-input v-model="form.date" type="date" label="Data" dense outlined />
            </div>
            <div class="col-12 col-sm-4">
              <q-select
                v-model="form.time"
                :options="timeOptions"
                label="Ora"
                dense outlined
                use-input
                new-value-mode="add-unique"
                fill-input
                hide-selected
                @filter="(val, update) => update()"
              />
            </div>
            <div class="col-12 col-sm-4">
              <q-select v-model="form.language" :options="['IT', 'EN', 'DE', 'FR']" label="Lingua" dense outlined />
            </div>
          </div>
          <!-- Riga 3: Prezzi -->
          <div class="row q-col-gutter-md">
            <div class="col-12 col-sm-4">
              <q-input v-model.number="form.price_total" type="number" label="Prezzo Totale (€)" prefix="€" dense outlined />
            </div>
            <div class="col-12 col-sm-4">
              <q-input v-model.number="form.paid_amount" type="number" label="Prezzo Pagato (€)" prefix="€" dense outlined />
            </div>
            <div class="col-12 col-sm-4">
              <q-select v-model="form.payment_type" :options="['CASH', 'SUMUP', 'BONIFICO', 'STRIPE', 'ALTRO']" label="Tipo Pagamento" dense outlined />
            </div>
          </div>
          <q-separator />
          <!-- Riga 4: Anagrafica referente -->
          <div class="text-subtitle2 text-blue-grey-8"><q-icon name="person" class="q-mr-xs" />Dati Referente</div>
          <div class="row q-col-gutter-md">
            <div class="col-12 col-sm-3"><q-input v-model="form.customer_name" label="Nome" dense outlined /></div>
            <div class="col-12 col-sm-3"><q-input v-model="form.customer_surname" label="Cognome" dense outlined /></div>
            <div class="col-12 col-sm-3"><q-input v-model="form.customer_email" label="Email" dense outlined /></div>
            <div class="col-12 col-sm-3"><q-input v-model="form.customer_phone" label="Telefono" dense outlined /></div>
          </div>
          <q-separator />
          <!-- Riga 5: Extra -->
          <div class="row q-col-gutter-md">
            <div class="col-12 col-sm-3">
              <q-input v-model="form.payment_date" type="date" label="Data Pagamento" dense outlined />
            </div>
            <div class="col-12 col-sm-3">
              <q-toggle v-model="form.is_gift" label="Regalo" dense />
            </div>
            <div class="col-12 col-sm-3">
              <q-input v-model="form.coupon_code" label="Codice Sconto" dense outlined />
            </div>
            <div class="col-12 col-sm-3">
              <q-toggle v-model="form.is_exclusive_raft" label="Gommone Esclusivo" dense />
            </div>
          </div>
          <q-input v-model="form.notes" label="Note" type="textarea" dense outlined autogrow />
        </div>
      </q-card-section>
      <q-separator />
      <q-card-actions align="right" class="bg-grey-1 q-pa-md">
        <q-btn flat label="Annulla" v-close-popup />
        <q-btn unelevated color="primary" icon="save" :label="isEdit ? 'Salva Modifiche' : 'Crea Ordine'" @click="save" :loading="saving" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useQuasar } from 'quasar'
import { useResourceStore } from 'stores/resource-store'
import { supabase } from 'src/supabase'

const props = defineProps({
  modelValue: Boolean,
  rideContext: Object,  // Dati del turno corrente (per nuova prenotazione)
  editOrder: Object,    // Dati dell'ordine (per modifica)
  selectedDate: String  // Data selezionata nel calendario padre (fallback)
})
const emit = defineEmits(['update:modelValue', 'saved'])

const $q = useQuasar()
const store = useResourceStore()
const saving = ref(false)

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isEdit = ref(false)
const originalRef = ref(null)

const orderStatusOptions = [
  { label: 'Confermato', value: 'CONFERMATO' },
  { label: 'In Attesa (Fantasma)', value: 'IN_ATTESA' },
  { label: 'Da Saldare', value: 'DA_SALDARE' },
  { label: 'Manuale', value: 'MANUALE' },
  { label: 'Completato', value: 'COMPLETATO' },
  { label: 'Cancellato', value: 'CANCELLATO' },
]

const timeOptions = ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00']

const defaultForm = () => ({
  order_status: 'CONFERMATO',
  total_pax: 1,
  activity: '',
  date: '',
  time: '09:00',
  language: 'IT',
  price_total: 0,
  paid_amount: 0,
  payment_type: 'CASH',
  customer_name: '',
  customer_surname: '',
  customer_email: '',
  customer_phone: '',
  payment_date: '',
  is_gift: false,
  coupon_code: '',
  is_exclusive_raft: false,
  notes: '',
})

const form = reactive(defaultForm())

// Pre-compila il form quando il dialog si apre
watch(isOpen, (val) => {
  if (!val) return
  Object.assign(form, defaultForm())

  if (props.editOrder) {
    // ── MODALITÀ EDIT ──
    isEdit.value = true
    originalRef.value = props.editOrder
    const o = props.editOrder
    form.order_status = o.order_status || 'CONFERMATO'
    form.total_pax = o.total_pax || o.pax || 1
    form.activity = o.activity_id || ''
    // Data dal rideContext (il ride in cui l'ordine è inserito)
    const editDate = props.rideContext?.ride_date || ''
    form.date = editDate ? String(editDate).replace(/\//g, '-') : ''
    const editTime = props.rideContext?.ride_time || ''
    form.time = editTime ? String(editTime).substring(0, 5) : ''
    form.language = o.language || 'IT'
    form.price_total = o.price_total || 0
    form.paid_amount = o.paid_amount || 0
    form.payment_type = o.payment_type || 'CASH'
    form.customer_name = o.customer_name || ''
    form.customer_surname = o.customer_surname || ''
    form.customer_email = o.customer_email || ''
    form.customer_phone = o.customer_phone || ''
    form.payment_date = o.payment_date || ''
    form.is_gift = o.is_gift || false
    form.coupon_code = o.coupon_code || ''
    form.is_exclusive_raft = o.is_exclusive_raft || false
    form.notes = o.notes || ''
  } else {
    // ── NUOVO ORDINE ──
    isEdit.value = false
    originalRef.value = null

    if (props.rideContext) {
      const ctx = props.rideContext
      const rDate = ctx.ride_date || ctx.date || ''
      form.date = rDate ? String(rDate).replace(/\//g, '-') : ''
      const rTime = ctx.ride_time || ctx.time || ctx.start_time || ''
      form.time = rTime ? String(rTime).substring(0, 5) : ''
      const ctxActId = ctx.activity_id || ''
      if (ctxActId) {
        form.activity = ctxActId
      } else {
        const actName = ctx.activity_name || ctx.activity_type || ctx.name || ctx.title || ''
        const matched = store.activities.find(a => a.name.toLowerCase() === actName.toLowerCase())
        form.activity = matched ? matched.id : ''
      }
    } else {
      const fallbackDate = props.selectedDate || ''
      form.date = fallbackDate ? String(fallbackDate).replace(/\//g, '-') : ''
    }
  }
})

async function save() {
  saving.value = true
  try {
    if (isEdit.value && originalRef.value) {
      // ── EDIT: aggiorna ordine su Supabase ──
      const o = originalRef.value
      if (o.id && typeof o.id === 'string' && o.id.length > 10) {
        const { error } = await supabase.from('orders').update({
          customer_name: form.customer_name || o.customer_name,
          customer_email: form.customer_email || '',
          customer_phone: form.customer_phone || '',
          pax: form.total_pax || 1,
          total_price: form.price_total || 0,
          status: form.order_status || 'CONFERMATO',
          notes: form.notes || '',
        }).eq('id', o.id)
        if (error) throw error
      }
      // Aggiorna anche localmente per reattività immediata
      o.order_status = form.order_status
      o.total_pax = form.total_pax
      o.price_total = form.price_total
      o.paid_amount = form.paid_amount
      o.customer_name = form.customer_name
      o.customer_surname = form.customer_surname
      o.customer_email = form.customer_email
      o.customer_phone = form.customer_phone
      o.is_exclusive_raft = form.is_exclusive_raft
      o.notes = form.notes
      $q.notify({ type: 'positive', message: 'Ordine aggiornato ✅' })
    } else {
      // ── CREAZIONE: salva su Supabase ──
      const activityId = form.activity || ''
      const dateStr = (form.date || props.selectedDate || '').replace(/\//g, '-')
      const timeStr = (String(form.time || '09:00').substring(0, 5)) + ':00'

      await store.saveOrder({
        activityId,
        dateStr,
        timeStr,
        customerName: form.customer_name || 'Nuovo Cliente',
        customerEmail: form.customer_email || '',
        customerPhone: form.customer_phone || '',
        pax: form.total_pax || 1,
        totalPrice: form.price_total || 0,
        status: form.order_status || 'CONFERMATO',
        notes: form.notes || '',
      })

      const realActivity = store.activities.find(a => a.id === activityId) || { name: activityId }
      $q.notify({ type: 'positive', message: `✅ Prenotazione ${realActivity.name} salvata nel Cloud!`, position: 'top' })
    }

    isOpen.value = false
    emit('saved')
  } catch (err) {
    console.error('[BookingDialog] Save error:', err)
    $q.notify({ type: 'negative', message: 'Errore: ' + err.message, position: 'top' })
  } finally {
    saving.value = false
  }
}
</script>
