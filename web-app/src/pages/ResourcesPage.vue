<template>
  <q-page class="q-pa-md bg-blue-grey-1">

    <div class="row items-center justify-between q-mb-md">
      <div>
        <div class="text-h5 text-weight-bold text-blue-grey-9">Staff & Risorse</div>
        <div class="text-caption text-grey-7">Gestione operativa: Guide, Autisti e Parco Mezzi.</div>
      </div>
    </div>

    <q-card class="shadow-2 fit-height-card my-rounded overflow-hidden row no-wrap">

      <!-- ═══ COLONNA 1: CATEGORIE ═══ -->
      <div class="col-auto border-right bg-white column" style="width: 250px">
        <div class="q-pa-md bg-blue-50 text-weight-bold text-blue-9">CATEGORIE</div>

        <q-tabs vertical v-model="activeCategory" class="text-grey-7 col-shrink" active-bg-color="blue-1" active-color="primary" indicator-color="primary">
          <q-tab name="STAFF" icon="groups" label="Personale" class="justify-start q-pl-md" />
          <q-tab name="FLEET" icon="sailing" label="Flotta & Mezzi" class="justify-start q-pl-md" />
        </q-tabs>

        <q-separator />

        <div class="q-pa-md">
          <q-btn v-if="activeCategory === 'STAFF'" unelevated color="primary" icon="person_add" label="Nuovo Staff" class="full-width" @click="openDialog('STAFF')" />
          <q-btn v-if="activeCategory === 'FLEET'" unelevated color="secondary" icon="add" label="Nuovo Mezzo" class="full-width" @click="openDialog('FLEET')" />
        </div>
      </div>

      <!-- ═══ COLONNA 2: ELENCO RISORSE ═══ -->
      <div class="col-3 border-right bg-grey-1 column" style="min-width: 280px">
        <div class="q-pa-sm q-px-md text-caption text-grey-6 bg-grey-2 border-bottom row justify-between items-center">
          <span>ELENCO {{ activeCategory }}</span>
          <q-badge color="grey-4" text-color="black">{{ activeCategory==='STAFF' ? store.staffList.length : store.fleetList.length }}</q-badge>
        </div>

        <q-scroll-area class="col">
          <q-list separator>

            <!-- STAFF -->
            <template v-if="activeCategory === 'STAFF'">
              <!-- Fissi -->
              <q-item-label header class="text-caption text-grey-6 bg-grey-2">FISSI</q-item-label>
              <q-item v-for="m in store.staffFisso" :key="m.id" clickable :active="store.selectedResourceId === m.id" active-class="bg-white border-left-active" class="resource-item" @click="selectResource(m.id)">
                <q-item-section avatar>
                  <q-avatar :color="getAvatarColor(m)" text-color="white" size="sm" font-size="14px">{{ m.name.charAt(0) }}</q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">{{ m.name }}</q-item-label>
                  <q-item-label caption class="ellipsis">
                  <q-chip v-for="r in (m.roles || [])" :key="r" :color="roleColor(r)" text-color="white" size="xs" dense class="q-mr-xs">{{ r }}</q-chip>
                  <span v-if="!m.roles || m.roles.length === 0" class="text-grey-5">Nessun ruolo</span>
                </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn flat round dense icon="delete" color="grey-4" size="sm" @click.stop="deleteItem('STAFF', m.id)" />
                </q-item-section>
              </q-item>

              <!-- Extra -->
              <q-item-label header class="text-caption text-grey-6 bg-grey-2 q-mt-xs">EXTRA</q-item-label>
              <q-item v-for="m in store.staffExtra" :key="m.id" clickable :active="store.selectedResourceId === m.id" active-class="bg-white border-left-active" class="resource-item" @click="selectResource(m.id)">
                <q-item-section avatar>
                  <q-avatar color="amber-8" text-color="white" size="sm" font-size="14px">{{ m.name.charAt(0) }}</q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">{{ m.name }} <q-badge color="amber" text-color="black" class="q-ml-xs">Extra</q-badge></q-item-label>
                  <q-item-label caption class="ellipsis">
                    <q-chip v-for="r in (m.roles || [])" :key="r" :color="roleColor(r)" text-color="white" size="xs" dense class="q-mr-xs">{{ r }}</q-chip>
                    <span v-if="!m.roles || m.roles.length === 0" class="text-grey-5">Nessun ruolo</span>
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn flat round dense icon="delete" color="grey-4" size="sm" @click.stop="deleteItem('STAFF', m.id)" />
                </q-item-section>
              </q-item>
            </template>

            <!-- FLEET -->
            <template v-if="activeCategory === 'FLEET'">
              <q-item v-for="f in store.fleetList" :key="f.id" clickable :active="store.selectedResourceId === f.id" active-class="bg-white border-left-active-orange" class="resource-item" @click="selectResource(f.id)">
                <q-item-section avatar>
                  <q-icon :name="getFleetIcon(f.category)" color="grey-7" size="sm" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">{{ f.name }}</q-item-label>
                  <q-item-label caption>{{ f.category }} · {{ f.total_quantity }} x {{ f.capacity_per_unit }} posti</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn flat round dense icon="delete" color="grey-4" size="sm" @click.stop="deleteItem('FLEET', f.id)" />
                </q-item-section>
              </q-item>
            </template>

          </q-list>
        </q-scroll-area>
      </div>

      <!-- ═══ COLONNA 3: DETTAGLIO + CALENDARIO ═══ -->
      <div class="col bg-white q-pa-lg scroll">
        <div v-if="selectedRes" class="column h-full">

          <!-- Header risorsa -->
          <div class="row items-center q-mb-lg bg-grey-1 q-pa-md rounded-borders">
            <q-avatar size="64px" :color="activeCategory==='STAFF' ? getAvatarColor(selectedRes) : 'blue-grey'" text-color="white" class="q-mr-md shadow-2">
              {{ selectedRes.name.charAt(0) }}
            </q-avatar>
            <div class="col">
              <div class="text-h5 text-weight-bold no-margin">{{ selectedRes.name }}</div>
              <div v-if="activeCategory === 'STAFF'" class="row q-gutter-xs q-mt-xs">
                <q-chip v-for="r in (selectedRes.roles || [])" :key="r" :color="roleColor(r)" text-color="white" size="sm" dense>{{ roleLabelMap[r] || r }}</q-chip>
                <q-badge :color="selectedRes.contract_type === 'EXTRA' ? 'amber' : 'blue-grey'" class="q-py-xs">{{ selectedRes.contract_type }}</q-badge>
              </div>
              <div v-else class="text-subtitle2 text-grey-7 q-mt-xs">
                {{ selectedRes.category === 'RAFT' ? '🛶 Gommone' : '🚐 Furgone' }}
                · {{ selectedRes.total_quantity }} unità x {{ selectedRes.capacity_per_unit }} posti
              </div>
            </div>
          </div>

          <!-- ═══ PERIODI CONTRATTO (solo Staff FISSO) ═══ -->
          <q-card v-if="activeCategory === 'STAFF' && selectedRes.contract_type === 'FISSO'" flat bordered class="q-mb-md">
            <q-card-section class="q-py-sm">
              <div class="text-subtitle2 text-weight-bold text-grey-9 q-mb-sm">📋 Periodi di Contratto</div>

              <!-- Periodi esistenti -->
              <div v-if="selectedRes.contract_periods && selectedRes.contract_periods.length" class="q-mb-sm">
                <q-chip
                  v-for="(cp, idx) in selectedRes.contract_periods" :key="idx"
                  removable @remove="removeContractPeriod(idx)"
                  color="blue-1" text-color="primary" icon="date_range"
                >
                  {{ cp.start }} → {{ cp.end }}
                </q-chip>
              </div>
              <div v-else class="text-caption text-grey-5 q-mb-sm">Nessun periodo definito</div>

              <!-- Form aggiunta -->
              <div class="row q-col-gutter-sm items-center">
                <div class="col"><q-input v-model="newContractStart" type="date" label="Inizio" outlined dense bg-color="white" /></div>
                <div class="col"><q-input v-model="newContractEnd" type="date" label="Fine" outlined dense bg-color="white" /></div>
                <div class="col-auto"><q-btn icon="add" label="Aggiungi" color="primary" unelevated dense @click="addContractPeriod" /></div>
              </div>
            </q-card-section>
          </q-card>

          <div class="text-subtitle1 text-weight-bold text-grey-9 q-mb-sm">
            {{ store.selectedIsExtra ? '📅 Turni Disponibilità' : '📅 Calendario Assenze / Manutenzione' }}
          </div>

          <!-- Calendario + Pannello eccezioni -->
          <q-card bordered flat class="bg-white col overflow-hidden column">
            <div class="row q-col-gutter-lg q-pa-md">

              <!-- Calendario Paintbrush -->
              <div class="col-auto">
                <div
                  class="non-selectable"
                  @mousedown="startPaint"
                  @mouseover="doPaint"
                  @mouseup="stopPaint"
                  @mouseleave="stopPaint"
                >
                  <q-date
                    v-model="calendarDates"
                    multiple minimal flat bordered
                    today-btn
                    class="shadow-1"
                  />
                </div>
                <div class="row justify-center q-gutter-md q-mt-sm">
                  <div class="row items-center text-caption"><div class="circle bg-green q-mr-xs"></div> Extra</div>
                  <div class="row items-center text-caption"><div class="circle bg-red q-mr-xs"></div> Off/Manut.</div>
                </div>
              </div>

              <!-- Pannello Salvataggio -->
              <div class="col column justify-between">
                <div class="bg-grey-1 q-pa-md rounded-borders border-grey">
                  <div class="text-weight-bold text-grey-9 q-mb-sm">
                    {{ store.selectedIsExtra ? 'Assegna Turno' : 'Segna Assenza / Guasto' }}
                  </div>
                  <div class="text-caption text-grey-6 q-mb-md">
                    Seleziona i giorni a pennello, poi salva.
                  </div>

                  <q-input v-model="excName" :label="store.selectedIsExtra ? 'Nome Turno (es. Weekend)' : 'Motivo Assenza (es. Ferie, Guasto)'" outlined dense bg-color="white" class="q-mb-md" />

                  <q-btn
                    class="full-width" unelevated
                    :color="store.selectedIsExtra ? 'positive' : 'negative'"
                    :label="store.selectedIsExtra ? 'Assegna Turno' : 'Segna Assenza'"
                    :icon="store.selectedIsExtra ? 'check_circle' : 'block'"
                    @click="saveException" :loading="store.loading"
                  />
                </div>

                <!-- Lista eccezioni correnti -->
                <div class="q-mt-md">
                  <div class="text-caption text-grey-6 q-mb-xs">Eccezioni registrate:</div>
                  <div v-if="store.resourceExceptions.length === 0" class="text-caption text-grey-4">Nessuna eccezione</div>
                  <q-card v-for="exc in store.resourceExceptions" :key="exc.id" flat bordered class="q-mb-xs">
                    <q-item dense>
                      <q-item-section avatar>
                        <q-icon :name="exc.is_available ? 'check_circle' : 'block'" :color="exc.is_available ? 'green' : 'red'" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label class="text-weight-bold text-caption">{{ exc.name || (exc.is_available ? 'Turno' : 'Assenza') }}</q-item-label>
                        <q-item-label caption>{{ exc.dates?.length || 0 }} date</q-item-label>
                      </q-item-section>
                      <q-item-section side>
                        <q-btn flat round dense icon="delete" color="negative" size="sm" @click="deleteException(exc.id)" />
                      </q-item-section>
                    </q-item>
                  </q-card>
                </div>
              </div>
            </div>
          </q-card>

        </div>
        <div v-else class="flex flex-center h-full text-grey-5 column">
          <q-icon name="touch_app" size="80px" color="grey-3" />
          <div class="text-h6 q-mt-md text-grey-4">Seleziona una risorsa dall'elenco</div>
        </div>
      </div>

    </q-card>

    <!-- ═══ Dialog Nuovo Staff/Mezzo ═══ -->
    <q-dialog v-model="dialog.open" persistent>
      <q-card style="min-width: 450px" class="my-rounded">
        <q-card-section class="bg-primary text-white row items-center justify-between q-py-sm">
          <div class="text-h6">{{ dialog.type === 'STAFF' ? 'Aggiungi Personale' : 'Aggiungi Mezzo' }}</div>
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-card-section class="q-pt-md">
          <q-form v-if="dialog.type === 'STAFF'" @submit="submitStaff" class="q-gutter-md">
            <q-input v-model="formStaff.name" label="Nome" outlined dense :rules="[val => !!val || 'Req']" />
            <q-select v-model="formStaff.contract_type" :options="['FISSO', 'EXTRA']" label="Tipo Contratto" outlined dense />
            <q-select
              v-model="formStaff.roles"
              :options="roleOptions"
              label="Ruoli"
              outlined dense
              multiple
              use-chips
              emit-value
              map-options
              option-label="label"
              option-value="value"
            />
            <div class="row justify-end q-mt-lg"><q-btn label="Salva" type="submit" color="primary" /></div>
          </q-form>
          <q-form v-if="dialog.type === 'FLEET'" @submit="submitFleet" class="q-gutter-md">
            <q-select v-model="formFleet.category" :options="[{label:'Gommone', value:'RAFT'}, {label:'Furgone', value:'VAN'}]" emit-value map-options label="Tipo" outlined dense />
            <q-input v-model="formFleet.name" label="Nome" outlined dense />
            <div class="row q-col-gutter-sm">
              <div class="col-6"><q-input v-model.number="formFleet.total_quantity" label="Quantità" type="number" outlined dense /></div>
              <div class="col-6"><q-input v-model.number="formFleet.capacity_per_unit" label="Capienza/unità" type="number" outlined dense /></div>
            </div>
            <div class="row justify-end q-mt-lg"><q-btn label="Salva" type="submit" color="secondary" /></div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useResourceStore } from 'stores/resource-store'
