<template>
  <q-dialog v-model="isOpen" maximized transition-show="slide-up" transition-hide="slide-down">
    <q-card class="column" style="background: #f5f7fa;">

      <!-- ═══ HEADER ═══ -->
      <q-toolbar class="bg-blue-grey-9 text-white">
        <q-icon name="tune" size="sm" class="q-mr-sm" />
        <q-toolbar-title>Configura Stagione</q-toolbar-title>
        <q-btn flat round dense icon="refresh" @click="loadActivities" :loading="loading">
          <q-tooltip>Ricarica</q-tooltip>
        </q-btn>
        <q-btn flat round dense icon="close" v-close-popup />
      </q-toolbar>

      <!-- ═══ LOADING ═══ -->
      <div v-if="loading" class="flex flex-center q-pa-xl col">
        <q-spinner size="3em" color="primary" />
      </div>

      <!-- ═══ BODY: ACCORDION ═══ -->
      <q-scroll-area v-else class="col">
        <div class="q-pa-md" style="max-width: 900px; margin: auto;">
          <q-btn color="primary" icon="add" label="Nuova Attività" class="q-mb-md full-width" outline @click="createNewActivity" />
          <q-list bordered class="rounded-borders bg-white shadow-1">
            <q-expansion-item
              v-for="act in activities" :key="act.id"
              group="activities"
              header-class="text-weight-bold"
            >
              <!-- Header personalizzato -->
              <template v-slot:header>
                <q-item-section avatar>
                  <q-avatar :style="{ backgroundColor: act.color_hex }" text-color="white" size="36px" font-size="12px">
                    {{ act.code }}
                  </q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">{{ act.name }}</q-item-label>
                  <q-item-label caption>
                    {{ act.manager === 'Anatre' ? '🦆 Anatre (FiRaft)' : '🍇 Grape' }}
                    · {{ act.default_times?.length || 0 }} partenze
                    <span v-if="act.season_start"> · {{ act.season_start }} → {{ act.season_end }}</span>
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-badge :color="act.manager === 'Anatre' ? 'orange' : 'green'" text-color="white">
                    {{ act.manager }}
                  </q-badge>
                </q-item-section>
              </template>

              <!-- Contenuto Expansion -->
              <q-card flat class="q-pa-md bg-grey-1">

                <!-- ── RIGA 1: STAGIONE ── -->
                <div class="text-subtitle2 text-blue-grey-8 q-mb-sm">
                  <q-icon name="date_range" class="q-mr-xs" />Stagione Base
                </div>
                <div class="row q-col-gutter-sm q-mb-md">
                  <div class="col-6 col-sm-3">
                    <q-input v-model="act.season_start" label="Inizio Stagione" type="date" outlined dense />
                  </div>
                  <div class="col-6 col-sm-3">
                    <q-input v-model="act.season_end" label="Fine Stagione" type="date" outlined dense />
                  </div>
                  <div class="col-6 col-sm-3">
                    <q-select v-model="act.manager" :options="['Grape', 'Anatre']" label="Gestore" outlined dense>
                      <template v-slot:prepend>
                        <q-icon :name="act.manager === 'Anatre' ? 'pets' : 'eco'" :color="act.manager === 'Anatre' ? 'orange' : 'green'" />
                      </template>
                    </q-select>
                  </div>
                  <div class="col-6 col-sm-3">
                    <q-input v-model="act.code" label="Codice" outlined dense hint="Es: CL, FA, SL" />
                  </div>
                </div>

                <!-- ── RIGA 2: PREZZO / DURATA / COLORE ── -->
                <div class="row q-col-gutter-sm q-mb-md">
                  <div class="col-4 col-sm-3">
                    <q-input v-model.number="act.price" label="Prezzo Base (€)" type="number" outlined dense step="0.50" />
                  </div>
                  <div class="col-4 col-sm-3">
                    <q-input v-model.number="act.duration_hours" label="Durata (ore)" type="number" outlined dense step="0.5" />
                  </div>
                  <div class="col-4 col-sm-3">
                    <q-input v-model="act.color_hex" label="Colore" outlined dense>
                      <template v-slot:append>
                        <q-icon name="palette" class="cursor-pointer">
                          <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                            <q-color v-model="act.color_hex" />
                          </q-popup-proxy>
                        </q-icon>
                      </template>
                      <template v-slot:prepend>
                        <div :style="{ width: '18px', height: '18px', borderRadius: '4px', backgroundColor: act.color_hex }" />
                      </template>
                    </q-input>
                  </div>
                  <div class="col-12 col-sm-3">
                    <q-input v-model="act.river_segments" label="Tratti Fiume" outlined dense placeholder="T1,T2" />
                  </div>
                </div>

                <!-- ── TOGGLE ARR ── -->
                <div class="q-mb-md">
                  <q-toggle v-model="act.allow_intersections" label="Consenti Incroci Fiume (ARR)" color="orange" left-label />
                </div>

                <!-- ── RIGA YIELD MANAGEMENT ── -->
                <div class="row q-col-gutter-sm q-mb-md">
                  <div class="col-4">
                    <q-select v-model="act.activity_class" :options="['RAFTING', 'HYDRO', 'KAYAK']" label="Classe Mezzo" outlined dense />
                  </div>
                  <div class="col-4">
                    <q-input v-model.number="act.yellow_threshold" type="number" label="Soglia Giallo (posti)" outlined dense />
                  </div>
                  <div class="col-4">
                    <q-input v-model.number="act.overbooking_limit" type="number" label="Max Overbooking" outlined dense />
                  </div>
                </div>

                <!-- ── RIGA 3: ORARI BASE (6 slot) ── -->
                <div class="text-subtitle2 text-blue-grey-8 q-mb-sm">
                  <q-icon name="schedule" class="q-mr-xs" />Orari Partenza Base (max 6)
                </div>
                <div class="row q-col-gutter-xs q-mb-md">
                  <div class="col-4 col-sm-2" v-for="(_, idx) in 6" :key="'time-'+idx">
                    <q-input
                      :model-value="getTimeSlot(act, idx)"
                      @update:model-value="setTimeSlot(act, idx, $event)"
                      :label="'Slot ' + (idx + 1)"
                      type="time" outlined dense clearable
                    />
                  </div>
                </div>

                <q-separator class="q-my-md" />

                <!-- ── SOTTOPERIODI ── -->
                <div class="row items-center justify-between q-mb-sm">
                  <div class="text-subtitle2 text-blue-grey-8">
                    <q-icon name="event_note" class="q-mr-xs" />Eccezioni / Sottoperiodi
                    <q-badge color="grey-5" class="q-ml-sm">{{ act.sub_periods?.length || 0 }}</q-badge>
                  </div>
                  <q-btn dense unelevated size="sm" color="teal" icon="add" label="Aggiungi Eccezione"
                    @click="openSubPeriodDialog(act)" />
                </div>

                <!-- Lista sottoperiodi -->
                <div v-if="act.sub_periods && act.sub_periods.length > 0">
                  <q-card v-for="(sp, spIdx) in act.sub_periods" :key="sp.id || spIdx"
                    flat bordered class="q-mb-sm">
                    <q-item dense>
                      <q-item-section avatar>
                        <q-icon :name="sp.is_closed ? 'block' : 'date_range'"
                          :color="sp.is_closed ? 'red' : 'teal'" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label class="text-weight-bold">
                          {{ sp.name || 'Eccezione' }}
                          <q-badge v-if="sp.is_closed" color="red" class="q-ml-sm">CHIUSO</q-badge>
                        </q-item-label>
                        <q-item-label caption>
                          {{ sp.dates ? sp.dates.length : 0 }} date selezionate
                          <span v-if="sp.dates && sp.dates.length > 0" class="text-grey-6">
                            · {{ sp.dates.slice(0, 3).join(', ') }}{{ sp.dates.length > 3 ? '…' : '' }}
                          </span>
                        </q-item-label>
                        <q-item-label caption v-if="!sp.is_closed && sp.override_price">
                          € {{ sp.override_price }}
                          <span v-if="sp.override_times?.length"> · Orari: {{ sp.override_times.join(', ') }}</span>
                        </q-item-label>
                      </q-item-section>
                      <q-item-section side>
                        <q-btn flat round dense icon="delete" color="negative" size="sm"
                          @click="act.sub_periods.splice(spIdx, 1)" />
                      </q-item-section>
                    </q-item>
                  </q-card>
                </div>
                <div v-else class="text-grey-5 text-center q-py-sm text-caption">
                  Nessuna eccezione configurata
                </div>

                <q-separator class="q-my-md" />

                <!-- ── BOTTONI SALVA + ELIMINA ── -->
                <div class="row q-gutter-sm">
                  <q-btn
                    label="Salva Modifiche Attività" icon="save" color="primary" unelevated
                    class="col" :loading="savingId === act.id"
                    @click="saveSeason(act)"
                  />
                  <q-btn
                    flat color="negative" icon="delete" label="Elimina"
                    @click="deleteActivity(act.id, act.name)"
                  />
                </div>
              </q-card>
            </q-expansion-item>
          </q-list>
        </div>
      </q-scroll-area>
    </q-card>

    <!-- ═══ SOTTO-DIALOG: AGGIUNGI ECCEZIONE ═══ -->
    <q-dialog v-model="spDialogOpen">
      <q-card style="width: 520px; max-width: 95vw;">
        <q-card-section class="bg-teal-8 text-white row items-center justify-between q-py-sm">
          <div class="text-h6">Nuova Eccezione</div>
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <!-- Nome eccezione -->
          <q-input v-model="newSp.name" label="Nome Eccezione (es. Weekend Settembre)" outlined dense />

          <!-- Calendario Paintbrush: tieni premuto e trascina -->
          <div class="text-subtitle2 text-blue-grey-8">
            <q-icon name="brush" class="q-mr-xs" />Seleziona date (tieni premuto e trascina a pennello)
          </div>
          <div
            class="flex flex-center non-selectable"
            @mousedown="startPaint"
            @mouseover="doPaint"
            @mouseup="stopPaint"
            @mouseleave="stopPaint"
          >
            <q-date
              v-model="newSp.rawDates"
              multiple
              color="teal"
              flat bordered
              minimal
            />
          </div>

          <div v-if="parsedDateCount > 0" class="text-caption text-teal-8 text-center">
            {{ parsedDateCount }} giorni selezionati
          </div>

          <q-separator />

          <!-- Toggle Chiusura -->
          <q-toggle v-model="newSp.is_closed" label="Chiusura totale (attività chiusa)" color="red" />

          <!-- Campi visibili solo se NON chiuso -->
          <template v-if="!newSp.is_closed">
            <q-input v-model.number="newSp.override_price" label="Prezzo Sovrascritto (€)" type="number" outlined dense />

            <div class="row q-col-gutter-sm q-mt-sm">
              <div class="col-6">
                <q-input v-model.number="newSp.yellow_threshold" type="number" label="Sovrascrivi Soglia Giallo" outlined dense placeholder="vuoto = default" />
              </div>
              <div class="col-6">
                <q-input v-model.number="newSp.overbooking_limit" type="number" label="Sovrascrivi Overbooking" outlined dense placeholder="vuoto = default" />
              </div>
            </div>

            <div class="text-subtitle2 text-blue-grey-8">Orari Sovrascritti (max 6)</div>
            <div class="row q-col-gutter-xs">
              <div class="col-4" v-for="idx in 6" :key="'sp-time-'+idx">
                <q-input
                  :model-value="newSp.override_times[idx - 1] || ''"
                  @update:model-value="setSpTime(idx - 1, $event)"
                  :label="'Slot ' + idx"
                  type="time" outlined dense clearable
                />
              </div>
            </div>
          </template>
        </q-card-section>

        <q-separator />

        <q-card-actions align="right" class="bg-grey-1 q-pa-md">
          <q-btn flat label="Annulla" v-close-popup />
          <q-btn label="Aggiungi" color="teal" unelevated icon="add" @click="addSubPeriod" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-dialog>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

