<template>
  <q-dialog v-model="isOpen" persistent>
    <q-card style="min-width: 520px; max-width: 650px;" class="yield-simulator">
      <!-- Header -->
      <q-card-section class="bg-deep-purple text-white row items-center">
        <q-icon name="calculate" size="md" class="q-mr-sm" />
        <div class="text-h6">Simulatore E-commerce 🧮</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <!-- Input -->
      <q-card-section class="q-gutter-md q-pt-lg">
        <div class="text-subtitle2 text-grey-7 q-mb-sm">Seleziona lo slot da analizzare:</div>
        <div class="row q-col-gutter-md">
          <div class="col-7">
            <q-input
              v-model="selectedDate"
              type="date"
              label="Data"
              outlined
              dense
              bg-color="white"
            >
              <template #prepend><q-icon name="event" color="deep-purple" /></template>
            </q-input>
          </div>
          <div class="col-5">
            <q-input
              v-model="selectedTime"
              type="time"
              label="Orario"
              outlined
              dense
              bg-color="white"
            >
              <template #prepend><q-icon name="schedule" color="deep-purple" /></template>
            </q-input>
          </div>
        </div>

        <q-btn
          class="full-width q-mt-md"
          color="deep-purple"
          icon="rocket_launch"
          label="CALCOLA POSTI VENDIBILI"
          unelevated
          size="lg"
          :loading="isCalculating"
          @click="calculate"
        />
      </q-card-section>

      <q-separator v-if="result" />

      <!-- Risultati -->
      <q-card-section v-if="result" class="text-center q-py-lg">
        <!-- PAX grande -->
        <div
          class="text-h2 text-weight-bold q-mb-xs"
          :class="result.available_pax > 0 ? 'text-positive' : 'text-negative'"
        >
          {{ result.available_pax }}
        </div>
        <div class="text-subtitle1 text-grey-6 q-mb-md">PAX Vendibili</div>

        <!-- Bottleneck -->
        <q-badge
          :color="result.available_pax > 0 ? 'amber-8' : 'negative'"
          text-color="white"
          class="text-subtitle2 q-pa-sm"
          :label="'⚠ ' + result.bottleneck"
        />

        <!-- Riepilogo Quick Stats -->
        <div class="row q-gutter-sm justify-center q-mt-lg">
          <q-chip icon="person" color="teal" text-color="white" dense>
            {{ debugInfo.free_guides?.length || 0 }} Guide
          </q-chip>
          <q-chip icon="sailing" color="blue" text-color="white" dense>
            {{ debugInfo.free_rafts?.length || 0 }} Gommoni
          </q-chip>
          <q-chip icon="local_shipping" color="orange" text-color="white" dense>
            {{ debugInfo.free_vans_hitch?.length || 0 }} Furgoni Gancio
          </q-chip>
          <q-chip icon="badge" color="deep-orange" text-color="white" dense>
            {{ debugInfo.free_drivers_c?.length || 0 }} Autisti Pat.C
          </q-chip>
          <q-chip icon="rv_hookup" color="brown" text-color="white" dense>
            {{ debugInfo.free_trailers?.length || 0 }} Carrelli
          </q-chip>
        </div>

        <!-- Pipeline visiva -->
        <div class="row items-center justify-center q-gutter-sm q-mt-lg text-body2">
          <div class="pipeline-box bg-teal-1 text-teal-9">
            <div class="text-weight-bold text-h6">{{ debugInfo.phase_a_rafts_to_deploy ?? '-' }}</div>
            <div class="text-caption">Gommoni in acqua</div>
          </div>
          <q-icon name="arrow_forward" color="grey-5" size="sm" />
          <div class="pipeline-box bg-orange-1 text-orange-9">
            <div class="text-weight-bold text-h6">{{ debugInfo.phase_b_transport_capacity ?? '-' }}</div>
            <div class="text-caption">Cap. trasporto</div>
          </div>
          <q-icon name="arrow_forward" color="grey-5" size="sm" />
          <div class="pipeline-box bg-deep-purple-1 text-deep-purple-9">
            <div class="text-weight-bold text-h6">{{ debugInfo.phase_c_actual_rafts ?? '-' }}</div>
            <div class="text-caption">Gommoni reali</div>
          </div>
          <q-icon name="arrow_forward" color="grey-5" size="sm" />
          <div class="pipeline-box bg-green-1 text-green-9">
            <div class="text-weight-bold text-h6">{{ debugInfo.phase_d_available_pax ?? '-' }}</div>
            <div class="text-caption">PAX finali</div>
          </div>
        </div>

        <q-separator class="q-my-md" />

        <!-- Dettagli espandibili -->
        <q-expansion-item
          icon="analytics"
          label="Dettagli Logistici (Debug)"
          header-class="text-grey-7 text-subtitle2"
          dense
        >
          <div class="q-pa-md text-left">
            <!-- Risorse occupate -->
            <div class="text-caption text-weight-bold text-grey-8 q-mb-xs">🔒 Risorse occupate nello slot:</div>
            <div v-if="debugInfo.busy_resources?.length" class="q-mb-md">
              <q-chip v-for="name in debugInfo.busy_resources" :key="name" dense size="sm" color="red-2" text-color="red-9" icon="lock">{{ name }}</q-chip>
            </div>
            <div v-else class="text-caption text-grey-5 q-mb-md">Nessuna risorsa occupata</div>

            <!-- Guide libere -->
            <div class="text-caption text-weight-bold text-grey-8 q-mb-xs">🟢 Guide libere:</div>
            <div class="q-mb-md">
              <q-chip v-for="name in debugInfo.free_guides" :key="name" dense size="sm" color="teal-2" text-color="teal-9">{{ name }}</q-chip>
              <span v-if="!debugInfo.free_guides?.length" class="text-caption text-grey-5">Nessuna</span>
            </div>

            <!-- Autisti Pat.C -->
            <div class="text-caption text-weight-bold text-grey-8 q-mb-xs">🟠 Autisti Patente Carrello:</div>
            <div class="q-mb-md">
              <q-chip v-for="name in debugInfo.free_drivers_c" :key="name" dense size="sm" color="orange-2" text-color="orange-9">{{ name }}</q-chip>
              <span v-if="!debugInfo.free_drivers_c?.length" class="text-caption text-grey-5">Nessuno</span>
            </div>

            <!-- Gommoni liberi -->
            <div class="text-caption text-weight-bold text-grey-8 q-mb-xs">🛶 Gommoni liberi:</div>
            <div class="q-mb-md">
              <q-chip v-for="r in debugInfo.free_rafts" :key="r.name" dense size="sm" color="blue-2" text-color="blue-9">{{ r.name }} ({{ r.capacity }}pax)</q-chip>
              <span v-if="!debugInfo.free_rafts?.length" class="text-caption text-grey-5">Nessuno</span>
            </div>

            <!-- Selezionati -->
            <div class="text-caption text-weight-bold text-grey-8 q-mb-xs">✅ Gommoni selezionati per il calcolo:</div>
            <div class="q-mb-md">
              <q-chip v-for="name in debugInfo.selected_rafts" :key="name" dense size="sm" color="green-2" text-color="green-9" icon="check_circle">{{ name }}</q-chip>
              <span v-if="!debugInfo.selected_rafts?.length" class="text-caption text-grey-5">Nessuno</span>
            </div>

            <!-- Furgoni e carrelli -->
            <div class="text-caption text-weight-bold text-grey-8 q-mb-xs">🚐 Furgoni gancio / 🚛 Carrelli:</div>
            <div class="q-mb-md">
              <q-chip v-for="name in debugInfo.free_vans_hitch" :key="name" dense size="sm" color="amber-2" text-color="amber-9" icon="local_shipping">{{ name }}</q-chip>
              <q-chip v-for="t in debugInfo.free_trailers" :key="t.name" dense size="sm" color="brown-2" text-color="brown-9" icon="rv_hookup">{{ t.name }} (max {{ t.max_rafts }})</q-chip>
            </div>

            <!-- Convogli -->
            <div class="text-caption text-weight-bold text-grey-8 q-mb-xs">🚚 Convogli formabili:</div>
            <div class="text-body2 text-grey-7">
              {{ debugInfo.phase_b_max_convoys ?? 0 }} convogli →
              capacità trasporto {{ debugInfo.phase_b_transport_capacity ?? 0 }} gommoni
            </div>
          </div>
        </q-expansion-item>
      </q-card-section>

      <!-- Error state -->
      <q-card-section v-if="errorMsg" class="text-center">
        <q-banner rounded class="bg-red-1 text-negative">
          <template #avatar><q-icon name="error" color="negative" /></template>
          {{ errorMsg }}
        </q-banner>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'