import { useQuasar } from 'quasar'

const store = useResourceStore()
const $q = useQuasar()

const activeCategory = ref('STAFF')
const dialog = reactive({ open: false, type: null })
const selectedRes = computed(() => store.selectedResource)

// Calendar
const calendarDates = ref(null)
const excName = ref('')

// Form
const formStaff = reactive({ name: '', contract_type: 'FISSO', roles: [] })
const formFleet = reactive({ category: 'RAFT', name: '', total_quantity: 1, capacity_per_unit: 8 })

onMounted(() => { store.fetchStaff(); store.fetchFleet() })

// Role system
const roleOptions = [
  { label: 'Guida Rafting R4', value: 'RAF4' },
  { label: 'Guida Rafting R3', value: 'RAF3' },
  { label: 'Safety Kayak', value: 'SK' },
  { label: 'Navetta / Autista', value: 'NC' },
  { label: 'Segreteria', value: 'SEG' },
  { label: 'Fotografo', value: 'FOT' },
  { label: 'Capobase', value: 'CB' },
]
const roleLabelMap = { RAF4: 'Guida R4', RAF3: 'Guida R3', SK: 'Safety Kayak', NC: 'Autista', SEG: 'Segreteria', FOT: 'Fotografo', CB: 'Capobase' }
function roleColor(r) {
  if (r === 'RAF4' || r === 'RAF3') return 'teal'
  if (r === 'SK') return 'cyan-8'
  if (r === 'NC') return 'orange'
  if (r === 'SEG') return 'indigo'
  if (r === 'FOT') return 'purple'
  if (r === 'CB') return 'red-8'
  return 'grey'
}
function getAvatarColor(m) {
  const roles = m.roles || []
  if (roles.includes('RAF4') || roles.includes('RAF3') || m.is_guide) return 'teal'
  if (roles.includes('NC') || m.is_driver) return 'orange'
  if (roles.includes('CB')) return 'red-8'
  if (roles.includes('SEG')) return 'indigo'
  return 'blue-grey'
}
function getFleetIcon(cat) { return cat==='RAFT'?'sailing':'airport_shuttle' }

