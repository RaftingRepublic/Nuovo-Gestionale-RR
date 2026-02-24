<template>
  <q-page class="q-pa-md" style="max-width: 1280px; margin: 0 auto;">

    <!-- ═══ HEADER ═══ -->
    <div class="row items-center q-mb-lg">
      <q-icon name="account_tree" size="32px" color="deep-purple" class="q-mr-sm" />
      <div>
        <div class="text-h5 text-weight-bold">Costruttore di Flussi</div>
        <div class="text-caption text-grey-7">
          Libreria Mattoncini + Costruttore Insieme per ogni attività
        </div>
      </div>
    </div>

    <!-- ═══ LAYOUT A DUE COLONNE ═══ -->
    <div class="row q-col-gutter-lg">

      <!-- ╔══════════════════════════════════════════════╗ -->
      <!-- ║  COLONNA SINISTRA — LIBRERIA MATTONCINI      ║ -->
      <!-- ╚══════════════════════════════════════════════╝ -->
      <div class="col-12 col-md-4">
        <q-card flat bordered class="library-card">
          <q-card-section class="bg-blue-grey-1 q-pb-sm">
            <div class="row items-center q-mb-sm">
              <q-icon name="widgets" color="blue-grey-7" size="22px" class="q-mr-sm" />
              <div class="text-subtitle1 text-weight-bold text-blue-grey-9">Libreria Mattoncini</div>
            </div>
            <q-btn
              icon="add_circle"
              label="Nuovo Mattoncino Master"
              color="indigo"
              unelevated
              dense
              class="full-width"
              @click="openLibraryDialog(null)"
            />
          </q-card-section>

          <q-separator />

          <!-- Lista template -->
          <q-card-section class="q-pa-sm" style="max-height: 65vh; overflow-y: auto;">
            <div v-if="blockTemplates.length === 0" class="text-center q-pa-lg text-grey-5">
              <q-icon name="inventory_2" size="48px" class="q-mb-sm" />
              <div class="text-body2">Nessun mattoncino salvato</div>
              <div class="text-caption">Crea il primo mattoncino master</div>
            </div>

            <q-card
              v-for="(tpl, tIdx) in blockTemplates"
              :key="tpl.id"
              flat
              bordered
              class="q-mb-sm template-card"
            >
              <q-card-section class="q-pa-sm">
                <!-- Riga Superiore: Badge codice + Nome + Icona fixed -->
                <div class="row items-center no-wrap q-mb-xs">
                  <q-badge
                    :style="{ backgroundColor: tpl.color || '#607d8b' }"
                    text-color="white"
                    :label="tpl.code || '??'"
                    class="q-mr-sm"
                    style="font-size: 11px; min-width: 36px; text-align: center;"
                  />
                  <div class="text-body2 text-weight-bold ellipsis" style="flex: 1;">
                    {{ tpl.name || 'Senza Nome' }}
                  </div>
                  <q-icon
                    v-if="tpl.allocation_rule === 'fixed'"
                    name="lock"
                    color="orange-8"
                    size="16px"
                    class="q-ml-xs"
                  >
                    <q-tooltip>Allocazione Fissa (1 per turno)</q-tooltip>
                  </q-icon>
                </div>

                <!-- Riga Info: Durata + Risorse -->
                <div class="row items-center q-gutter-xs text-caption text-grey-7">
                  <q-icon name="schedule" size="14px" />
                  <span>{{ tpl.duration_min || 0 }} min</span>
                  <template v-if="tpl.resources && tpl.resources.length > 0">
                    <span class="q-mx-xs">·</span>
                    <q-icon name="build" size="14px" />
                    <span>{{ tpl.resources.join(', ') }}</span>
                  </template>
                </div>

                <!-- Azioni -->
                <div class="row q-gutter-xs q-mt-sm">
                  <q-btn
                    icon="edit"
                    label="Modifica"
                    flat
                    dense
                    size="xs"
                    color="indigo"
                    @click="openLibraryDialog(tIdx)"
                  />
                  <q-btn
                    icon="delete"
                    label="Elimina"
                    flat
                    dense
                    size="xs"
                    color="red-5"
                    @click="deleteTemplate(tIdx)"
                  />
                </div>
              </q-card-section>
            </q-card>
          </q-card-section>
        </q-card>
      </div>

      <!-- ╔══════════════════════════════════════════════╗ -->
      <!-- ║  COLONNA DESTRA — COSTRUTTORE INSIEME        ║ -->
      <!-- ╚══════════════════════════════════════════════╝ -->
      <div class="col-12 col-md-8">

        <!-- Selettore Attività + Salva -->
        <div class="row items-end q-col-gutter-sm q-mb-md">
          <div class="col">
            <q-select
              v-model="selectedActivityId"
              :options="activityOptions"
              option-value="value"
              option-label="label"
              emit-value
              map-options
              outlined
              label="Seleziona Attività"
              clearable
              dense
            >
              <template #prepend>
                <q-icon name="category" />
              </template>
            </q-select>
          </div>
          <div class="col-auto">
            <q-btn
              label="Salva Configurazione"
              icon="cloud_upload"
              color="deep-purple"
              unelevated
              dense
              :loading="saving"
              :disable="!selectedActivity || saving"
              @click="saveWorkflow"
            />
          </div>
        </div>

        <!-- Banner Info Attività -->
        <q-banner v-if="selectedActivity" rounded class="bg-deep-purple-1 text-deep-purple-9 q-mb-md">
          <template #avatar>
            <q-icon name="info" color="deep-purple" />
          </template>
          <div class="row items-center wrap">
            <q-badge
              :style="{ backgroundColor: selectedActivity.color_hex || '#9C27B0' }"
              text-color="white"
              :label="selectedActivity.code"
              class="q-mr-sm"
            />
            <strong>Insieme: {{ selectedActivity.name }}</strong>
            <span class="q-mx-sm">—</span>
            Durata: <strong class="q-ml-xs">{{ selectedActivity.duration_hours }}h</strong>
            <span class="q-mx-sm">|</span>
            Tratti: <strong class="q-ml-xs">{{ selectedActivity.river_segments || '—' }}</strong>
          </div>
        </q-banner>

        <!-- Nessuna Attività -->
        <div v-if="!selectedActivity" class="text-center q-pa-xl text-grey-5">
          <q-icon name="touch_app" size="64px" class="q-mb-md" />
          <div class="text-h6">Seleziona un'attività per iniziare</div>
          <div class="text-caption q-mt-xs">Oppure crea mattoncini nella Libreria a sinistra</div>
        </div>

        <!-- ═══ FLUSSI OPERATIVI ═══ -->
        <div v-if="selectedActivity && schema">

          <div v-for="(flow, fIdx) in schema.flows" :key="flow.id" class="q-mb-md">
            <q-card flat bordered class="bg-grey-1">
              <q-card-section class="row items-center q-pb-sm">
                <q-icon name="linear_scale" color="indigo" class="q-mr-sm" size="20px" />
                <q-input
                  v-model="flow.name"
                  dense
                  borderless
                  input-class="text-subtitle1 text-weight-bold"
                  style="flex: 1;"
                  placeholder="Nome Flusso..."
                />
                <q-space />
                <q-btn
                  icon="delete_outline"
                  flat round dense
                  color="red-5"
                  size="sm"
                  @click="removeFlow(fIdx)"
                >
                  <q-tooltip>Elimina Flusso</q-tooltip>
                </q-btn>
              </q-card-section>

              <q-separator />

              <!-- Blocchi orizzontali -->
              <q-card-section>
                <div class="row q-gutter-sm wrap items-center">
                  <template
                    v-for="(block, bIdx) in flow.blocks"
                    :key="block.id"
                  >
                    <!-- Giustificazione: q-space prima del primo blocco ancorato a 'end' -->
                    <q-space v-if="block.anchor === 'end' && (bIdx === 0 || flow.blocks[bIdx - 1].anchor !== 'end')" />
                    <div
                      class="cursor-pointer"
                      @click="openFlowBlockDialog(fIdx, bIdx)"
                    >
                    <q-chip
                      :style="{
                        backgroundColor: block.color || '#607d8b',
                        color: '#fff',
                        border: '2px solid transparent'
                      }"
                      text-color="white"
                      :icon="block.allocation_rule === 'fixed' ? 'lock' : 'extension'"
                      clickable
                      square
                      size="md"
                    >
                      <strong class="q-mr-xs">{{ block.code || '?' }}</strong>
                      {{ block.name || 'Blocco' }}
                      <q-badge color="white" text-color="grey-8" class="q-ml-sm" floating>
                        {{ block.duration_min || 0 }}'
                      </q-badge>
                      <q-tooltip>
                        {{ block.allocation_rule === 'fixed' ? '🔒 Fisso' : '📐 Proporzionale' }}
                        · Ancora: {{ block.anchor === 'end' ? 'Fine ←' : 'Inizio →' }}
                      </q-tooltip>
                    </q-chip>
                  </div>
                  </template>

                  <!-- Bottone aggiunta rapida blocco vuoto -->
                  <q-btn
                    icon="add"
                    label="Blocco"
                    dense flat
                    color="indigo"
                    size="sm"
                    @click="addEmptyBlockToFlow(fIdx)"
                  />
                </div>

                <!-- Indicatore ancoraggio sotto i chip -->
                <div v-if="flow.blocks.length > 0" class="row q-gutter-xs q-mt-xs">
                  <q-badge
                    v-for="block in flow.blocks"
                    :key="'anch-' + block.id"
                    :color="block.anchor === 'end' ? 'orange-7' : 'blue-grey-5'"
                    text-color="white"
                    :label="block.anchor === 'end' ? '← Fine' : 'Inizio →'"
                    style="font-size: 9px;"
                  />
                </div>

                <!-- Dropdown: Aggiungi da Libreria (modello Pull) -->
                <q-btn-dropdown
                  outline
                  color="deep-purple"
                  icon="widgets"
                  label="Aggiungi da Libreria"
                  class="q-mt-sm"
                  size="sm"
                  :disable="blockTemplates.length === 0"
                >
                  <q-list>
                    <q-item v-if="blockTemplates.length === 0" disable>
                      <q-item-section class="text-grey-5 text-caption">
                        Nessun mattoncino in libreria
                      </q-item-section>
                    </q-item>
                    <q-item
                      v-for="(tpl, tIdx) in blockTemplates"
                      :key="'pull-' + tIdx"
                      clickable
                      v-close-popup
                      @click="addBlockToSpecificFlow(fIdx, tpl)"
                    >
                      <q-item-section avatar>
                        <q-badge
                          :style="{ backgroundColor: tpl.color || '#607d8b' }"
                          text-color="white"
                          :label="tpl.code || '??'"
                          style="font-size: 11px; min-width: 36px; text-align: center;"
                        />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label>{{ tpl.name || 'Senza Nome' }}</q-item-label>
                        <q-item-label caption>
                          {{ tpl.duration_min || 0 }} min
                          <template v-if="tpl.allocation_rule === 'fixed'"> · 🔒 Fisso</template>
                        </q-item-label>
                      </q-item-section>
                    </q-item>
                  </q-list>
                </q-btn-dropdown>
              </q-card-section>
            </q-card>
          </div>

          <!-- Bottone + Flusso -->
          <q-btn
            icon="add_circle_outline"
            label="Aggiungi Flusso Operativo"
            outline
            color="deep-purple"
            class="full-width q-mb-md"
            @click="addFlow"
          />

          <!-- Debug JSON -->
          <q-expansion-item
            label="JSON Preview (Debug)"
            icon="data_object"
            header-class="text-caption text-grey-6"
            dense
          >
            <q-card flat bordered class="bg-grey-2 q-pa-sm">
              <pre style="font-size: 11px; max-height: 300px; overflow: auto; white-space: pre-wrap;">{{ JSON.stringify(schema, null, 2) }}</pre>
            </q-card>
          </q-expansion-item>
        </div>
      </div>
    </div>

    <!-- ╔══════════════════════════════════════════════════╗ -->
    <!-- ║  DIALOG UNIFICATO — Editor Blocco               ║ -->
    <!-- ╚══════════════════════════════════════════════════╝ -->
    <q-dialog v-model="dialogOpen" persistent>
      <q-card style="min-width: 480px; max-width: 600px;">
        <q-card-section class="row items-center q-pb-sm bg-deep-purple-1">
          <q-icon
            :name="dialogMode === 'library' ? 'widgets' : 'extension'"
            color="deep-purple"
            size="24px"
            class="q-mr-sm"
          />
          <div class="text-subtitle1 text-weight-bold">
            {{ dialogMode === 'library'
              ? (dialogEditIndex !== null ? 'Modifica Mattoncino Master' : 'Nuovo Mattoncino Master')
              : 'Modifica Blocco (nel Flusso)'
            }}
          </div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-separator />

        <q-card-section v-if="dialogBlock" class="q-gutter-md">
          <div class="row q-col-gutter-md">
            <!-- Nome -->
            <div class="col-12 col-sm-7">
              <q-input
                v-model="dialogBlock.name"
                outlined dense
                label="Nome Blocco"
                :rules="[v => !!v || 'Obbligatorio']"
              />
            </div>
            <!-- Codice -->
            <div class="col-12 col-sm-5">
              <q-input
                v-model="dialogBlock.code"
                outlined dense
                label="Codice"
                maxlength="5"
                hint="Es: BRF, DRP, RVR"
              />
            </div>
          </div>

          <div class="row q-col-gutter-md">
            <!-- Durata -->
            <div class="col-12 col-sm-4">
              <q-input
                v-model.number="dialogBlock.duration_min"
                outlined dense
                type="number"
                label="Durata (min)"
                :min="0"
                suffix="min"
              />
            </div>
            <!-- Colore -->
            <div class="col-12 col-sm-8">
              <q-input
                v-model="dialogBlock.color"
                outlined dense
                label="Colore HEX"
                hint="#ff9800"
              >
                <template #prepend>
                  <div
                    :style="{
                      width: '18px', height: '18px', borderRadius: '4px',
                      backgroundColor: dialogBlock.color || '#ccc',
                      border: '1px solid #aaa'
                    }"
                  />
                </template>
                <template #append>
                  <q-icon name="palette" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-color
                        v-model="dialogBlock.color"
                        format-model="hex"
                        no-header no-footer
                      />
                    </q-popup-proxy>
                  </q-icon>
                </template>
              </q-input>
            </div>
          </div>

          <!-- Risorse -->
          <q-select
            v-model="dialogBlock.resources"
            multiple use-chips use-input
            outlined dense
            new-value-mode="add"
            :options="resourceSuggestions"
            label="Risorse Collegate"
            hint="Seleziona o digita nuovi tag"
          />

          <!-- Regola Allocazione (SEMPRE visibile) -->
          <div>
            <div class="text-caption text-grey-7 q-mb-xs">Regola di Allocazione</div>
            <q-option-group
              v-model="dialogBlock.allocation_rule"
              :options="allocationRuleOptions"
              inline dense
              color="deep-purple"
            />
          </div>

          <!-- Ancoraggio Temporale (SOLO nel flusso, nascosto per la libreria) -->
          <div v-if="dialogMode === 'flow'">
            <div class="text-caption text-grey-7 q-mb-xs">Ancoraggio Temporale</div>
            <q-option-group
              v-model="dialogBlock.anchor"
              :options="anchorOptions"
              inline dense
              color="deep-purple"
            />
          </div>
        </q-card-section>

        <q-separator />

        <q-card-actions align="right" class="q-pa-md">
          <q-btn v-if="dialogMode === 'flow'" flat color="negative" icon="delete" label="Rimuovi" @click="removeBlockFromFlow" />
          <q-space />
          <q-btn label="Annulla" flat color="grey" v-close-popup />
          <q-btn
            :label="dialogMode === 'library'
              ? (dialogEditIndex !== null ? 'Aggiorna Master' : 'Crea Mattoncino')
              : 'Applica Modifiche'"
            unelevated
            color="deep-purple"
            icon="check"
            @click="confirmDialog"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useResourceStore } from 'stores/resource-store'
