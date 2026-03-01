<template>
  <!-- ═══════════════════════════════════════════════════════ -->
  <!-- CREW BUILDER PANEL — Banchina d'Imbarco Digitale       -->
  <!-- Fase 7.C.2 — Dogma Tetris Umano (Nominale)            -->
  <!-- ═══════════════════════════════════════════════════════ -->
  <div class="row q-col-gutter-md">

    <!-- ╔══════════════════════════════════════════╗ -->
    <!-- ║  ZONA BANCHINA — Riepilogo Passeggeri   ║ -->
    <!-- ╚══════════════════════════════════════════╝ -->
    <div class="col-12 col-md-4">
      <q-card flat bordered class="full-height">
        <q-card-section class="bg-blue-grey-1 q-pb-sm">
          <div class="row items-center q-gutter-sm">
            <q-icon name="groups" color="blue-grey-7" size="22px" />
            <div class="text-subtitle1 text-weight-bold text-blue-grey-9">
              Banchina d'Imbarco
            </div>
          </div>
        </q-card-section>

        <q-separator />

        <!-- ═══ FASE 7.E — BILANCIA BANCHINA (Banner a 3 stati) ═══ -->
        <q-banner
          v-if="assignedPax > totalPaxToBoard"
          rounded dense
          class="bg-red-2 text-red-10 q-mx-md q-mt-md"
          style="border: 2px solid #c62828;"
        >
          <template #avatar><q-icon name="error" color="red-10" size="28px" /></template>
          <div class="text-weight-bold" style="font-size: 14px;">
            🚨 ERRORE CRITICO: Stai imbarcando fantasmi che non hanno pagato! (Sovra-assegnazione)
          </div>
          <div class="text-caption">
            Imbarcati {{ assignedPax }} su {{ totalPaxToBoard }} paganti — {{ assignedPax - totalPaxToBoard }} fantasmi a bordo.
          </div>
        </q-banner>
        <q-banner
          v-else-if="assignedPax < totalPaxToBoard"
          rounded dense
          class="bg-orange-1 text-orange-10 q-mx-md q-mt-md"
          style="border: 2px solid #e65100;"
        >
          <template #avatar><q-icon name="warning" color="orange-9" size="28px" /></template>
          <div class="text-weight-bold" style="font-size: 14px;">
            ⚠️ ATTENZIONE: Hai passeggeri paganti ancora sulla ghiaia.
          </div>
          <div class="text-caption">
            Imbarcati {{ assignedPax }} su {{ totalPaxToBoard }} paganti — {{ totalPaxToBoard - assignedPax }} in attesa sul molo.
          </div>
        </q-banner>
        <q-banner
          v-else-if="totalPaxToBoard > 0"
          rounded dense
          class="bg-green-1 text-green-10 q-mx-md q-mt-md"
          style="border: 2px solid #2e7d32;"
        >
          <template #avatar><q-icon name="check_circle" color="green-8" size="28px" /></template>
          <div class="text-weight-bold" style="font-size: 14px;">
            ✅ Bilancio perfetto. Tutti a bordo.
          </div>
          <div class="text-caption">
            {{ assignedPax }} passeggeri imbarcati su {{ assignedPax }} paganti.
          </div>
        </q-banner>

        <q-card-section class="q-pa-md">
          <!-- Contatore Da Imbarcare -->
          <div class="row items-center justify-between q-mb-sm">
            <div class="text-body2 text-grey-7">Passeggeri paganti</div>
            <q-badge color="primary" class="text-body2 q-pa-sm">
              {{ totalPaxToBoard }}
            </q-badge>
          </div>

          <!-- Contatore Imbarcati -->
          <div class="row items-center justify-between q-mb-sm">
            <div class="text-body2 text-grey-7">Già imbarcati</div>
            <q-badge :color="assignedPax > totalPaxToBoard ? 'red' : 'green'" class="text-body2 q-pa-sm">
              {{ assignedPax }}
            </q-badge>
          </div>

          <!-- Contatore Non Assegnati -->
          <div class="row items-center justify-between q-mb-md">
            <div class="text-body2 text-grey-7">In attesa sul molo</div>
            <q-badge :color="remainingOnDock > 0 ? 'orange' : 'grey'" class="text-body2 q-pa-sm">
              {{ remainingOnDock }}
            </q-badge>
          </div>

          <q-separator class="q-mb-md" />

          <!-- Lista Ordini con pax residui (Tetris Umano) -->
          <div class="text-caption text-weight-bold text-grey-8 q-mb-xs">Manifesto d'Imbarco</div>
          <div v-if="!rideOrders || rideOrders.length === 0" class="text-center text-grey-5 q-pa-md">
            <q-icon name="event_seat" size="36px" class="q-mb-xs" />
            <div class="text-caption">Nessun passeggero</div>
          </div>
          <q-list separator dense v-else>
            <q-item
              v-for="order in rideOrders"
              :key="order.id"
              dense
              class="q-px-xs"
              :style="getRemainingPax(order) === 0 ? 'opacity: 0.45;' : ''"
            >
              <q-item-section avatar>
                <q-avatar
                  size="30px"
                  :color="getRemainingPax(order) === 0 ? 'green-2' : 'primary'"
                  :text-color="getRemainingPax(order) === 0 ? 'green-9' : 'white'"
                  :icon="getRemainingPax(order) === 0 ? 'check' : 'person'"
                />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-medium text-body2">
                  {{ order.customer_name || order.booker_name || 'Senza Nome' }}
                </q-item-label>
                <q-item-label caption>
                  {{ getOrderPax(order) }} pax totali
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-badge
                  v-if="getRemainingPax(order) === 0"
                  color="green"
                  label="IMBARCATI"
                  class="text-caption"
                />
                <q-badge
                  v-else
                  color="orange"
                  :label="getRemainingPax(order) + ' sul molo'"
                  class="text-caption"
                />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
      </q-card>
    </div>

    <!-- ╔══════════════════════════════════════════╗ -->
    <!-- ║  ZONA FIUME — Gommoni Varati             ║ -->
    <!-- ╚══════════════════════════════════════════╝ -->
    <div class="col-12 col-md-8">
      <q-card flat bordered class="full-height">
        <q-card-section class="bg-blue-1 q-pb-sm">
          <div class="row items-center q-gutter-sm">
            <q-icon name="sailing" color="blue-8" size="22px" />
            <div class="text-subtitle1 text-weight-bold text-blue-9">
              Flotta in Acqua
            </div>
            <q-space />
            <q-badge color="blue-grey" outline>
              {{ crewStore.allocations.length }} gommoni varati
            </q-badge>
          </div>
        </q-card-section>

        <q-separator />

        <q-card-section class="q-pa-md" style="min-height: 300px; max-height: 60vh; overflow-y: auto;">

          <!-- Pulsante VARA NUOVO GOMMONE -->
          <q-btn
            unelevated
            color="primary"
            icon="add_circle"
            label="VARA NUOVO GOMMONE"
            class="full-width q-mb-md"
            size="md"
            @click="addRaft"
          />

          <!-- Nessuna barca -->
          <div v-if="crewStore.allocations.length === 0" class="text-center text-grey-4 q-pa-xl">
            <q-icon name="directions_boat" size="56px" class="q-mb-sm" />
            <div class="text-h6 text-grey-5">Nessuna barca in acqua</div>
            <div class="text-caption text-grey-4">
              Premi "VARA NUOVO GOMMONE" per iniziare ad assegnare l'equipaggio
            </div>
          </div>

          <!-- ═══ RIGHE GOMMONI (Fase 7.E — Sensore di Galleggiamento) ═══ -->
          <q-card
            v-for="(alloc, index) in crewStore.allocations"
            :key="'raft-' + index"
            flat bordered
            class="q-mb-md"
            :class="getBoatStatusClass(alloc)"
            :style="getBoatBorderStyle(alloc)"
          >
            <!-- Header gommone con totale pax a bordo + Sensore Overflow -->
            <q-card-section class="q-py-sm q-px-md" :class="getBoatHeaderBg(alloc)">
              <div class="row items-center q-gutter-sm">
                <q-avatar
                  :color="getBoatOverflowInfo(alloc).status === 'overflow' ? 'red-2' : getBoatOverflowInfo(alloc).status === 'full' ? 'green-2' : 'blue-2'"
                  :text-color="getBoatOverflowInfo(alloc).status === 'overflow' ? 'red-10' : getBoatOverflowInfo(alloc).status === 'full' ? 'green-10' : 'blue-9'"
                  size="28px" class="text-weight-bold"
                >
                  {{ index + 1 }}
                </q-avatar>
                <div
                  class="text-subtitle2 text-weight-bold"
                  :class="getBoatOverflowInfo(alloc).status === 'overflow' ? 'text-red-10' : 'text-blue-9'"
                >
                  Gommone #{{ index + 1 }}
                </div>
                <q-space />

                <!-- Badge Sensore di Galleggiamento -->
                <q-badge
                  v-if="getBoatOverflowInfo(alloc).status === 'overflow'"
                  color="red"
                  class="text-body2 q-pa-xs text-weight-bold"
                >
                  🚨 OVERFLOW {{ getBoatPax(alloc) }}/{{ getBoatOverflowInfo(alloc).capacity }}
                </q-badge>
                <q-badge
                  v-else-if="getBoatOverflowInfo(alloc).status === 'full'"
                  color="green"
                  class="text-body2 q-pa-xs text-weight-bold"
                >
                  ✅ PIENO {{ getBoatPax(alloc) }}/{{ getBoatOverflowInfo(alloc).capacity }}
                </q-badge>
                <q-badge
                  v-else-if="getBoatOverflowInfo(alloc).capacity > 0"
                  color="blue"
                  class="text-body2 q-pa-xs"
                >
                  {{ getBoatPax(alloc) }}/{{ getBoatOverflowInfo(alloc).capacity }} — {{ getBoatOverflowInfo(alloc).capacity - getBoatPax(alloc) }} liberi
                </q-badge>
                <q-badge
                  v-else
                  :color="getBoatPax(alloc) > 0 ? 'blue' : 'grey'"
                  class="text-body2 q-pa-xs"
                >
                  {{ getBoatPax(alloc) }} pax a bordo
                </q-badge>

                <q-btn flat round dense color="red-6" icon="delete" size="sm" @click="removeRaft(index)">
                  <q-tooltip>Tira su questa barca</q-tooltip>
                </q-btn>
              </div>
            </q-card-section>

            <q-separator />

            <!-- Selettori Gommone + Guida -->
            <q-card-section class="q-py-sm q-px-md">
              <div class="row q-col-gutter-sm items-center">
                <!-- Select Gommone Fisico -->
                <div class="col-12 col-sm-6">
                  <q-select
                    v-model="alloc.resource_id"
                    :options="raftOptions"
                    option-value="id"
                    option-label="name"
                    emit-value
                    map-options
                    dense outlined
                    label="Gommone"
                    clearable
                    class="bg-white"
                  >
                    <template #prepend>
                      <q-icon name="rowing" color="blue-6" size="18px" />
                    </template>
                  </q-select>
                </div>

                <!-- Select Guida -->
                <div class="col-12 col-sm-6">
                  <q-select
                    v-model="alloc.metadata.guide_id"
                    :options="guideOptions"
                    option-value="id"
                    option-label="name"
                    emit-value
                    map-options
                    dense outlined
                    label="Guida"
                    clearable
                    class="bg-white"
                  >
                    <template #prepend>
                      <q-icon name="person" color="green-7" size="18px" />
                    </template>
                  </q-select>
                </div>
              </div>
            </q-card-section>

            <q-separator />

            <!-- Gruppi Imbarcati (Tetris Umano) -->
            <q-card-section class="q-py-sm q-px-md">
              <div class="text-caption text-weight-bold text-grey-8 q-mb-xs">
                <q-icon name="groups" size="14px" class="q-mr-xs" />Gruppi Imbarcati
              </div>

              <!-- Nessun gruppo -->
              <div v-if="!alloc.metadata.groups || alloc.metadata.groups.length === 0" class="text-caption text-grey-4 q-pa-sm text-center">
                Nessun gruppo assegnato. Usa il selettore sotto.
              </div>

              <!-- Lista gruppi imbarcati -->
              <div
                v-for="(group, gIdx) in alloc.metadata.groups"
                :key="'g-' + index + '-' + gIdx"
                class="row items-center q-gutter-xs q-mb-xs"
                style="border-bottom: 1px dashed #e0e0e0; padding-bottom: 4px;"
              >
                <div class="col">
                  <span class="text-weight-medium text-body2">{{ group.customer_name || 'Senza Nome' }}</span>
                  <span class="text-caption text-grey-6 q-ml-xs">(ord.{{ String(group.order_id || '').substring(0, 8) }})</span>
                </div>
                <div class="col-auto" style="width: 70px;">
                  <q-input
                    v-model.number="group.pax"
                    type="number"
                    dense outlined
                    :min="1"
                    class="bg-white"
                    input-class="text-center"
                    hide-bottom-space
                  />
                </div>
                <div class="col-auto" style="font-size: 11px; color: #888;">pax</div>
                <div class="col-auto">
                  <q-btn flat round dense color="red-5" icon="close" size="xs" @click="removeGroupFromRaft(alloc, gIdx)">
                    <q-tooltip>Sbarca questo gruppo</q-tooltip>
                  </q-btn>
                </div>
              </div>

              <!-- Selettore "Aggiungi Gruppo" -->
              <q-select
                :model-value="null"
                :options="availableOrdersForRaft()"
                option-label="customer_name"
                dense outlined
                label="Aggiungi Gruppo..."
                clearable
                class="bg-white q-mt-sm"
                @update:model-value="val => addGroupToRaft(alloc, val)"
              >
                <template #prepend>
                  <q-icon name="person_add" color="primary" size="18px" />
                </template>
                <template #option="scope">
                  <q-item v-bind="scope.itemProps">
                    <q-item-section>
                      <q-item-label>{{ scope.opt.customer_name || 'Senza Nome' }}</q-item-label>
                    </q-item-section>
                    <q-item-section side>
                      <q-badge color="orange" :label="getRemainingPax(scope.opt) + ' pax'" />
                    </q-item-section>
                  </q-item>
                </template>
              </q-select>
            </q-card-section>
          </q-card>

        </q-card-section>

        <q-separator />

        <!-- FOOTER — Sigilla Equipaggi (Fase 7.E — Kill-Switch Varo) -->
        <q-card-actions class="bg-grey-1 q-pa-md">
          <q-space />
          <q-btn
            unelevated
            :color="isVaroBloccato ? 'grey-5' : 'green-8'"
            icon="lock"
            label="SIGILLA EQUIPAGGI"
            :loading="crewStore.isLoading"
            :disable="isVaroBloccato || crewStore.allocations.length === 0"
            @click="sealCrew"
          >
            <q-tooltip v-if="isVaroBloccato" class="bg-red-9 text-body2" :offset="[0, 8]">
              🚫 Varo bloccato: {{ varoBlockReason }}
            </q-tooltip>
          </q-btn>
        </q-card-actions>
      </q-card>
    </div>
  </div>