// ═══ PERIODI CONTRATTO ═══
const newContractStart = ref('')
const newContractEnd = ref('')

async function addContractPeriod() {
  if (!newContractStart.value || !newContractEnd.value) {
    $q.notify({ type: 'warning', message: 'Inserisci entrambe le date' })
    return
  }
  const periods = [...(selectedRes.value.contract_periods || []), {
    start: newContractStart.value,
    end: newContractEnd.value,
  }]
  await store.updateStaff(selectedRes.value.id, { contract_periods: periods })
  newContractStart.value = ''
  newContractEnd.value = ''
  $q.notify({ type: 'positive', message: 'Periodo aggiunto' })
}

async function removeContractPeriod(idx) {
  const periods = [...(selectedRes.value.contract_periods || [])]
  periods.splice(idx, 1)
  await store.updateStaff(selectedRes.value.id, { contract_periods: periods })
  $q.notify({ type: 'info', message: 'Periodo rimosso' })
}

// Actions
function openDialog(type) { dialog.type = type; dialog.open = true; formStaff.name=''; formStaff.roles=[]; formFleet.name='' }

async function submitStaff() {
  const payload = {
    name: formStaff.name,
    contract_type: formStaff.contract_type,
    roles: formStaff.roles,
    is_guide: formStaff.roles.includes('RAF4') || formStaff.roles.includes('RAF3'),
    is_driver: formStaff.roles.includes('NC'),
  }
  await store.addStaff(payload)
  dialog.open = false
  $q.notify({ type: 'positive', message: 'Staff aggiunto' })
}

