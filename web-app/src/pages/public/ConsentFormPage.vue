<template>
  <q-page class="q-pa-md bg-grey-1">
    <div class="text-h4 q-mb-md text-primary text-weight-bold text-center">
      Consenso Informato
    </div>

    <q-stepper
      v-model="step"
      ref="stepperRef"
      color="primary"
      animated
      alternative-labels
      header-nav
      class="shadow-2 rounded-borders"
    >

      <!-- ═══════════════════════════════════════════════════════ -->
      <!-- STEP 1: LINGUA                                         -->
      <!-- ═══════════════════════════════════════════════════════ -->
      <q-step :name="1" :title="t.steps.lang" icon="translate" :done="step > 1">
        <div class="row justify-center text-center">
          <div class="col-12 col-md-8">
            <div class="text-h6 q-mb-lg">Scegli la lingua / Choose language</div>

            <div class="row q-gutter-md justify-center">
              <q-btn
                size="lg"
                :unelevated="store.language === 'it'"
                :outline="store.language !== 'it'"
                color="primary"
                label="Italiano"
                class="q-px-lg"
                @click="store.setLanguage('it')"
              />
              <q-btn
                size="lg"
                :unelevated="store.language === 'en'"
                :outline="store.language !== 'en'"
                color="primary"
                label="English"
                class="q-px-lg"
                @click="store.setLanguage('en')"
              />
              <q-btn
                size="lg"
                :unelevated="store.language === 'fr'"
                :outline="store.language !== 'fr'"
                color="primary"
                label="Français"
                class="q-px-lg"
                @click="store.setLanguage('fr')"
              />
            </div>

            <div class="q-mt-xl">
              <q-btn
                size="lg" color="primary" :label="t.nav.continue"
                class="full-width" style="max-width: 300px"
                @click="step = 2"
              />
            </div>
          </div>
        </div>
      </q-step>

      <!-- ═══════════════════════════════════════════════════════ -->
      <!-- STEP 2: DOCUMENTI                                      -->
      <!-- ═══════════════════════════════════════════════════════ -->
      <q-step :name="2" :title="t.steps.docs" icon="badge" :done="step > 2">
        <div class="row justify-center">
          <StepDocuments
            @next="step = 3"
            @prev="step = 1"
            @open-camera="openCamera"
          />
        </div>
      </q-step>

      <!-- ═══════════════════════════════════════════════════════ -->
      <!-- STEP 3: CONTATTI                                       -->
      <!-- ═══════════════════════════════════════════════════════ -->
      <q-step :name="3" :title="t.steps.contact" icon="contact_phone" :done="step > 3">
        <div class="row justify-center">
          <div class="col-12 col-md-6">
            <q-form @submit="step = 4">
              <div class="text-subtitle1 q-mb-md">{{ t.summary.contacts_title }}</div>
              <q-input
                v-model="store.contact.email"
                :label="t.person.email"
                type="email"
                outlined class="q-mb-md"
                :rules="[val => !!val || t.errors.email_required, val => /.+@.+\..+/.test(val) || t.errors.email_invalid]"
              />
              <div class="row q-col-gutter-sm">
                <div class="col-4">
                  <q-select v-model="store.contact.prefix" :options="['+39', '+33', '+49', '+41', '+44', '+1']" :label="t.person.prefix" outlined />
                </div>
                <div class="col-8">
                  <q-input v-model="store.contact.telefono" :label="t.person.phone" type="tel" outlined :rules="[val => !!val || t.errors.required]" />
                </div>
              </div>
              <div class="row justify-end q-mt-lg q-gutter-sm">
                <q-btn flat :label="t.nav.back" @click="step = 2" />
                <q-btn color="primary" :label="t.nav.continue" type="submit" />
              </div>
            </q-form>
          </div>
        </div>
      </q-step>

      <!-- ═══════════════════════════════════════════════════════ -->
      <!-- STEP 4: PRIVACY                                        -->
      <!-- ═══════════════════════════════════════════════════════ -->
      <q-step :name="4" :title="t.steps.privacy" icon="gavel" :done="step > 4">
        <div class="row justify-center">
          <div class="col-12 col-md-8">
            <!-- Cantiere 3: Hero banner con info discesa dal Magic Link -->
            <div v-if="orderInfo" class="q-pa-md q-mb-md rounded-borders bg-blue-1" style="border-left: 4px solid var(--q-primary);">
              <div class="text-subtitle1 text-primary text-weight-bold">
                <q-icon name="water" class="q-mr-xs" />
                In riferimento alla discesa {{ orderInfo.activity_name }} del {{ orderInfo.date }} alle {{ orderInfo.time }}
              </div>
            </div>
            <q-banner class="bg-indigo-1 q-mb-md rounded-borders text-body1">
              <q-icon name="info" color="primary" size="sm" class="q-mr-sm"/> <strong>{{ t.privacy.accept_for_all }}</strong>
            </q-banner>

            <!-- Card Adulto/Tutore -->
            <q-card v-if="store.tutorParticipates || !store.hasMinors" bordered class="q-mb-lg" :class="store.guardian.ocrData.legal.isComplete ? 'bg-green-1' : 'bg-white'">
              <q-card-section class="row items-center justify-between">
                <div class="text-subtitle1 text-weight-bold">
                  <q-icon name="person" class="q-mr-xs"/> {{ store.hasMinors ? t.docs.guardian_card_title : t.summary.participant_title }}
                </div>
                <q-btn :color="store.guardian.ocrData.legal.isComplete ? 'positive' : 'primary'" :icon="store.guardian.ocrData.legal.isComplete ? 'check' : 'edit'" :label="t.steps.privacy" @click="openLegalDialog(store.guardian.ocrData, t.privacy.adult_label, true)" />
              </q-card-section>
            </q-card>

            <!-- Sync + Minori -->
            <div v-if="store.hasMinors">
              <div class="q-pa-md q-mb-lg rounded-borders shadow-1 transition-all" :class="canSync ? 'bg-white border-primary' : 'bg-grey-2 text-grey-6'">
                <q-checkbox v-model="syncWithTutor" @update:model-value="onSyncToggle" :disable="!canSync" :label="t.privacy.sync_tutor" color="green" />
              </div>
              <div v-for="(minor, idx) in store.minors" :key="minor.id" class="q-mb-md">
                <q-card bordered :class="minor.ocrData.legal.isComplete ? 'bg-green-1' : 'bg-white'">
                  <q-card-section class="row items-center justify-between">
                    <div class="text-subtitle1 text-weight-bold"><q-icon name="child_care" class="q-mr-xs"/> {{ t.privacy.minor_label }} #{{ idx + 1 }}</div>
                    <q-btn :disable="syncWithTutor" :color="minor.ocrData.legal.isComplete ? 'positive' : 'primary'" icon="edit" :label="t.steps.privacy" @click="openLegalDialog(minor.ocrData, `${t.privacy.minor_label} #${idx + 1}`, false)" />
                  </q-card-section>
                </q-card>
              </div>
            </div>

            <div class="row justify-end q-mt-lg q-gutter-sm">
              <q-btn flat :label="t.nav.back" @click="step = 3" />
              <q-btn color="primary" :label="t.nav.continue" :disable="!allLegalCompleted" @click="finalizeLegalStep" />
            </div>
          </div>
        </div>
      </q-step>

      <!-- ═══════════════════════════════════════════════════════ -->
      <!-- STEP 5: VERIFICA & FIRMA (con invio integrato)         -->
      <!-- ═══════════════════════════════════════════════════════ -->
      <q-step :name="5" :title="t.steps.review" icon="edit_note" :done="step > 5">
        <!-- Form Review + Firma + Invio (i dati sono già pre-compilati dall'OCR allo Step 2) -->
        <StepReview @prev="step = 4" @next="onSubmitSuccess" />
      </q-step>

      <!-- ═══════════════════════════════════════════════════════ -->
      <!-- STEP 6: CONFERMA COMPLETAMENTO                         -->
      <!-- ═══════════════════════════════════════════════════════ -->
      <q-step :name="6" :title="t.steps.summary" icon="check_circle">
        <div class="row justify-center">
          <div class="col-12 col-md-8 text-center">
            <q-icon name="check_circle" color="positive" size="80px" class="q-mb-lg" />
            <div class="text-h4 text-positive q-mb-md">{{ t.summary.success }}</div>
            <p v-if="orderId" class="text-grey-7 text-body1 q-mb-xl">
              Consenso registrato! Puoi passare il telefono al prossimo partecipante del gruppo.
            </p>
            <p v-else class="text-grey-7 text-body1 q-mb-xl">Registrazione completata con successo. Puoi chiudere questa pagina o registrare un nuovo partecipante.</p>
            <q-btn
              color="primary"
              size="lg"
              :icon="orderId ? 'group_add' : 'person_add'"
              :label="orderId ? 'Prossimo Partecipante' : 'Nuova Registrazione'"
              @click="startNewRegistration"
              class="q-px-xl"
            />
          </div>
        </div>
      </q-step>

    </q-stepper>

    <!-- ═══════ DIALOG: CAMERA (dal ScannerPage originale) ═══════ -->
    <q-dialog v-model="cameraDialog.open" maximized transition-show="slide-up" transition-hide="slide-down">
      <q-card class="bg-black">
        <CameraCapture
          v-if="cameraDialog.open"
          :doc-type="cameraDialog.currentDocType"
          @capture="onCameraCapture"
          @close="cameraDialog.open = false"
        />
      </q-card>
    </q-dialog>

    <!-- ═══════ DIALOG: PRIVACY/LEGAL ═══════ -->
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
                <!-- Privacy Policy -->
                <q-step :name="1" title="Privacy Policy" icon="policy" :done="currentLegalData.privacy">
                  <div class="legal-scroll" @scroll="onDialogScroll('privacy', $event)">
                    <div class="text-body2">{{ currentLegalText.privacy }}</div>
                  </div>
                  <div class="row justify-end q-mt-md">
                    <q-btn color="primary" :label="t.privacy.read_and_accept" :disable="!legalDialog.unlocked.privacy" @click="currentLegalData.privacy = true; legalDialog.step = 2" />
                  </div>
                </q-step>
                <!-- Consenso Informato -->
                <q-step :name="2" title="Consenso Informato / Informed Consent" icon="assignment" :done="currentLegalData.informedConsent">
                  <div class="legal-scroll" @scroll="onDialogScroll('informed', $event)">
                    <div class="text-body2">{{ currentLegalText.informed }}</div>
                  </div>
                  <div class="row justify-end q-mt-md">
                    <q-btn color="primary" :label="t.privacy.read_and_accept" :disable="!legalDialog.unlocked.informed" @click="currentLegalData.informedConsent = true; legalDialog.step = 3" />
                  </div>
                </q-step>
                <!-- Consenso Foto -->
                <q-step :name="3" :title="t.summary.photo" icon="photo_camera" :done="currentLegalData.photoConsent !== null">
                  <div class="q-pa-sm bg-grey-2 rounded-borders q-mb-md text-body2">{{ t.privacy.photo_consent_text }}</div>
                  <q-option-group v-model="currentLegalData.photoConsent" :options="yesNoOptions" type="radio" inline @update:model-value="v => { if(!v) photoWarningDialog = true }" />
                  <div class="row justify-end q-mt-md"><q-btn color="primary" :label="t.nav.confirm" :disable="currentLegalData.photoConsent === null" @click="legalDialog.step = 4" /></div>
                </q-step>
                <!-- Newsletter -->
                <q-step :name="4" :title="t.summary.news" icon="mail" :done="currentLegalData.newsletterConsent !== null">
                  <div class="q-pa-sm bg-grey-2 rounded-borders q-mb-md text-body2">{{ t.privacy.newsletter_text }}</div>
                  <q-option-group v-model="currentLegalData.newsletterConsent" :options="yesNoOptions" type="radio" inline />
                  <div class="row justify-end q-mt-md"><q-btn color="primary" :label="t.nav.close" :disable="currentLegalData.newsletterConsent === null" @click="closeLegalDialog(true)" /></div>
                </q-step>
              </q-stepper>
            </div>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- ═══════ DIALOG: Mismatch Warning ═══════ -->
    <q-dialog v-model="warningMismatchDialog.open">
      <q-card style="min-width: 350px">
        <q-card-section class="bg-orange-1 text-orange-9"><div class="text-h6"><q-icon name="warning" /> {{ t.dialogs.doc_check }}</div></q-card-section>
        <q-card-section>
          <ul class="q-pl-md"><li v-for="(warn, i) in warningMismatchDialog.messages" :key="i">{{ warn }}</li></ul>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat :label="t.nav.correct" color="primary" v-close-popup @click="step = 2" />
          <q-btn unelevated :label="t.nav.ignore" color="orange" text-color="white" v-close-popup @click="step = 5" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- ═══════ DIALOG: Photo Warning ═══════ -->
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
import { useRoute } from 'vue-router'
import { useRegistrationStore } from 'stores/registration-store'
import { useQuasar } from 'quasar'
import { supabase } from 'src/supabase'
import { translations } from 'src/constants/translations'
import { LEGAL_TEXTS } from 'src/constants/legal'
import CameraCapture from 'components/CameraCapture.vue'
import StepDocuments from 'components/scanner/steps/StepDocuments.vue'
import StepReview from 'components/scanner/steps/StepReview.vue'

// Init
const route = useRoute()
const store = useRegistrationStore()
const $q = useQuasar()

// Cantiere 3: Magic Link (Auto-Slotting)
const orderId = computed(() => route.query.order_id || null)
const orderInfo = ref(null)

// State
const step = ref(1)
// loadingOcr rimosso: l'attesa OCR ora avviene in StepDocuments (Step 2)
const syncWithTutor = ref(false)
const stepperRef = ref(null)

const t = computed(() => translations[store.language] || translations.it)
const currentLegalText = computed(() => LEGAL_TEXTS[store.language] || LEGAL_TEXTS.it)

const yesNoOptions = computed(() => [
  { label: t.value.summary.yes, value: true },
  { label: t.value.summary.no, value: false }
])

// Mobile Photo rimosso: la scansione avviene ora interamente allo Step 2

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
  store.resetStore()
  // Cantiere 3: se c'è order_id, carica info discesa direttamente da Supabase
  if (orderId.value) {
    try {
      const { data, error } = await supabase
        .from('orders')
        .select('*, rides(date, time, activities(name))')
        .eq('id', orderId.value)
        .single()
      if (data && !error) {
        orderInfo.value = {
          activity_name: data.rides?.activities?.name || 'Discesa',
          date: data.rides?.date || '',
          time: data.rides?.time ? data.rides.time.substring(0, 5) : ''
        }
      } else {
        console.error('Ordine non trovato in Supabase:', error)
        $q.notify({ type: 'negative', message: 'Link non valido o ordine non trovato.', position: 'top' })
      }
    } catch (e) {
      console.error('Errore caricamento info ordine da Supabase:', e)
      $q.notify({ type: 'negative', message: 'Errore nel caricamento dell\'ordine.', position: 'top' })
    }
  }
})