</template>

<script setup>
import { computed, watch, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useCrewStore } from 'stores/crew-store'
import { useResourceStore, isGuideEligibleForActivity } from 'stores/resource-store'

const $q = useQuasar()
const crewStore = useCrewStore()
const resourceStore = useResourceStore()

// ── Props: L'ancora della barca ──
const props = defineProps({
  ride: {
    type: Object,
    required: true
  },
  orders: {
    type: Array,
    default: () => []
  }
})

// ── Ordini del turno (shortcut reattivo) ──
const rideOrders = computed(() => props.ride?.orders || props.orders || [])

// ── Helper: pax di un ordine ──
function getOrderPax(order) {
  return order.pax || order.total_pax || order.actual_pax || 0
}

// ── TETRIS UMANO: pax residui per ordine ──
function getRemainingPax(order) {
  if (!order || !order.id) return 0
  const orderTotal = getOrderPax(order)
  let assigned = 0
  for (const alloc of crewStore.allocations) {
    const groups = alloc.metadata?.groups || []
    for (const g of groups) {
      if (g.order_id === order.id) {
        assigned += (g.pax || 0)
      }
    }
  }
  return Math.max(0, orderTotal - assigned)
}

// ── Totale pax paganti sul molo ──
const totalPaxToBoard = computed(() => {
  return props.ride?.booked_pax || rideOrders.value.reduce((sum, o) => sum + getOrderPax(o), 0)
})