const $q = useQuasar()

// ═══ STATE PRINCIPALE ═══
const isOpen = ref(false)
const loading = ref(false)
const activities = ref([])
const savingId = ref(null)

// ═══ CRUD ATTIVITÀ ═══
function createNewActivity() {
  $q.dialog({
    title: 'Nuova Attività',
    message: 'Inserisci il nome della nuova attività:',
    prompt: { model: '', type: 'text', label: 'Es. Rafting Extreme' },
    cancel: true,
    persistent: false,
  }).onOk(async (name) => {
    if (!name || !name.trim()) return
    const code = name.trim().substring(0, 2).toUpperCase()
    try {
      await api.post('/calendar/activities', { name: name.trim(), code })
      $q.notify({ type: 'positive', message: `✅ "${name.trim()}" creata!` })
      await loadActivities()
    } catch (e) {
      console.error(e)
      $q.notify({ type: 'negative', message: 'Errore creazione attività' })
    }
  })
}

function deleteActivity(id, name) {
  $q.dialog({
    title: 'Elimina Attività',
    message: `Sei sicuro di voler eliminare "${name}" e tutte le sue regole stagionali?`,
    cancel: true,
    persistent: false,
    ok: { label: 'Elimina', color: 'negative', flat: true },
  }).onOk(async () => {
    try {
      await api.delete('/calendar/activities/' + id)
      $q.notify({ type: 'info', message: `🗑️ "${name}" eliminata` })
      await loadActivities()
    } catch (e) {
      console.error(e)
      $q.notify({ type: 'negative', message: 'Errore eliminazione' })
    }
  })
}