import { api } from 'src/boot/axios'

const $q = useQuasar()
const store = useResourceStore()
const saving = ref(false)

// ═══════════════════════════════════════════════════════════
// TASK 1: LIBRERIA MATTONCINI (LocalStorage)
// ═══════════════════════════════════════════════════════════
const LS_KEY = 'rr_block_templates'

const blockTemplates = ref(
  $q.localStorage.getItem(LS_KEY) || []
)

// Persistenza reattiva — salva ad ogni modifica profonda
watch(blockTemplates, (val) => {
  $q.localStorage.set(LS_KEY, JSON.parse(JSON.stringify(val)))
}, { deep: true })

// ═══════════════════════════════════════════════════════════
// COSTANTI E SUGGERIMENTI
// ═══════════════════════════════════════════════════════════
const resourceSuggestions = ['RAF4', 'RAF3', 'HYD', 'SK', 'CB', 'SH', 'VAN', 'RAFT', 'TRAILER', 'N', 'NC', 'C']

const anchorOptions = [
  { label: 'Offset da Inizio →', value: 'start' },
  { label: '← Offset da Fine (a ritroso)', value: 'end' },
]

const allocationRuleOptions = [
  { label: 'Proporzionale ai mezzi', value: 'per_unit' },
  { label: 'Fissa per il turno', value: 'fixed' },
]