const props = defineProps({
  modelValue: Boolean,
  initialDate: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const $q = useQuasar()

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

// State
const selectedDate = ref('')
const selectedTime = ref('09:00')
const isCalculating = ref(false)
const result = ref(null)
const errorMsg = ref('')

const debugInfo = computed(() => result.value?.debug_info || {})

// Pre-fill date when dialog opens
watch(isOpen, (open) => {
  if (open) {
    if (props.initialDate) {
      // Formato YYYY/MM/DD o YYYY-MM-DD → normalizza
      selectedDate.value = props.initialDate.replace(/\//g, '-')
    } else {
      const today = new Date()
      selectedDate.value = today.toISOString().slice(0, 10)
    }
    result.value = null
    errorMsg.value = ''
  }
})

async function calculate() {
  if (!selectedDate.value || !selectedTime.value) {
    $q.notify({ type: 'warning', message: 'Seleziona data e orario' })
    return
  }

  isCalculating.value = true
  result.value = null
  errorMsg.value = ''

  try {
    const res = await api.post('/availability/calculate', {
      date: selectedDate.value,
      time: selectedTime.value,
    })
    result.value = res.data
  } catch (err) {
    console.error('[YieldSimulator] API error:', err)
    errorMsg.value = err?.response?.data?.detail || err.message || 'Errore di comunicazione con il server'
    $q.notify({ type: 'negative', message: 'Errore calcolo disponibilità' })
  } finally {
    isCalculating.value = false
  }
}
</script>

<style scoped>
.yield-simulator {
  border-radius: 16px;
}
.pipeline-box {
  border-radius: 12px;
  padding: 12px 16px;
  min-width: 90px;
  text-align: center;
}
</style>