// ═══ STATE SOTTO-DIALOG ═══
const spDialogOpen = ref(false)
const spTargetActivity = ref(null)
const newSp = reactive({
  name: '',
  rawDates: null,
  is_closed: false,
  allow_intersections: false,
  yellow_threshold: null,
  overbooking_limit: null,
  override_price: null,
  override_times: ['', '', '', '', '', ''],
})

// Esponi isOpen per PlanningPage
defineExpose({ isOpen })

// Carica quando si apre
watch(isOpen, (val) => {
  if (val) loadActivities()
})

// ═══ PAINTBRUSH LOGIC ═══
const isPainting = ref(false)
let currentBtn = null

const startPaint = (e) => {
  isPainting.value = true
  const btn = e.target.closest('.q-date__calendar-item button')
  if (btn && !btn.disabled) {
    btn.click()
  }
  currentBtn = btn
}

const stopPaint = () => {
  isPainting.value = false
  currentBtn = null
}

const doPaint = (e) => {
  if (!isPainting.value) return
  const btn = e.target.closest('.q-date__calendar-item button')
  if (btn && btn !== currentBtn && !btn.disabled) {
    btn.click()
    currentBtn = btn
  }
}

// ═══ PARSER QUASAR DATES (solo multiple, no range) ═══
function parseQuasarDates(modelValue) {
  if (!modelValue) return []
  const items = Array.isArray(modelValue) ? modelValue : [modelValue]
  const converted = items
    .filter(d => typeof d === 'string')
    .map(d => d.replace(/\//g, '-'))
  return [...new Set(converted)].sort()
}

const parsedDateCount = computed(() => {
  return parseQuasarDates(newSp.rawDates).length
})

// ═══ LOAD ═══
async function loadActivities() {
  loading.value = true
  try {
    const res = await api.get('/calendar/activities')
    activities.value = res.data
  } catch (e) {
    console.error(e)
    $q.notify({ type: 'negative', message: 'Errore caricamento attività' })
  } finally {
    loading.value = false
  }
}

// ═══ TIME SLOTS HELPERS (6 slot) ═══
function getTimeSlot(act, idx) {
  if (!act.default_times) return ''
  return act.default_times[idx] || ''
}

function setTimeSlot(act, idx, val) {
  if (!act.default_times) act.default_times = []
  while (act.default_times.length <= idx) act.default_times.push('')
  act.default_times[idx] = val || ''
}

// ═══ SUB-PERIOD DIALOG ═══
function openSubPeriodDialog(act) {
  spTargetActivity.value = act
  newSp.name = ''
  newSp.rawDates = null
  newSp.is_closed = false
  newSp.allow_intersections = false
  newSp.yellow_threshold = null
  newSp.overbooking_limit = null
  newSp.override_price = null
  newSp.override_times = ['', '', '', '', '', '']
  spDialogOpen.value = true
}

function setSpTime(idx, val) {
  newSp.override_times[idx] = val || ''
}

function addSubPeriod() {
  const dates = parseQuasarDates(newSp.rawDates)

  if (dates.length === 0) {
    $q.notify({ type: 'warning', message: 'Seleziona almeno un giorno sul calendario' })
    return
  }

  const sp = {
    name: newSp.name || null,
    dates: dates,
    is_closed: newSp.is_closed,
    allow_intersections: newSp.allow_intersections || null,
    yellow_threshold: newSp.yellow_threshold ?? null,
    overbooking_limit: newSp.overbooking_limit ?? null,
    override_price: newSp.is_closed ? null : (newSp.override_price || null),
    override_times: newSp.is_closed ? [] : newSp.override_times.filter(t => t && t.trim() !== ''),
  }

  if (!spTargetActivity.value.sub_periods) {
    spTargetActivity.value.sub_periods = []
  }
  spTargetActivity.value.sub_periods.push(sp)
  spDialogOpen.value = false

  $q.notify({ type: 'positive', message: `"${sp.name || 'Eccezione'}" — ${dates.length} giorni aggiunti` })
}

// ═══ SALVA STAGIONE ═══
async function saveSeason(act) {
  savingId.value = act.id
  try {
    const cleanTimes = (act.default_times || []).filter(t => t && t.trim() !== '')

    const cleanSp = (act.sub_periods || []).map(sp => ({
      name: sp.name || null,
      dates: sp.dates || [],
      is_closed: sp.is_closed || false,
      allow_intersections: sp.allow_intersections ?? null,
      yellow_threshold: sp.yellow_threshold ?? null,
      overbooking_limit: sp.overbooking_limit ?? null,
      override_price: sp.override_price || null,
      override_times: (sp.override_times || []).filter(t => t && t.trim() !== ''),
    }))

    await api.patch(`/calendar/activities/${act.id}/season`, {
      code: act.code || undefined,
      color_hex: act.color_hex || undefined,
      duration_hours: act.duration_hours ?? undefined,
      river_segments: act.river_segments || undefined,
      manager: act.manager,
      price: act.price,
      season_start: act.season_start || null,
      season_end: act.season_end || null,
      default_times: cleanTimes,
      allow_intersections: act.allow_intersections ?? false,
      activity_class: act.activity_class || 'RAFTING',
      yellow_threshold: act.yellow_threshold ?? 8,
      overbooking_limit: act.overbooking_limit ?? 0,
      sub_periods: cleanSp,
    })

    $q.notify({ type: 'positive', message: `✅ ${act.name} salvata con successo!`, icon: 'check_circle' })
    await loadActivities()
  } catch (e) {
    console.error(e)
    $q.notify({ type: 'negative', message: 'Errore salvataggio' })
  } finally {
    savingId.value = null
  }
}
</script>