// ═══════════════════════════════════════════════════════════
// GENERATORE ID
// ═══════════════════════════════════════════════════════════
let _counter = 0
function genId(prefix) {
  _counter++
  return `${prefix}_${Date.now()}_${_counter}`
}

// ═══════════════════════════════════════════════════════════
// SELETTORE ATTIVITÀ + SCHEMA
// ═══════════════════════════════════════════════════════════
const selectedActivityId = ref(null)
const schema = ref(null)

onMounted(async () => {
  if (!store.activities.length) {
    await store.fetchCatalogs()
  }
})

const activityOptions = computed(() => {
  return (store.activities || []).map(a => ({
    label: `[${a.code}] ${a.name} — ${a.duration_hours}h`,
    value: a.id,
  }))
})

const selectedActivity = computed(() => {
  if (!selectedActivityId.value) return null
  return (store.activities || []).find(a => String(a.id) === String(selectedActivityId.value))
})

// Watcher: carica/inizializza schema quando cambia attività
watch(selectedActivity, (act) => {
  if (!act) {
    schema.value = null
    return
  }
  if (act.workflow_schema && act.workflow_schema.flows) {
    // Deep clone + fallback allocation_rule per blocchi legacy
    const cloned = JSON.parse(JSON.stringify(act.workflow_schema))
    for (const flow of cloned.flows) {
      for (const block of flow.blocks) {
        if (!block.allocation_rule) block.allocation_rule = 'per_unit'
      }
    }
    schema.value = cloned
  } else {
    schema.value = { flows: [] }
  }
}, { immediate: true })

