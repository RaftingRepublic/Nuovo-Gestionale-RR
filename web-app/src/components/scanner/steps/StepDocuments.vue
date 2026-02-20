<template>
  <div class="col-12 col-md-8">

    <div v-if="!store.isEditMode" class="q-mb-lg">
      <div class="text-subtitle1 text-center q-mb-sm text-grey-8">Come vuoi inserire i dati?</div>
      <div class="row q-col-gutter-sm justify-center">
        <div class="col-12 col-sm-6">
          <div
            class="selection-card cursor-pointer q-pa-sm transition-generic"
            :class="!store.isManualMode ? 'active-mode shadow-2' : 'inactive-mode'"
            v-on:click="store.setInputMode('SCAN')"
            v-ripple
          >
            <div class="row items-center no-wrap">
              <div class="col-auto q-mr-md">
                <q-avatar color="blue-1" text-color="primary" icon="document_scanner" size="md" font-size="20px"/>
              </div>
              <div class="col">
                <div class="text-weight-bold text-primary">{{ t.docs.mode_scan_title }}</div>
                <div class="text-caption text-grey-7">{{ t.docs.mode_scan_desc }}</div>
              </div>
              <div class="col-auto">
                <q-radio :model-value="store.inputMode" v-on:update:model-value="val => store.inputMode = val" val="SCAN" dense color="primary" class="no-pointer-events" />
              </div>
            </div>
            <div v-if="!store.isManualMode" class="floating-badge bg-green text-white">Consigliato</div>
          </div>
        </div>

        <div class="col-12 col-sm-6">
          <div
            class="selection-card cursor-pointer q-pa-sm transition-generic"
            :class="store.isManualMode ? 'active-mode-manual shadow-2' : 'inactive-mode'"
            v-on:click="store.setInputMode('MANUAL')"
            v-ripple
          >
            <div class="row items-center no-wrap">
              <div class="col-auto q-mr-md">
                <q-avatar :color="store.isManualMode ? 'orange-1' : 'grey-2'" :text-color="store.isManualMode ? 'orange-9' : 'grey-6'" icon="edit_note" size="md" font-size="20px"/>
              </div>
              <div class="col">
                <div class="text-weight-bold" :class="store.isManualMode ? 'text-orange-9' : 'text-grey-8'">{{ t.docs.mode_manual_title }}</div>
                <div class="text-caption text-grey-7">{{ t.docs.mode_manual_desc }}</div>
              </div>
              <div class="col-auto">
                <q-radio :model-value="store.inputMode" v-on:update:model-value="val => store.inputMode = val" val="MANUAL" dense color="orange" class="no-pointer-events" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <q-card v-if="!store.isManualMode" bordered class="q-mb-md">
      <q-card-section class="bg-grey-2">
        <div class="text-weight-bold text-subtitle1">{{ adultCardTitle }}</div>
        <div class="text-caption text-grey-7">{{ t.docs.guardian_card_desc }}</div>
      </q-card-section>
      <q-card-section>
        <div>
          <q-select
            v-model="store.guardian.ocrData.tipo_documento"
            :options="docTypes"
            :label="t.docs.type_doc"
            outlined dense class="q-mb-md" emit-value map-options
            :readonly="store.isEditMode"
          />

          <div v-if="!store.isEditMode">
            <div class="row q-col-gutter-sm items-center q-mb-sm">
              <div class="col">
                <q-file outlined dense v-model="store.guardian.frontFile" :label="t.docs.scan_front" accept="image/*" @update:model-value="store.startGuardianScan()">
                  <template v-slot:prepend><q-icon name="image" /></template>
                </q-file>
              </div>
              <div class="col-auto">
                <q-btn round color="primary" icon="photo_camera" v-on:click="$emit('open-camera', { target: 'guardian', side: 'FRONT' })">
                  <q-tooltip>Fotocamera</q-tooltip>
                </q-btn>
              </div>
            </div>
            <div class="row q-col-gutter-sm items-center transition-generic" :style="{ opacity: isBackRequired(store.guardian.ocrData.tipo_documento) ? 1 : 0.5 }">
              <div class="col">
                <q-file
                  outlined dense
                  v-model="store.guardian.backFile"
                  :label="isBackRequired(store.guardian.ocrData.tipo_documento) ? 'Retro (Obbligatorio)' : 'Retro (Non richiesto)'"
                  accept="image/*"
                  @update:model-value="store.startGuardianScan()"
                  :disable="!isBackRequired(store.guardian.ocrData.tipo_documento)"
                >
                  <template v-slot:prepend><q-icon name="flip" /></template>
                </q-file>
              </div>
              <div class="col-auto">
                <q-btn
                  round color="primary" icon="photo_camera"
                  v-on:click="$emit('open-camera', { target: 'guardian', side: 'BACK' })"
                  :disable="!isBackRequired(store.guardian.ocrData.tipo_documento)"
                >
                  <q-tooltip>Fotocamera</q-tooltip>
                </q-btn>
              </div>
            </div>
          </div>
          <div v-else class="text-caption text-grey-6">* Scansioni non modificabili</div>

          <div v-if="store.guardian.ocrData.debug" class="q-mt-md">
            <q-expansion-item dense icon="bug_report" :label="t.docs.debug_ai" header-class="text-white bg-grey-8">
              <q-card class="bg-grey-2">
                <q-card-section>
                  <div class="q-mt-sm text-caption">Source: <q-badge color="purple">{{ store.guardian.ocrData.source }}</q-badge></div>
                  <div v-if="store.guardian.ocrData.warning_mismatch" class="q-mt-sm text-red text-weight-bold">
                     ⚠️ MISMATCH: Tipo documento rilevato diverso da quello dichiarato!
                  </div>
                </q-card-section>
              </q-card>
            </q-expansion-item>
          </div>
        </div>
      </q-card-section>
    </q-card>

    <div class="q-my-lg">
      <div class="row items-center justify-between q-mb-md">
         <q-toggle
          v-if="!store.isEditMode"
          v-model="store.hasMinors"
          :label="t.docs.minor_toggle"
          size="lg"
          class="text-weight-medium"
        />
        <!-- Stepper per numero minori (Visibile solo se ci sono minori) -->
        <div v-if="store.hasMinors" class="row items-center q-gutter-sm bg-grey-2 rounded-borders q-px-sm">
            <q-btn round flat dense icon="remove" color="primary" @click="updateMinorsCount(-1)" :disable="store.minors.length <= 1" />
            <div class="text-weight-bold text-h6 q-px-md">{{ store.minors.length }}</div>
            <q-btn round flat dense icon="add" color="primary" @click="updateMinorsCount(1)" :disable="store.minors.length >= 10" />
        </div>
      </div>

      <q-slide-transition>
        <div v-if="store.hasMinors" class="bg-orange-1 q-pa-md rounded-borders q-mt-sm border-orange">
          <div class="row items-center justify-between q-mb-md">
            <div class="text-h6 text-orange-9"><q-icon name="child_care" /> {{ t.docs.minor_area }}</div>
            <q-toggle
              v-if="!store.isEditMode"
              v-model="store.tutorParticipates"
              :label="t.docs.tutor_participates"
              color="green" dense
            />
          </div>

          <!-- LISTA MINORI: Mostra cards solo se NON è Manual Mode -->
          <div v-if="!store.isManualMode">
            <div v-for="(minor, index) in store.minors" :key="minor.id" class="q-mb-md">
              <q-card bordered class="bg-white">
                <q-card-section class="row justify-between bg-grey-1 items-center q-py-sm">
                  <div class="text-weight-bold text-primary">Minore #{{ index + 1 }}</div>
                  <q-btn v-if="!store.isEditMode" flat round color="negative" icon="delete" size="sm" v-on:click="store.removeMinor(index)" />
                </q-card-section>
                <q-separator />
                <q-card-section>
                    <q-select
                      v-model="minor.ocrData.tipo_documento"
                      :options="docTypes"
                      :label="t.docs.type_doc"
                      outlined dense class="q-mb-md" emit-value map-options
                      :readonly="store.isEditMode"
                    />
                    <div v-if="!store.isEditMode">
                      <div class="row q-col-gutter-sm items-center q-mb-sm">
                        <div class="col">
                          <q-file outlined dense v-model="minor.frontFile" :label="t.docs.scan_front" accept="image/*" @update:model-value="store.startMinorScan(index)">
                            <template v-slot:prepend><q-icon name="image" /></template>
                          </q-file>
                        </div>
                        <div class="col-auto">
                          <q-btn round color="primary" icon="photo_camera" v-on:click="$emit('open-camera', { target: 'minor', side: 'FRONT', index })">
                            <q-tooltip>Fotocamera</q-tooltip>
                          </q-btn>
                        </div>
                      </div>
                      <div class="row q-col-gutter-sm items-center transition-generic" :style="{ opacity: isBackRequired(minor.ocrData.tipo_documento) ? 1 : 0.5 }">
                        <div class="col">
                          <q-file outlined dense
                            v-model="minor.backFile"
                            :label="isBackRequired(minor.ocrData.tipo_documento) ? 'Retro (Obbligatorio)' : 'Retro (Non richiesto)'"
                            accept="image/*"
                            @update:model-value="store.startMinorScan(index)"
                            :disable="!isBackRequired(minor.ocrData.tipo_documento)"
                          >
                            <template v-slot:prepend><q-icon name="flip" /></template>
                          </q-file>
                        </div>
                        <div class="col-auto">
                          <q-btn
                            round color="primary" icon="photo_camera"
                            v-on:click="$emit('open-camera', { target: 'minor', side: 'BACK', index })"
                            :disable="!isBackRequired(minor.ocrData.tipo_documento)"
                          >
                            <q-tooltip>Fotocamera</q-tooltip>
                          </q-btn>
                        </div>
                      </div>
                    </div>
                </q-card-section>
              </q-card>
            </div>

            <q-btn
              v-if="!store.isEditMode"
              outline color="primary" icon="add" :label="t.docs.add_minor"
              class="full-width bg-white"
              v-on:click="store.addMinor()" :disable="store.minors.length >= 5"
            />
          </div>
          <div v-else class="text-grey-7 text-center q-pa-md bg-white rounded-borders">
             <q-icon name="edit_note" size="sm" /> Modalità manuale attivata per <b>{{ store.minors.length }}</b> minori.
             <br><small>Inserirai i dati nello step di verifica.</small>
          </div>

        </div>
      </q-slide-transition>
    </div>

    <div class="row justify-end q-mt-xl q-gutter-sm">
      <q-btn flat :label="t.nav.back" v-on:click="$emit('prev')" />
      <q-btn color="primary" :label="t.nav.continue" v-on:click="checkAndProceed" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRegistrationStore } from 'stores/registration-store'