// ── Pax assegnati (getter dal crew store) ──
const assignedPax = computed(() => crewStore.assignedPax)

// ── Pax ancora sul molo ──
const remainingOnDock = computed(() => {
  return Math.max(0, totalPaxToBoard.value - assignedPax.value)
})

// ── Pax a bordo di un singolo gommone ──
function getBoatPax(alloc) {
  const groups = alloc.metadata?.groups || []
  return groups.reduce((sum, g) => sum + (g.pax || 0), 0)
}

// ═══════════════════════════════════════════════════════════
// FASE 7.E — SENSORE DI GALLEGGIAMENTO (Overflow Gommone)
// ═══════════════════════════════════════════════════════════

/**
 * Restituisce { capacity, pax, status } per un singolo gommone.
 * status: 'overflow' | 'full' | 'free' | 'unknown'
 * Incrocia resource_id con fleetList per ottenere la capienza fisica.
 */
function getBoatOverflowInfo(alloc) {
  const pax = getBoatPax(alloc)
  if (!alloc.resource_id) {
    return { capacity: 0, pax, status: 'unknown' }
  }
  const raft = (resourceStore.fleetList || []).find(f => f.id === alloc.resource_id)
  const cap = raft?.capacity || raft?.capacity_per_unit || 0
  if (cap <= 0) {
    return { capacity: 0, pax, status: 'unknown' }
  }
  if (pax > cap) return { capacity: cap, pax, status: 'overflow' }
  if (pax === cap) return { capacity: cap, pax, status: 'full' }
  return { capacity: cap, pax, status: 'free' }
}