// ═══════════════════════════════════════════════════════════
// TASK 4: DIALOG UNIFICATO
// ═══════════════════════════════════════════════════════════
const dialogOpen = ref(false)
const dialogMode = ref('library')        // 'library' | 'flow'
const dialogBlock = ref(null)             // Oggetto blocco editato
const dialogEditIndex = ref(null)         // Indice template in libreria (null = nuovo)
const dialogFlowIdx = ref(null)           // Indici nel flusso
const dialogFlowBlockIdx = ref(null)

function _defaultBlock() {
  return {
    id: genId('blk'),
    name: '',
    code: '',
    color: '#607d8b',
    duration_min: 15,
    resources: [],
    allocation_rule: 'per_unit',
    anchor: 'start',
  }
}

// ── Apertura Dialog: Libreria ──
function openLibraryDialog(templateIndex) {
  dialogMode.value = 'library'
  dialogFlowIdx.value = null
  dialogFlowBlockIdx.value = null
  if (templateIndex !== null && templateIndex !== undefined) {
    dialogEditIndex.value = templateIndex
    dialogBlock.value = JSON.parse(JSON.stringify(blockTemplates.value[templateIndex]))
  } else {
    dialogEditIndex.value = null
    dialogBlock.value = _defaultBlock()
  }
  dialogOpen.value = true
}

