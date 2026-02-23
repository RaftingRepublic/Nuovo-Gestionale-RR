<template>
  <q-dialog v-model="isOpen">
    <q-card style="width: 600px; max-width: 95vw;">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6"><q-icon name="group" class="q-mr-sm" />Lista Partecipanti — {{ localOrder?.customer_name || 'Gruppo' }}</div>
        <q-space />
        <q-badge color="green" class="q-mr-sm q-pa-sm">{{ participants.filter(p => p.selected).length }} / {{ participants.length }}</q-badge>
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section class="q-pt-md" style="max-height: 60vh; overflow-y: auto;">
        <q-list separator>
          <q-item v-for="pax in participants" :key="pax.id" tag="label" v-ripple>
            <q-item-section side v-if="firaftRequired">
              <q-checkbox v-model="pax.selected" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ pax.name }}</q-item-label>
              <q-item-label caption>{{ pax.email || '—' }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <div class="row items-center q-gutter-sm">
                <q-icon name="thumb_up" size="sm" :color="pax.privacy ? 'green' : 'grey-4'" />
                <q-icon v-if="firaftRequired" name="security" size="sm" :color="pax.status === 'success' ? 'green' : (pax.status === 'error' ? 'red' : 'grey-4')" />
              </div>
            </q-item-section>
          </q-item>
        </q-list>
      </q-card-section>

      <q-card-actions align="center" class="bg-grey-1 q-pa-md">
        <q-btn v-if="firaftRequired" color="primary" label="TESSERA SELEZIONATI" :loading="loading" @click="processFiraft" />
        <q-btn flat label="ESCI" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useQuasar } from 'quasar'
import { useResourceStore } from 'stores/resource-store'
import { supabase } from 'src/supabase'

const props = defineProps({
  modelValue: Boolean,
  order: Object,      // L'ordine bersaglio
  rideContext: Object  // Il ride corrente (per isFiraftRequired)
})
const emit = defineEmits(['update:modelValue', 'registered'])

const $q = useQuasar()
const store = useResourceStore()
const loading = ref(false)
const participants = ref([])
const localOrder = ref(null)

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// Business Rule: Anatre vs Grape
const firaftRequired = computed(() => {
  const ride = props.rideContext
  if (!ride) return false
  const manager = String(ride.manager || ride.gestore || '').toLowerCase()
  if (manager.includes('anatre')) return true
  if (manager.includes('grape')) return false
  const name = String(ride.activity_name || ride.activity_type || ride.title || '').toLowerCase()
  if (name.includes('family') || name.includes('anatre')) return true
  return false
})

// Pre-popola i partecipanti quando il dialog si apre
watch(isOpen, async (val) => {
  if (!val || !props.order) return
  localOrder.value = props.order
  participants.value = []

  const order = props.order
  const paxCount = order._actual_pax !== undefined && order._actual_pax !== null
    ? order._actual_pax
    : (order.total_pax || order.pax || 1)

  // Carica partecipanti reali dal DB
  let dbPax = []
  if (order.id && typeof order.id === 'string' && order.id.length > 10) {
    dbPax = await store.fetchParticipantsForOrder(order.id)
  }

  // Mappa i partecipanti dal DB
  for (const p of dbPax) {
    participants.value.push({
      id: p.id,
      name: p.name || '',
      email: p.email || '',
      selected: p.firaft_status !== 'success',
      privacy: p.is_privacy_signed || false,
      status: p.firaft_status || 'pending',
    })
  }

  // Riempi i vuoti fino a paxCount con placeholder
  const remaining = paxCount - dbPax.length
  for (let i = 0; i < remaining; i++) {
    const idx = dbPax.length + i
    participants.value.push({
      id: 'temp-' + idx,
      name: idx === 0
        ? (order.customer_name || order.referent?.name || 'Referente Gruppo')
        : `Ospite ${idx + 1} (${order.customer_name || 'Gruppo'})`,
      email: idx === 0 ? (order.customer_email || order.referent?.email || '') : '',
      selected: true,
      privacy: false,
      status: 'pending',
    })
  }
})

async function processFiraft() {
  loading.value = true
  const selected = participants.value.filter(p => p.selected && p.status !== 'success')
  if (selected.length === 0) {
    loading.value = false
    $q.notify({ type: 'info', message: 'Nessun partecipante da tessere.' })
    return
  }

  try {
    for (const pax of selected) {
      const payload = {
        order_id: localOrder.value.id,
        name: pax.name || 'Ospite',
        email: pax.email || null,
        is_privacy_signed: pax.privacy || false,
        firaft_status: 'success',
      }

      if (pax.id && !String(pax.id).startsWith('temp')) {
        payload.id = pax.id
      }

      const { data, error } = await supabase
        .from('participants')
        .upsert(payload)
        .select()
        .single()

      if (error) {
        console.error('[FiraftDialog] Supabase upsert error:', error)
        pax.status = 'error'
      } else {
        pax.id = data.id
        pax.status = 'success'
        pax.selected = false
      }
    }

    $q.notify({ type: 'positive', message: `Tesseramenti registrati nel Cloud! (${selected.filter(p => p.status === 'success').length}/${selected.length})`, position: 'top' })
    emit('registered')
  } catch (err) {
    console.error('[FiraftDialog] processFiraft error:', err)
    $q.notify({ type: 'negative', message: 'Errore tesseramento: ' + err.message })
  } finally {
    loading.value = false
  }
}
</script>