// Classe dinamica per la card del gommone
function getBoatStatusClass(alloc) {
  const info = getBoatOverflowInfo(alloc)
  if (info.status === 'overflow') return 'bg-red-1'
  if (info.status === 'full') return 'bg-green-1'
  return ''
}

// Bordo dinamico per la card del gommone
function getBoatBorderStyle(alloc) {
  const info = getBoatOverflowInfo(alloc)
  if (info.status === 'overflow') return 'border-left: 4px solid #c62828; border-color: #e57373;'
  if (info.status === 'full') return 'border-left: 4px solid #2e7d32;'
  return 'border-left: 4px solid #1976D2;'
}

// Background header dinamico
function getBoatHeaderBg(alloc) {
  const info = getBoatOverflowInfo(alloc)
  if (info.status === 'overflow') return 'bg-red-2'
  if (info.status === 'full') return 'bg-green-1'
  return 'bg-blue-1'
}

// ═══════════════════════════════════════════════════════════
// FASE 7.E — KILL-SWITCH VARO (Blocco Salvataggio)
// ═══════════════════════════════════════════════════════════

/** True se c'è almeno un gommone in overflow fisico */
const hasOverflow = computed(() => {
  return crewStore.hasAnyOverflow(resourceStore.fleetList)
})

/** True se imbarcati > paganti (fantasmi a bordo) */
const hasGhostPassengers = computed(() => {
  return assignedPax.value > totalPaxToBoard.value
})

