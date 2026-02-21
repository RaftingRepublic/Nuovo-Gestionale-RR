<template>
  <q-page class="q-pa-md bg-grey-1">
    <div class="text-h4 q-mb-md text-primary text-weight-bold text-center">
      {{ store.isEditMode ? t.nav.confirm_edit : 'Consenso Informato' }}
    </div>

    <div v-if="loadingData" class="flex flex-center q-pa-xl">
      <q-spinner-dots size="3em" color="primary" />
      <div class="q-mt-md text-grey-7">Caricamento dati...</div>
    </div>

    <q-stepper
      v-else
      v-model="step"
      ref="stepper"
      color="primary"
      animated
      alternative-labels
      header-nav
      class="shadow-2 rounded-borders"
    >
      <!-- STEP 1: LINGUA -->
      <q-step :name="1" :title="t.steps.lang" icon="translate" :done="step > 1">
        <div class="row justify-center text-center">
          <div class="col-12 col-md-8">
            <div class="text-h6 q-mb-lg">Scegli la lingua / Choose language</div>

            <div class="row q-gutter-md justify-center">
              <!-- ITALIANO -->
              <q-btn
                size="lg"
                :unelevated="store.language === 'it'"
                :outline="store.language !== 'it'"
                color="primary"
                label="Italiano"
                class="transition-generic q-px-lg"
                v-on:click="store.setLanguage('it')"
              />

              <!-- INGLESE -->
              <q-btn
                size="lg"
                :unelevated="store.language === 'en'"
                :outline="store.language !== 'en'"
                color="primary"
                label="English"
                class="transition-generic q-px-lg"
                v-on:click="store.setLanguage('en')"
              />

              <!-- FRANCESE -->
              <q-btn
                size="lg"
                :unelevated="store.language === 'fr'"
                :outline="store.language !== 'fr'"
                color="primary"
                label="Français"
                class="transition-generic q-px-lg"
                v-on:click="store.setLanguage('fr')"
              />
            </div>

            <div class="q-mt-xl">
              <q-btn
                size="lg"
                color="primary"
                :label="t.nav.continue"
                class="full-width"
                style="max-width: 300px"
                v-on:click="step = 2"
              />
            </div>
          </div>
        </div>
      </q-step>

      <!-- STEP 2: DOCUMENTI -->
      <q-step :name="2" :title="t.steps.docs" icon="badge" :done="step > 2">
        <div class="row justify-center">
          <StepDocuments
            v-on:next="step = 3"
            v-on:prev="step = 1"
            v-on:open-camera="openCamera"
          />
        </div>
      </q-step>

      <!-- STEP 3: CONTATTI -->
      <q-step :name="3" :title="t.steps.contact" icon="contact_phone" :done="step > 3">
        <div class="row justify-center">
          <div class="col-12 col-md-6">
            <q-form v-on:submit="step = 4">
              <div class="text-subtitle1 q-mb-md">{{ t.summary.contacts_title }}</div>
              <q-input
                v-model="store.contact.email"
                :label="t.person.email"
                type="email"
                outlined class="q-mb-md"
                :readonly="store.isEditMode"
                :rules="[val => !!val || t.errors.email_required, val => /.+@.+\..+/.test(val) || t.errors.email_invalid]"
              />
              <div class="row q-col-gutter-sm">
                <div class="col-4">
                  <q-select v-model="store.contact.prefix" :options="['+39', '+33', '+49', '+41', '+44', '+1']" :label="t.person.prefix" outlined :readonly="store.isEditMode" />
                </div>
                <div class="col-8">
                  <q-input v-model="store.contact.telefono" :label="t.person.phone" type="tel" outlined :readonly="store.isEditMode" :rules="[val => !!val || t.errors.required]" />
                </div>
              </div>
              <div class="row justify-end q-mt-lg q-gutter-sm">
                <q-btn flat :label="t.nav.back" v-on:click="step = 2" />
                <q-btn color="primary" :label="t.nav.continue" type="submit" />
              </div>
            </q-form>
          </div>
        </div>
      </q-step>

      <!-- STEP 4: PRIVACY -->
      <q-step :name="4" :title="t.steps.privacy" icon="gavel" :done="step > 4">
        <div class="row justify-center">
          <div class="col-12 col-md-8">
            <q-banner v-if="store.isEditMode" class="bg-green-1 q-mb-md rounded-borders">
              <q-icon name="check_circle" color="green" /> {{ t.privacy.already_accepted }}
            </q-banner>
            <q-banner v-else class="bg-indigo-1 q-mb-md rounded-borders text-body1">
              <q-icon name="info" color="primary" size="sm" class="q-mr-sm"/> <strong>{{ t.privacy.accept_for_all }}</strong>
            </q-banner>

            <q-card v-if="store.tutorParticipates || !store.hasMinors" bordered class="q-mb-lg" :class="store.guardian.ocrData.legal.isComplete ? 'bg-green-1' : 'bg-white'">
              <q-card-section class="row items-center justify-between">
                <div class="text-subtitle1 text-weight-bold">
                  <q-icon name="person" class="q-mr-xs"/> {{ store.hasMinors ? t.docs.guardian_card_title : t.summary.participant_title }}
                </div>
                <q-btn :color="store.guardian.ocrData.legal.isComplete ? 'positive' : 'primary'" :icon="store.guardian.ocrData.legal.isComplete ? 'check' : 'edit'" :label="t.steps.privacy" v-on:click="openLegalDialog(store.guardian.ocrData, t.privacy.adult_label, true)" />
              </q-card-section>
            </q-card>

            <div v-if="store.hasMinors">
              <div class="q-pa-md q-mb-lg rounded-borders shadow-1 transition-all" :class="canSync ? 'bg-white border-primary' : 'bg-grey-2 text-grey-6'">
                <q-checkbox v-model="syncWithTutor" @update:model-value="onSyncToggle" :disable="!canSync" :label="t.privacy.sync_tutor" color="green" />
              </div>
              <div v-for="(minor, idx) in store.minors" :key="minor.id" class="q-mb-md">
                  <q-card bordered :class="minor.ocrData.legal.isComplete ? 'bg-green-1' : 'bg-white'">
                  <q-card-section class="row items-center justify-between">
                    <div class="text-subtitle1 text-weight-bold"><q-icon name="child_care" class="q-mr-xs"/> {{ t.privacy.minor_label }} #{{ idx + 1 }}</div>
                    <q-btn :disable="syncWithTutor" :color="minor.ocrData.legal.isComplete ? 'positive' : 'primary'" icon="edit" :label="t.steps.privacy" v-on:click="openLegalDialog(minor.ocrData, `${t.privacy.minor_label} #${idx + 1}`, false)" />
                  </q-card-section>
                </q-card>
              </div>
            </div>

            <div class="row justify-end q-mt-lg q-gutter-sm">
              <q-btn flat :label="t.nav.back" v-on:click="step = 3" />
              <q-btn color="primary" :label="t.nav.continue" :disable="!allLegalCompleted" v-on:click="finalizeLegalStep" />
            </div>
          </div>
        </div>
      </q-step>

      <!-- STEP 5: REVIEW -->
      <q-step :name="5" :title="t.steps.review" icon="edit_note" :done="step > 5">
        <div v-if="loadingOcr" class="flex flex-center q-pa-xl">
          <q-spinner-dots size="3em" color="primary" />
          <div class="q-mt-md">{{ t.review.processing }}</div>
        </div>
        <StepReview v-else v-on:prev="step = 4" v-on:next="step = 6" />
      </q-step>

      <!-- STEP 6: SUMMARY -->
      <q-step :name="6" :title="t.steps.summary" icon="summarize">
        <div class="row justify-center">
          <div class="col-12 col-md-10">
            <div class="text-h5 q-mb-md text-center">{{ t.summary.title }}</div>
            <p class="text-grey-7 text-center q-mb-lg">{{ t.summary.subtitle }}</p>

            <q-card class="bg-blue-1 q-mb-md shadow-1">
              <q-item>
                <q-item-section avatar>
                  <q-avatar color="primary" text-color="white" icon="contact_mail" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">{{ t.summary.contacts_title }}</q-item-label>
                  <q-item-label caption class="text-black">
                    {{ store.contact.email }} <br>
                    {{ store.contact.prefix }} {{ store.contact.telefono }}
                  </q-item-label>
                </q-item-section>
              </q-item>
            </q-card>

            <div v-if="store.tutorParticipates || !store.hasMinors">
              <div class="text-subtitle2 text-grey-8 q-mb-sm q-mt-md">{{ store.hasMinors ? t.summary.tutor_title : t.summary.participant_title }}</div>
              <q-card bordered class="q-mb-md bg-white">
                <q-card-section class="q-pa-sm">
                  <q-list dense>
                    <q-item>
                      <q-item-section>
                        <q-item-label class="text-weight-bold">{{ store.guardian.ocrData.nome }} {{ store.guardian.ocrData.cognome }}</q-item-label>
                        <q-item-label caption>
                          {{ t.summary.born_on }} {{ store.guardian.ocrData.data_nascita }} {{ t.summary.born_at }} {{ store.guardian.ocrData.comune_nascita }} ({{ store.guardian.ocrData.stato_nascita }})
                        </q-item-label>
                        <q-item-label caption>
                          {{ t.summary.residing_at }} {{ store.guardian.ocrData.comune_residenza }} ({{ store.guardian.ocrData.stato_residenza }})
                        </q-item-label>
                      </q-item-section>
                    </q-item>
                    <q-separator spaced />
                    <q-item>
                      <q-item-section>
                        <q-item-label caption>{{ t.person.doc_type }}</q-item-label>
                        <q-item-label>{{ store.guardian.ocrData.tipo_documento }} {{ t.summary.doc_n }} {{ store.guardian.ocrData.numero_documento }}</q-item-label>
                        <q-item-label caption>{{ t.summary.expiry }}: {{ store.guardian.ocrData.scadenza_documento }}</q-item-label>
                      </q-item-section>
                      <q-item-section side>
                         <q-badge :color="store.guardian.ocrData.legal.isComplete ? 'green' : 'red'">{{ t.summary.consents_ok }}</q-badge>
                      </q-item-section>
                    </q-item>
                    <q-separator spaced />
                     <q-item>
                      <q-item-section>
                        <q-item-label caption>{{ t.summary.signature }}</q-item-label>
                        <img v-if="store.guardian.ocrData.signature" :src="store.guardian.ocrData.signature" style="max-height: 40px; max-width: 100px; object-fit: contain; border: 1px solid #eee;" />
                        <div v-else class="text-negative text-caption">{{ t.summary.missing }}</div>
                      </q-item-section>
                    </q-item>
                  </q-list>
                </q-card-section>
              </q-card>
            </div>

            <div v-if="store.hasMinors">
              <div class="text-subtitle2 text-grey-8 q-mb-sm q-mt-md">{{ t.summary.minors_title }}</div>
              <div v-for="(minor, idx) in store.minors" :key="idx">
                 <q-card bordered class="q-mb-sm bg-white">
                  <q-card-section class="q-pa-sm">
                    <q-list dense>
                      <q-item>
                        <q-item-section>
                          <q-item-label class="text-weight-bold">{{ minor.ocrData.nome }} {{ minor.ocrData.cognome }}</q-item-label>
                           <q-item-label caption>
                            {{ t.summary.born_on }} {{ minor.ocrData.data_nascita }}
                          </q-item-label>
                        </q-item-section>
                         <q-item-section side>
                           <q-chip size="sm" color="orange" text-color="white">{{ t.privacy.minor_label }} #{{ idx+1 }}</q-chip>
                        </q-item-section>
                      </q-item>
                       <q-item>
                        <q-item-section>
                          <q-item-label caption>{{ t.person.doc_type }}</q-item-label>
                          <q-item-label>{{ minor.ocrData.tipo_documento }} {{ t.summary.doc_n }} {{ minor.ocrData.numero_documento }}</q-item-label>
                        </q-item-section>
                      </q-item>
                      <q-separator spaced />
                       <q-item>
                        <q-item-section>
                          <q-item-label caption>{{ t.steps.privacy }}</q-item-label>
                          <div class="text-caption text-grey-8">
                            {{ t.summary.photo }}: <b>{{ minor.ocrData.legal.photoConsent ? t.summary.yes : t.summary.no }}</b> |
                            {{ t.summary.news }}: <b>{{ minor.ocrData.legal.newsletterConsent ? t.summary.yes : t.summary.no }}</b>
                          </div>
                        </q-item-section>
                      </q-item>
                    </q-list>
                  </q-card-section>
                 </q-card>
              </div>
            </div>

            <div class="row justify-between q-mt-xl">
              <q-btn flat :label="t.nav.back" v-on:click="step = 5" />
              <q-btn color="positive" size="lg" icon="check" :label="store.isEditMode ? t.nav.confirm_edit : t.nav.confirm" v-on:click="submitAll" :loading="submitting" />
            </div>
          </div>
        </div>
      </q-step>
    </q-stepper>

    <q-dialog v-model="cameraDialog.open" maximized transition-show="slide-up" transition-hide="slide-down">
      <q-card class="bg-black">
        <CameraCapture
          v-if="cameraDialog.open"
          :doc-type="cameraDialog.currentDocType"
          v-on:capture="onCameraCapture"
          v-on:close="cameraDialog.open = false"
        />
      </q-card>
    </q-dialog>

    <!-- LEGAL DIALOG -->
    <q-dialog v-model="legalDialog.open" persistent maximized transition-show="slide-up" transition-hide="slide-down">
      <q-card class="bg-grey-1">
        <q-toolbar class="bg-primary text-white">
          <q-toolbar-title>{{ t.steps.privacy }}: {{ legalDialog.title }}</q-toolbar-title>
          <q-btn flat round dense icon="close" v-close-popup />
        </q-toolbar>
        <q-card-section class="q-pa-md">
          <div class="row justify-center">
            <div class="col-12 col-md-8">
              <q-stepper v-model="legalDialog.step" vertical animated class="bg-white rounded-borders">
                <q-step :name="1" title="Privacy Policy" icon="policy" :done="currentLegalData.privacy">
                  <div class="legal-scroll" v-on:scroll="onDialogScroll('privacy', $event)">
                    <div class="text-body2">{{ currentLegalText.privacy }}</div>
                  </div>
                  <div class="row justify-end q-mt-md">
                    <q-btn color="primary" :label="t.privacy.read_and_accept" :disable="!legalDialog.unlocked.privacy && !store.isEditMode" v-on:click="currentLegalData.privacy = true; legalDialog.step = 2" />
                  </div>
                </q-step>
                <q-step :name="2" title="Consenso Informato / Informed Consent" icon="assignment" :done="currentLegalData.informedConsent">
                  <div class="legal-scroll" v-on:scroll="onDialogScroll('informed', $event)">
                    <div class="text-body2">{{ currentLegalText.informed }}</div>
                  </div>
                  <div class="row justify-end q-mt-md">
                    <q-btn color="primary" :label="t.privacy.read_and_accept" :disable="!legalDialog.unlocked.informed && !store.isEditMode" v-on:click="currentLegalData.informedConsent = true; legalDialog.step = 3" />
                  </div>
                </q-step>
                <q-step :name="3" :title="t.summary.photo" icon="photo_camera" :done="currentLegalData.photoConsent !== null">
                  <div class="q-pa-sm bg-grey-2 rounded-borders q-mb-md text-body2">{{ t.privacy.photo_consent_text }}</div>
                  <q-option-group v-model="currentLegalData.photoConsent" :options="yesNoOptions" type="radio" inline @update:model-value="v => { if(!v) photoWarningDialog = true }" />
                  <div class="row justify-end q-mt-md"><q-btn color="primary" :label="t.nav.confirm" :disable="currentLegalData.photoConsent === null" v-on:click="legalDialog.step = 4" /></div>
                </q-step>
                <q-step :name="4" :title="t.summary.news" icon="mail" :done="currentLegalData.newsletterConsent !== null">
                  <div class="q-pa-sm bg-grey-2 rounded-borders q-mb-md text-body2">{{ t.privacy.newsletter_text }}</div>
                  <q-option-group v-model="currentLegalData.newsletterConsent" :options="yesNoOptions" type="radio" inline />
                  <div class="row justify-end q-mt-md"><q-btn color="primary" :label="t.nav.close" :disable="currentLegalData.newsletterConsent === null" v-on:click="closeLegalDialog(true)" /></div>
                </q-step>
              </q-stepper>
            </div>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-dialog v-model="warningMismatchDialog.open">
      <q-card style="min-width: 350px">
        <q-card-section class="bg-orange-1 text-orange-9"><div class="text-h6"><q-icon name="warning" /> {{ t.dialogs.doc_check }}</div></q-card-section>
        <q-card-section>
          <ul class="q-pl-md"><li v-for="(warn, i) in warningMismatchDialog.messages" :key="i">{{ warn }}</li></ul>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat :label="t.nav.correct" color="primary" v-close-popup v-on:click="step = 2" />
          <q-btn unelevated :label="t.nav.ignore" color="orange" text-color="white" v-close-popup v-on:click="step = 5" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="photoWarningDialog" persistent>
      <q-card style="min-width: 300px">
        <q-card-section class="bg-warning text-white">
          <div class="text-h6"><q-icon name="warning" /> Attenzione</div>
        </q-card-section>

        <q-card-section class="q-pt-lg">
          Non dando il consenso nessuno potrà essere fotografato sul tuo gommone.
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Ho capito" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRegistrationStore } from 'stores/registration-store'
import { useQuasar } from 'quasar'
import { useRoute, useRouter } from 'vue-router'
import { api } from 'src/boot/axios'
import { translations } from 'src/constants/translations'
import { LEGAL_TEXTS } from 'src/constants/legal'
import CameraCapture from 'components/CameraCapture.vue'
import StepDocuments from 'components/scanner/steps/StepDocuments.vue'
import StepReview from 'components/scanner/steps/StepReview.vue'