watch(() => store.hasMinors, (val) => { if (val && store.minors.length === 0) store.addMinor() })

// Compressione e upload immagini rimossi: gestiti in StepDocuments (Step 2)

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
  legalDialog.unlocked = { privacy: false, informed: false }
  legalDialog.open = true
}

function onDialogScroll(type, e) {
  const el = e.target
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 50) {
    if (type === 'privacy') legalDialog.unlocked.privacy = true
    if (type === 'informed') legalDialog.unlocked.informed = true
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

function finalizeLegalStep() {
  // L'OCR è già stato completato allo Step 2, qui controlliamo solo i warning
  if (!store.isManualMode) {
    const warnings = []
    if (store.guardian.ocrData.warning_mismatch) {
      // Mostra "Tutore" solo se ci sono minori, altrimenti "Partecipante"
      const label = store.hasMinors ? t.value.dialogs.tutor_check : (t.value.dialogs.participant_check || t.value.dialogs.tutor_check)
      warnings.push(label)
    }
    store.minors.forEach((m, i) => { if (m.ocrData.warning_mismatch) warnings.push(`${t.value.dialogs.minor_check} ${i + 1}: ${t.value.docs.mismatch_warning}`) })

    if (warnings.length > 0) {
      warningMismatchDialog.messages = warnings
      warningMismatchDialog.open = true
      return
    }
  }
  step.value = 5
}

// ── Gestione Successo Invio (chiamata da StepReview) ──
async function onSubmitSuccess () {
  // Cantiere 3.12: aggiorna participant slot in Supabase direttamente
  if (orderId.value) {
    try {
      const fullName = `${store.guardian.ocrData.nome || ''} ${store.guardian.ocrData.cognome || ''}`.trim()

      // Trova il primo slot EMPTY per questo ordine
      const { data: slots } = await supabase
        .from('participants')
        .select('*')
        .eq('order_id', orderId.value)
        .eq('status', 'EMPTY')
        .order('created_at', { ascending: true })
        .limit(1)

      if (slots && slots.length > 0) {
        await supabase.from('participants').update({
          name: fullName || 'Partecipante',
          email: store.contact.email || '',
          is_privacy_signed: true,
          status: 'COMPLETED'
        }).eq('id', slots[0].id)
        console.log(`[SlotConsumption] Aggiornato partecipante ${slots[0].id} per ordine ${orderId.value}`)
      }

      $q.notify({ type: 'positive', message: 'Consenso registrato con successo!', icon: 'check_circle', position: 'top' })
    } catch (e) {
      console.error('[SlotConsumption] Errore aggiornamento partecipante:', e)
      $q.notify({ type: 'negative', message: 'Errore durante il salvataggio del consenso.', position: 'top', timeout: 6000 })
      return // Non avanzare allo step 6
    }
  }
  step.value = 6
}

function startNewRegistration () {
  store.resetStore()
  step.value = 1
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