async function submitFleet() {
  await store.addFleet({...formFleet})
  dialog.open = false
  $q.notify({ type: 'positive', message: 'Mezzo aggiunto' })
}

async function selectResource(id) {
  store.selectResource(id)
  await store.fetchResourceExceptions(id)
  calendarDates.value = null
  excName.value = ''
}

async function deleteItem(type, id) {
  if (!confirm('Eliminare definitivamente?')) return
  if (type==='STAFF') await store.deleteStaff(id)
  else await store.deleteFleet(id)
  $q.notify({ type: 'info', message: 'Eliminato' })
}

// ═══ SALVA ECCEZIONE ═══
async function saveException() {
  if (!selectedRes.value || !calendarDates.value) {
    $q.notify({ type: 'warning', message: 'Seleziona almeno un giorno' })
    return
  }
  const dates = extractDates(calendarDates.value)
  const isExtra = store.selectedIsExtra

  await store.saveException({
    resource_id: selectedRes.value.id,
    resource_type: store.selectedResourceType,
    name: excName.value || null,
    is_available: isExtra,  // Extra→turno(true), Fisso/Fleet→assenza(false)
    dates: dates,
  })

  $q.notify({
    type: 'positive',
    message: isExtra ? `Turno assegnato (${dates.length} giorni)` : `Assenza registrata (${dates.length} giorni)`
  })
  calendarDates.value = null
  excName.value = ''
}

