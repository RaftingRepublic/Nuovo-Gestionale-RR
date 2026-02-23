<template>
  <q-dialog v-model="isOpen" position="right" maximized>
    <q-card style="width: 400px; max-width: 90vw; display: flex; flex-direction: column;" v-if="localSlot">
      <q-card-section class="bg-blue-grey-8 text-white row items-center q-pb-none">
        <div class="text-h6"><q-icon name="handyman" class="q-mr-sm" /> Assegna Risorse</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section class="bg-blue-grey-8 text-white q-pt-xs">
        <div class="text-subtitle2">{{ localSlot.time ? String(localSlot.time).substring(0,5) : '' }} — {{ localSlot.activity_type || localSlot.activity_name || '' }}</div>
        <div class="text-caption">Pax: {{ localSlot.booked_pax || 0 }} / {{ localSlot.total_capacity || 16 }}</div>
      </q-card-section>

      <q-card-section class="q-pt-md scroll" style="flex-grow: 1;">
        <div class="text-subtitle2 text-primary q-mb-sm"><q-icon name="rowing" /> Guide e Istruttori</div>
        <q-select
          v-model="localSlot.assigned_guides"
          multiple
          use-chips
          outlined
          dense
          :options="guideOptionsDB"
          option-label="name"
          option-value="id"
          label="Seleziona Guide"
        />

        <div class="text-subtitle2 text-light-blue-8 q-mt-lg q-mb-sm"><q-icon name="rowing" /> Flotta Acquatica (Gommoni)</div>
        <q-select
          v-model="localSlot.assigned_boats"
          multiple
          use-chips
          outlined
          dense
          :options="boatOptionsDB"
          option-label="name"
          option-value="id"
          label="Seleziona Gommoni"
        />

        <div class="text-subtitle2 text-orange-9 q-mt-lg q-mb-sm"><q-icon name="directions_bus" /> Furgoni e Navette</div>
        <q-select
          v-model="localSlot.assigned_vans"
          multiple
          use-chips
          outlined
          dense
          :options="vanOptionsDB"
          option-label="name"
          option-value="id"
          label="Seleziona Furgoni"
        />

        <div class="text-subtitle2 text-brown-8 q-mt-lg q-mb-sm"><q-icon name="rv_hookup" /> Carrelli Rimorchio</div>
        <q-select
          v-model="localSlot.assigned_trailers"
          multiple
          use-chips
          outlined
          dense
          :options="trailerOptionsDB"
          option-label="name"
          option-value="id"
          label="Seleziona Carrelli"
        />

        <div class="q-mt-xl text-caption text-grey-6">
          Le risorse assegnate vengono salvate nella tabella ride_allocations su Supabase.
        </div>
      </q-card-section>

      <q-card-actions align="right" class="bg-white">
        <q-btn flat label="CHIUDI" color="blue-grey" v-close-popup />
        <q-btn unelevated label="SALVA RISORSE" color="primary" icon="cloud_upload" @click="saveAllocations" :loading="saving" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useQuasar } from 'quasar'
import { useResourceStore } from 'stores/resource-store'

const props = defineProps({
  modelValue: Boolean,
  ride: Object
})
const emit = defineEmits(['update:modelValue', 'saved'])

const $q = useQuasar()
const store = useResourceStore()
const saving = ref(false)

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// Slot locale reattivo — clone del ride passato dal padre
const localSlot = reactive({
  id: null,
  time: '',
  date: '',
  activity_id: null,
  activity_type: '',
  activity_name: '',
  booked_pax: 0,
  total_capacity: 16,
  assigned_guides: [],
  assigned_boats: [],
  assigned_vans: [],
  assigned_trailers: [],
})

// Opzioni risorse filtrate dallo store
const guideOptionsDB = computed(() => store.resources.filter(r => r.type === 'guide'))
const boatOptionsDB = computed(() => store.resources.filter(r => r.type === 'raft'))
const vanOptionsDB = computed(() => store.resources.filter(r => r.type === 'van'))
const trailerOptionsDB = computed(() => store.resources.filter(r => r.type === 'trailer'))

// Pre-popola quando il dialog si apre
watch(isOpen, (val) => {
  if (val && props.ride) {
    localSlot.id = props.ride.id
    localSlot.time = props.ride.time || ''
    localSlot.date = props.ride.date || ''
    localSlot.activity_id = props.ride.activity_id || null
    localSlot.activity_type = props.ride.activity_type || ''
    localSlot.activity_name = props.ride.activity_name || ''
    localSlot.booked_pax = props.ride.booked_pax || 0
    localSlot.total_capacity = props.ride.total_capacity || 16
    localSlot.assigned_guides = props.ride.guides || []
    localSlot.assigned_boats = props.ride.rafts || []
    localSlot.assigned_vans = props.ride.vans || []
    localSlot.assigned_trailers = props.ride.trailers || []
  }
})

async function saveAllocations() {
  if (!localSlot.id) return
  saving.value = true
  try {
    const extractIds = (arr) => (arr || []).map(item => typeof item === 'string' ? item : item?.id).filter(Boolean)
    const allIds = [
      ...extractIds(localSlot.assigned_guides),
      ...extractIds(localSlot.assigned_boats),
      ...extractIds(localSlot.assigned_vans),
      ...extractIds(localSlot.assigned_trailers),
    ]

    await store.saveRideAllocations({
      id: localSlot.id,
      date: localSlot.date,
      time: localSlot.time,
      activity_id: localSlot.activity_id,
    }, allIds)

    isOpen.value = false
    $q.notify({ type: 'positive', message: 'Logistica aggiornata nel cloud! ☁️', position: 'top' })
    emit('saved')
  } catch (err) {
    console.error('[ResourcePanel] Save allocations error:', err)
    $q.notify({ type: 'negative', message: 'Errore salvataggio risorse: ' + err.message })
  } finally {
    saving.value = false
  }
}
</script>