/** Kill-Switch: blocca il bottone SIGILLA se overflow O fantasmi */
const isVaroBloccato = computed(() => {
  return hasOverflow.value || hasGhostPassengers.value
})

/** Motivo del blocco (per tooltip) */
const varoBlockReason = computed(() => {
  const reasons = []
  if (hasOverflow.value) reasons.push('Almeno un gommone è in OVERFLOW')
  if (hasGhostPassengers.value) reasons.push('Ci sono fantasmi non paganti a bordo')
  return reasons.join(' + ') || ''
})

// ── Opzioni per i Select ──
const raftOptions = computed(() => {
  return (resourceStore.fleetList || []).filter(f => f.category === 'RAFT' && f.is_active !== false)
})
// Hotfix 10.F + Opzione C: Activity-Aware Guide Filtering + Date-Awareness
const guideOptions = computed(() => {
  const rideDate = props.ride?.date || props.ride?.ride_date || ''
  return (resourceStore.staffList || []).filter(s => {
    if (s.is_active === false) return false
    // 1. Idoneità contestuale all'attività (Activity-Aware + Idratazione Difensiva)
    const activity = props.ride?.activity || resourceStore.activities?.find(a => a.id === props.ride?.activity_id)
    if (!isGuideEligibleForActivity(s.roles, activity)) return false
    // 2. Contratto attivo nella data del turno (se specificato)
    if (rideDate && s.contract_periods) {
      let periods = []
      try {
        periods = typeof s.contract_periods === 'string' ? JSON.parse(s.contract_periods) : s.contract_periods
      } catch { periods = [] }
      if (Array.isArray(periods) && periods.length > 0) {
        const targetTime = new Date(rideDate).setHours(0, 0, 0, 0)
        const inContract = periods.some(cp => {
          if (!cp.start || !cp.end) return false
          return targetTime >= new Date(cp.start).setHours(0, 0, 0, 0) &&
                 targetTime <= new Date(cp.end).setHours(23, 59, 59, 999)
        })
        if (!inContract) return false
      }
      // Array vuoto o assente = tempo indeterminato → valida
    }
    // 3. Nessuna eccezione di assenza per questa data
    if (rideDate && s.id) {
      const exceptions = resourceStore.resourceExceptions || []
      const isAbsent = exceptions.some(exc =>
        String(exc.resource_id) === String(s.id) &&
        exc.resource_type === 'STAFF' &&
        exc.is_available === false &&
        Array.isArray(exc.dates) && exc.dates.includes(rideDate)
      )
      if (isAbsent) return false
    }
    return true
  })
})