async function deleteException(excId) {
  await store.deleteException(excId, selectedRes.value.id)
  $q.notify({ type: 'info', message: 'Eccezione eliminata' })
}

// ═══ PAINTBRUSH LOGIC ═══
const isPainting = ref(false)
let currentBtn = null

const startPaint = (e) => {
  isPainting.value = true
  const btn = e.target.closest('.q-date__calendar-item button')
  if (btn && !btn.disabled) btn.click()
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

function extractDates(val) {
  if (!val) return []
  const items = Array.isArray(val) ? val : [val]
  const converted = items
    .filter(d => typeof d === 'string')
    .map(d => d.replace(/\//g, '-'))
  return [...new Set(converted)].sort()
}
</script>

<style scoped>
.my-rounded { border-radius: 12px; }
.fit-height-card { height: calc(100vh - 100px); min-height: 500px; }
.border-right { border-right: 1px solid #e0e0e0; }
.border-left-active { border-left: 4px solid var(--q-primary); }
.border-left-active-orange { border-left: 4px solid var(--q-warning); }
.border-bottom { border-bottom: 1px solid #eee; }
.border-grey { border: 1px solid #ddd; }
.border-top { border-top: 1px solid #e0e0e0; }
.h-full { height: 100%; }
.resource-item { transition: background 0.2s; }
.circle { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.non-selectable { user-select: none; }
</style>