import { translations } from 'src/constants/translations' // Named Import Corretto
import { useQuasar } from 'quasar'

const emit = defineEmits(['next', 'prev', 'open-camera'])
const store = useRegistrationStore()
const $q = useQuasar()

// Localization helper
const t = computed(() => translations[store.language] || translations.it)

const adultCardTitle = computed(() =>
  store.hasMinors ?
  (store.tutorParticipates ? 'Tutore (Partecipante)' : 'Tutore (Non partecipante)') :
  'Partecipante'
)

const docTypes = [
  {label: 'CIE Italiana', value: 'CIE'},
  {label: 'Patente di guida', value: 'PATENTE_IT'},
  {label: 'ID straniera', value: 'CIE_EU'},
  {label: 'Passaporto', value: 'PASSAPORTO'},
  {label: 'Altro', value: 'ALTRO'}
]

// Logica per determinare se il retro è richiesto
function isBackRequired(docType) {
  return docType !== 'PASSAPORTO'
}

function updateMinorsCount(delta) {
  const currentLen = store.minors.length
  if (delta > 0 && currentLen < 10) {
    store.addMinor()
  } else if (delta < 0 && currentLen > 0) {
    store.removeMinor(currentLen - 1)
  }
}

function checkAndProceed() {
  if(store.isManualMode || store.isEditMode) {
    emit('next')
    return
  }

  // Validazione Adulto/Tutore
  if(!store.guardian.frontFile) {
    $q.notify({type:'warning', message: 'Fronte documento tutore obbligatorio'})
    return
  }
  if(isBackRequired(store.guardian.ocrData.tipo_documento) && !store.guardian.backFile) {
    $q.notify({type:'warning', message: `Per ${store.guardian.ocrData.tipo_documento} è richiesto anche il Retro`})
    return
  }

  // Validazione Minori
  if(store.hasMinors) {
    for(let i = 0; i < store.minors.length; i++) {
      const m = store.minors[i]
      if(!m.frontFile) {
        $q.notify({type:'warning', message: `Fronte documento Minore #${i+1} mancante`})
        return
      }
      if(isBackRequired(m.ocrData.tipo_documento) && !m.backFile) {
        $q.notify({type:'warning', message: `Retro documento Minore #${i+1} mancante`})
        return
      }
    }
  }

  // ── OCR in background (fire-and-forget) ──
  // L'utente avanza subito; Azure lavora silenziosamente
  store.resolveAllOcr()
    .then(() => {
      if (store.guardian.isAnalyzed && store.guardian.ocrData.nome) {
        $q.notify({ type: 'positive', message: 'Dati documento estratti!', timeout: 2000 })
      }
    })
    .catch((err) => {
      console.error('OCR background error:', err)
      $q.notify({ type: 'warning', message: 'Analisi non completata. Potrai compilare i dati manualmente.', timeout: 3000 })
    })

  // Avanzamento IMMEDIATO – nessuna attesa
  emit('next')
}
</script>

<style scoped>
.selection-card {
  border-radius: 8px;
  border: 1px solid #ddd;
  position: relative;
  background: white;
}
.selection-card:hover { border-color: #bbb; }
.active-mode { border: 2px solid var(--q-primary); background: #e3f2fd; }
.active-mode-manual { border: 2px solid var(--q-warning); background: #fff3e0; }
.inactive-mode { opacity: 0.8; }
.floating-badge {
  position: absolute; top: -8px; right: -8px;
  font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: bold;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
.border-orange { border: 1px solid var(--q-warning); }
.transition-generic { transition: all 0.2s ease-in-out; }
</style>