// Init
const store = useRegistrationStore()
const $q = useQuasar()
const route = useRoute()
const router = useRouter()

// State
const step = ref(1)
const loadingData = ref(false)
const loadingOcr = ref(false)
const submitting = ref(false)
const syncWithTutor = ref(false)

const t = computed(() => translations[store.language] || translations.it)
const currentLegalText = computed(() => LEGAL_TEXTS[store.language] || LEGAL_TEXTS.it)

const yesNoOptions = computed(() => [
  {label: t.value.summary.yes, value: true},
  {label: t.value.summary.no, value: false}
])

// Dialogs
const photoWarningDialog = ref(false)
const warningMismatchDialog = reactive({ open: false, messages: [] })
const cameraDialog = reactive({ open: false, target: null, side: null, index: null, currentDocType: 'CIE' })
const legalDialog = reactive({ open: false, step: 1, title: '', targetRef: null, isGuardian: false, unlocked: { privacy: false, informed: false } })

const currentLegalData = computed(() => legalDialog.targetRef ? legalDialog.targetRef.legal : {})
const canSync = computed(() => store.guardian.ocrData.legal.isComplete)
const allLegalCompleted = computed(() => {
  if ((store.tutorParticipates || !store.hasMinors) && !store.guardian.ocrData.legal.isComplete) return false
  if (store.hasMinors && store.minors.some(m => !m.ocrData.legal.isComplete)) return false
  return true
})