// ── Apertura Dialog: Blocco nel Flusso ──
function openFlowBlockDialog(fIdx, bIdx) {
  dialogMode.value = 'flow'
  dialogEditIndex.value = null
  dialogFlowIdx.value = fIdx
  dialogFlowBlockIdx.value = bIdx
  const block = schema.value.flows[fIdx].blocks[bIdx]
  dialogBlock.value = JSON.parse(JSON.stringify(block))
  // Fallback allocation_rule per blocchi legacy
  if (!dialogBlock.value.allocation_rule) dialogBlock.value.allocation_rule = 'per_unit'
  dialogOpen.value = true
}

// ── Conferma Dialog ──
function confirmDialog() {
  if (!dialogBlock.value || !dialogBlock.value.name) {
    $q.notify({ type: 'warning', message: 'Il nome del blocco è obbligatorio.', position: 'top' })
    return
  }

  if (dialogMode.value === 'library') {
    // Salva nella Libreria
    const clean = JSON.parse(JSON.stringify(dialogBlock.value))
    // Rimuovi anchor dal master (si aggiunge solo nel flusso)
    delete clean.anchor
    if (dialogEditIndex.value !== null) {
      // Aggiorna esistente
      blockTemplates.value.splice(dialogEditIndex.value, 1, clean)
    } else {
      // Nuovo
      clean.id = genId('tpl')
      blockTemplates.value.push(clean)
    }
  } else if (dialogMode.value === 'flow') {
    // Aggiorna blocco nel flusso
    const flow = schema.value.flows[dialogFlowIdx.value]
    if (flow && flow.blocks[dialogFlowBlockIdx.value]) {
      const updated = JSON.parse(JSON.stringify(dialogBlock.value))
      flow.blocks.splice(dialogFlowBlockIdx.value, 1, updated)
    }
  }

  dialogOpen.value = false
}