// ── Ordini ancora da imbarcare (con pax residui > 0) ──
function availableOrdersForRaft() {
  return rideOrders.value.filter(o => getRemainingPax(o) > 0)
}

// ── Caricamento Busta Stagna ──
async function loadCrewData() {
  const rideId = props.ride?.id
  if (!rideId || String(rideId).startsWith('ghost')) return
  await crewStore.loadCrew(rideId)
}

onMounted(() => {
  loadCrewData()
})

// Watch reattivo: se cambia il ride, ricarica
watch(() => props.ride?.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    loadCrewData()
  }
})

// ── AZIONI GOMMONI ──
function addRaft() {
  crewStore.allocations.push({
    resource_id: null,
    resource_type: 'RAFT',
    metadata: {
      guide_id: null,
      groups: [],
    }
  })
}

function removeRaft(index) {
  crewStore.allocations.splice(index, 1)
}

// ── TETRIS UMANO: Aggiungi gruppo a gommone ──
function addGroupToRaft(alloc, order) {
  if (!order || !order.id) return
  const remaining = getRemainingPax(order)
  if (remaining <= 0) return

  if (!alloc.metadata.groups) {
    alloc.metadata.groups = []
  }

  alloc.metadata.groups.push({
    order_id: order.id,
    customer_name: order.customer_name || order.booker_name || 'Senza Nome',
    pax: remaining,
  })
}

// ── TETRIS UMANO: Rimuovi gruppo da gommone ──
function removeGroupFromRaft(alloc, groupIndex) {
  if (alloc.metadata?.groups) {
    alloc.metadata.groups.splice(groupIndex, 1)
  }
}

// ── SIGILLA (salva Busta Stagna) ──
async function sealCrew() {
  const rideId = props.ride?.id
  if (!rideId) {
    $q.notify({ type: 'warning', message: 'Turno non valido. Impossibile salvare.' })
    return
  }

  const success = await crewStore.saveCrew(rideId, crewStore.allocations)
  if (success) {
    $q.notify({
      type: 'positive',
      message: 'Equipaggi Sigillati (Bozza Salvata) 🚣',
      caption: crewStore.allocations.length + ' gommoni varati con ' + assignedPax.value + ' passeggeri',
      icon: 'check_circle',
      position: 'top'
    })
  } else {
    $q.notify({
      type: 'negative',
      message: 'Errore di salvataggio. Riprova.',
      icon: 'error',
      position: 'top'
    })
  }
}
</script>

<style scoped>
.full-height {
  min-height: 400px;
}
</style>