// Lifecycle
onMounted(async () => {
  if (route.params.id) {
    loadingData.value = true
    try {
      await store.fetchRegistration(route.params.id)
      step.value = 4
    } catch (e) {
      console.error(e)
      $q.notify({ type: 'negative', message: t.value.errors.data_missing })
    } finally { loadingData.value = false }
  } else {
    store.resetStore()
  }
})

watch(() => store.hasMinors, (val) => { if (val && store.minors.length === 0) store.addMinor() })

// Camera Logic
function openCamera({ target, side, index }) {
  cameraDialog.target = target
  cameraDialog.side = side
  cameraDialog.index = index
  cameraDialog.currentDocType = (target === 'guardian') ? store.guardian.ocrData.tipo_documento : store.minors[index].ocrData.tipo_documento
  cameraDialog.open = true
}

function onCameraCapture(file) {
  cameraDialog.open = false
  if (cameraDialog.target === 'guardian') {
    if (cameraDialog.side === 'FRONT') store.guardian.frontFile = file
    if (cameraDialog.side === 'BACK') store.guardian.backFile = file
    store.startGuardianScan()
  } else {
    const idx = cameraDialog.index
    if (cameraDialog.side === 'FRONT') store.minors[idx].frontFile = file
    if (cameraDialog.side === 'BACK') store.minors[idx].backFile = file
    store.startMinorScan(idx)
  }
  $q.notify({ type: 'positive', message: t.value.dialogs.camera_analysis })
}