function removeBlockFromFlow() {
  if (dialogMode.value !== 'flow') return
  $q.dialog({
    title: 'Rimuovi Mattoncino',
    message: 'Vuoi rimuovere questo mattoncino dal flusso?',
    cancel: true,
    persistent: true,
  }).onOk(() => {
    const flow = schema.value.flows[dialogFlowIdx.value]
    if (flow && flow.blocks[dialogFlowBlockIdx.value]) {
      flow.blocks.splice(dialogFlowBlockIdx.value, 1)
    }
    dialogOpen.value = false
  })
}

// ═══════════════════════════════════════════════════════════
// LIBRERIA: Elimina Template
// ═══════════════════════════════════════════════════════════
function deleteTemplate(tIdx) {
  $q.dialog({
    title: 'Elimina Mattoncino',
    message: `Vuoi eliminare "${blockTemplates.value[tIdx]?.name || 'questo mattoncino'}" dalla libreria?`,
    cancel: true,
    persistent: true,
  }).onOk(() => {
    blockTemplates.value.splice(tIdx, 1)
  })
}

// ═══════════════════════════════════════════════════════════
// LIBRERIA → FLUSSO: Inserisci Template in Flusso Specifico (Modello Pull)
// ═══════════════════════════════════════════════════════════
function addBlockToSpecificFlow(flowIndex, template) {
  const flow = schema.value.flows[flowIndex]
  if (!flow) return

  // Deep clone — disaccoppia completamente dalla libreria
  const newBlock = JSON.parse(JSON.stringify(template))
  newBlock.id = 'blk_' + Date.now() + Math.random().toString(36).substring(2, 7)
  newBlock.anchor = 'start'  // Default per il flusso
  if (!newBlock.allocation_rule) newBlock.allocation_rule = 'per_unit'

  flow.blocks.push(newBlock)
  $q.notify({
    type: 'positive',
    message: `"${newBlock.name}" inserito in "${flow.name}"`,
    icon: 'add_box',
    position: 'top',
    timeout: 1500,
  })
}

// ═══════════════════════════════════════════════════════════
// FLUSSI: CRUD
// ═══════════════════════════════════════════════════════════
function addFlow() {
  if (!schema.value) return
  schema.value.flows.push({
    id: genId('flow'),
    name: `Flusso ${schema.value.flows.length + 1}`,
    blocks: [],
  })
}

function removeFlow(fIdx) {
  $q.dialog({
    title: 'Elimina Flusso',
    message: `Vuoi eliminare "${schema.value.flows[fIdx]?.name || 'questo flusso'}" e tutti i suoi blocchi?`,
    cancel: true,
    persistent: true,
  }).onOk(() => {
    schema.value.flows.splice(fIdx, 1)
  })
}

// Aggiunta blocco vuoto (senza passare dalla libreria)
function addEmptyBlockToFlow(fIdx) {
  const flow = schema.value.flows[fIdx]
  if (!flow) return
  const newBlock = _defaultBlock()
  newBlock.name = 'Nuovo Blocco'
  newBlock.code = 'NEW'
  flow.blocks.push(newBlock)
  // Apri subito nel dialog
  openFlowBlockDialog(fIdx, flow.blocks.length - 1)
}

// ═══════════════════════════════════════════════════════════
// SALVATAGGIO WORKFLOW SU BACKEND
// ═══════════════════════════════════════════════════════════
async function saveWorkflow() {
  if (!selectedActivity.value || !schema.value) return
  saving.value = true
  try {
    await api.patch(`/calendar/activities/${selectedActivity.value.id}/season`, {
      workflow_schema: schema.value,
    })
    await store.fetchCatalogs()
    $q.notify({
      type: 'positive',
      message: `Workflow "${selectedActivity.value.name}" salvato con successo!`,
      icon: 'check_circle',
      position: 'top',
      timeout: 2500,
    })
  } catch (err) {
    console.error('[WorkflowBuilder] Save error:', err)
    $q.notify({
      type: 'negative',
      message: 'Errore durante il salvataggio del workflow.',
      caption: err?.response?.data?.detail || err.message || 'Controlla la connessione.',
      icon: 'error',
      position: 'top',
      timeout: 4000,
    })
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.library-card {
  position: sticky;
  top: 68px;
}
.template-card {
  transition: box-shadow 0.2s ease, transform 0.15s ease;
}
.template-card:hover {
  box-shadow: 0 2px 12px rgba(0,0,0,0.12);
  transform: translateY(-1px);
}
</style>