// Legal Logic
function openLegalDialog(personData, title, isGuardian) {
  legalDialog.targetRef = personData
  legalDialog.title = title
  legalDialog.isGuardian = isGuardian
  legalDialog.step = 1
  legalDialog.unlocked = { privacy: store.isEditMode, informed: store.isEditMode }
  legalDialog.open = true
}

function onDialogScroll(type, e) {
  const el = e.target
  if(el.scrollTop + el.clientHeight >= el.scrollHeight - 50) {
    if(type === 'privacy') legalDialog.unlocked.privacy = true
    if(type === 'informed') legalDialog.unlocked.informed = true
  }
}

function closeLegalDialog(complete) {
  if (complete && legalDialog.targetRef) {
    legalDialog.targetRef.legal.isComplete = true
    if (legalDialog.isGuardian && syncWithTutor.value) onSyncToggle(true)
  }
  legalDialog.open = false
}

function onSyncToggle(val) {
  if (val && store.guardian.ocrData.legal.isComplete) {
    store.minors.forEach(m => m.ocrData.legal = { ...store.guardian.ocrData.legal })
    $q.notify({ type: 'positive', message: t.value.privacy.consents_synced })
  }
}

async function finalizeLegalStep() {
  if (!store.isEditMode && !store.isManualMode) {
    loadingOcr.value = true
    try {
      await store.resolveAllOcr()
      const warnings = []
      if (store.guardian.ocrData.warning_mismatch) {
        const label = store.hasMinors ? t.value.dialogs.tutor_check : (t.value.dialogs.participant_check || t.value.dialogs.tutor_check)
        warnings.push(label)
      }
      store.minors.forEach((m, i) => { if (m.ocrData.warning_mismatch) warnings.push(`${t.value.dialogs.minor_check} ${i+1}: ${t.value.docs.mismatch_warning}`) })

      if (warnings.length > 0) {
        warningMismatchDialog.messages = warnings
        warningMismatchDialog.open = true
        return
      }
    } finally { loadingOcr.value = false }
  }
  step.value = 5
}

// Submission
function validatePerson(p, label) {
  const isItalian = (v) => v && (v.toUpperCase() === 'ITALIA' || v.toUpperCase() === 'IT')

  // Campi Base Sempre Obbligatori
  if (!p.nome || !p.cognome || !p.data_nascita || !p.tipo_documento || !p.numero_documento || !p.scadenza_documento) {
    return `${label}: ${t.value.errors.data_missing} (Campi base)`
  }
  if (!p.stato_nascita || !p.stato_residenza) {
     return `${label}: ${t.value.errors.data_missing} (Stato Nascita/Residenza)`
  }

  // Case A/B: Nato in Italia -> Comune Nascita obbligatorio
  if (isItalian(p.stato_nascita) && !p.comune_nascita) {
    return `${label}: Comune di nascita obbligatorio per nati in Italia`
  }

  // Case A/C: Residente in Italia -> Comune Res + CF obbligatori
  if (isItalian(p.stato_residenza)) {
    if (!p.comune_residenza) return `${label}: Comune di residenza obbligatorio`
    if (!p.codice_fiscale) return `${label}: Codice Fiscale obbligatorio`
  }

  if (!p.signature) return `${label}: ${t.value.errors.signature_missing}`
  return null
}

async function submitAll() {
  const errors = []
  if (store.tutorParticipates || !store.hasMinors) {
    const err = validatePerson(store.guardian.ocrData, store.hasMinors ? t.value.summary.tutor_title : t.value.summary.participant_title)
    if(err) errors.push(err)
  }
  store.minors.forEach((m, i) => {
    const err = validatePerson(m.ocrData, `${t.value.summary.minors_title} ${i+1}`)
    if(err) errors.push(err)
  })

  if (errors.length > 0) {
    $q.notify({ type: 'negative', message: errors[0] })
    return
  }

  submitting.value = true
  const finalContact = { email: store.contact.email, telefono: `${store.contact.prefix} ${store.contact.telefono}`.trim() }

  try {
    // 1. Gestione Adulto/Tutore
    if (store.tutorParticipates || !store.hasMinors) {
      const payload = {
        participant: {
          ...store.guardian.ocrData,
          legal: store.guardian.ocrData.legal
        },
        contact: finalContact,
        signatureBase64: store.guardian.ocrData.signature,
        is_minor: false,
        language: store.language,
        tutorParticipates: store.tutorParticipates,
        hasMinors: store.hasMinors,
        order_id: route.query.order_id || null
      }
      await api.post('/registration/submit', payload, {
        params: store.isEditMode ? { update_id: store.editRegistrationId } : {}
      })
    }

    // 2. Gestione Minori
    if (store.hasMinors) {
      for (const minor of store.minors) {
        const payload = {
          participant: {
            ...minor.ocrData,
            legal: minor.ocrData.legal
          },
          guardian: store.guardian.ocrData,
          contact: finalContact,
          // Se il minore non ha firmato, usa la firma del tutore
          signatureBase64: minor.ocrData.signature || store.guardian.ocrData.signature,
          is_minor: true,
          language: store.language,
          tutorParticipates: store.tutorParticipates,
          hasMinors: store.hasMinors,
          order_id: route.query.order_id || null
        }
        await api.post('/registration/submit', payload, {
          params: store.isEditMode ? { update_id: store.editRegistrationId } : {}
        })
      }
    }

    $q.notify({ type: 'positive', message: t.value.summary.success })
    router.push(store.isEditMode ? '/registrazioni' : '/')
  } catch(e) {
    console.error(e)
    const detail = e.response?.data?.detail
    $q.notify({ type: 'negative', message: typeof detail === 'string' ? detail : t.value.summary.error_submit })
  } finally { submitting.value = false }
}
</script>

<style scoped>
.legal-scroll {
  height: 200px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; background: #f9f9f9; white-space: pre-wrap;
}
.transition-all { transition: all 0.3s ease; }
.border-primary { border: 1px solid var(--q-primary); }
.border-orange { border: 1px solid var(--q-warning); }
</style>
