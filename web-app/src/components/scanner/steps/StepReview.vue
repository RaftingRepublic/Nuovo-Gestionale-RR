<template>
  <div class="row q-col-gutter-lg">
    <!-- ═══ Banner Modalità Modifica ═══ -->
    <div class="col-12" v-if="store.isEditMode">
      <q-banner class="bg-warning text-dark q-mb-md">
        <q-icon name="lock" /> <strong>{{ t.review.edit_warning }}</strong>
      </q-banner>
    </div>

    <!-- ═══ Card Adulto/Tutore ═══ -->
    <div class="col-12" v-if="store.tutorParticipates || !store.hasMinors">
      <q-card bordered class="shadow-1">
        <q-card-section class="bg-primary text-white">
          <div class="text-h6">{{ store.hasMinors ? 'Tutore' : 'Partecipante' }}</div>
        </q-card-section>
        <q-card-section>
          <PersonForm
            v-model="store.guardian.ocrData"
            :is-adult="true"
            :readonly="store.isEditMode"
          />
        </q-card-section>
      </q-card>
    </div>

    <!-- ═══ Card Minori ═══ -->
    <div v-if="store.hasMinors" class="col-12">
      <div v-for="(minor, idx) in store.minors" :key="minor.id" class="q-mb-md">
        <q-card bordered class="shadow-1">
          <q-card-section class="bg-secondary text-white">
            <div class="text-h6">Minore #{{ idx + 1 }}</div>
          </q-card-section>
          <q-card-section>
             <PersonForm
              v-model="minor.ocrData"
              :is-adult="false"
              :readonly="store.isEditMode"
            />
            <div class="q-mt-md">
              <div class="text-subtitle2 q-mb-sm">{{ t.review.minor_sig_title }} #{{ idx + 1 }}</div>
              <SignaturePad
                v-model="minor.ocrData.signature"
                @update:biometrics="(val) => minor.ocrData.signatureBiometrics = val"
                :ref="el => { if (el) minorSigRefs[idx] = el }"
              />
              <!-- ═══ Anteprima Firma Minore (Reattiva) ═══ -->
              <div class="q-mt-xs row items-center q-gutter-sm">
                <template v-if="minor.ocrData.signature">
                  <q-badge color="positive" class="q-pa-xs">
                    <q-icon name="check" size="xs" class="q-mr-xs" /> Acquisita
                  </q-badge>
                  <img
                    :src="minor.ocrData.signature"
                    style="max-height: 60px; object-fit: contain; background: #fff; border: 1px solid #ccc; border-radius: 4px; padding: 4px;"
                    alt="Anteprima Firma"
                  />
                </template>
                <div v-else class="text-negative text-caption text-weight-bold">
                  <q-icon name="warning" size="xs" class="q-mr-xs" />{{ t.summary.signature }}: {{ t.summary.missing }}
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- ═══ Firma Principale (Tutore/Partecipante) ═══ -->
    <div class="col-12" v-if="store.tutorParticipates || !store.hasMinors">
      <q-card bordered class="bg-grey-1">
        <q-card-section>
          <div class="text-subtitle1 text-weight-bold">{{ t.review.main_sig_title }}</div>
          <div class="text-caption text-grey-7 q-mb-sm">{{ t.review.main_sig_desc }}</div>
          <SignaturePad
            ref="mainSigRef"
            v-model="store.guardian.ocrData.signature"
            @update:biometrics="(val) => store.guardian.ocrData.signatureBiometrics = val"
          />
          <!-- ═══ Anteprima Firma Principale (Reattiva) ═══ -->
          <div class="q-mt-xs row items-center q-gutter-sm">
            <template v-if="store.guardian.ocrData.signature">
              <q-badge color="positive" class="q-pa-xs">
                <q-icon name="check" size="xs" class="q-mr-xs" /> Acquisita
              </q-badge>
              <img
                :src="store.guardian.ocrData.signature"
                style="max-height: 60px; object-fit: contain; background: #fff; border: 1px solid #ccc; border-radius: 4px; padding: 4px;"
                alt="Anteprima Firma"
              />
            </template>
            <div v-else class="text-negative text-caption text-weight-bold">
              <q-icon name="warning" size="xs" class="q-mr-xs" />{{ t.summary.signature }}: {{ t.summary.missing }}
            </div>
          </div>
        </q-card-section>
      </q-card>
    </div>

    <!-- ═══ Bottoni Navigazione + Submit ═══ -->
    <div class="col-12 row justify-between q-mt-lg">
      <q-btn flat :label="t.nav.back" v-on:click="$emit('prev')" />
      <q-btn
        color="positive"
        size="lg"
        icon="check"
        :label="t.nav.confirm"
        @click="handleSubmit"
        :loading="submitting"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { useRegistrationStore } from 'stores/registration-store'
import { useQuasar } from 'quasar'
import { api } from 'src/boot/axios'
import { translations } from 'src/constants/translations'
import PersonForm from '../PersonForm.vue'
import SignaturePad from '../SignaturePad.vue'

defineEmits(['next', 'prev'])

const route = useRoute()
const store = useRegistrationStore()
const $q = useQuasar()
const t = computed(() => translations[store.language] || translations.it)

// Cantiere 6.3: order_id dalla URL per Slot Consumption
const currentOrderId = computed(() => route.query.order_id || null)

// ── Refs per la firma ──
const mainSigRef = ref(null)
const minorSigRefs = reactive({})
const submitting = ref(false)



// ── Validazione Persona ──
function validatePerson (p, label) {
  const isItalian = (v) => v && (v.toUpperCase() === 'ITALIA' || v.toUpperCase() === 'IT')

  if (!p.nome || !p.cognome || !p.data_nascita || !p.tipo_documento || !p.numero_documento || !p.scadenza_documento) {
    return `${label}: ${t.value.errors.data_missing} (Campi base)`
  }
  if (!p.stato_nascita || !p.stato_residenza) {
    return `${label}: ${t.value.errors.data_missing} (Stato Nascita/Residenza)`
  }
  if (isItalian(p.stato_nascita) && !p.comune_nascita) {
    return `${label}: Comune di nascita obbligatorio per nati in Italia`
  }
  if (isItalian(p.stato_residenza)) {
    if (!p.comune_residenza) return `${label}: Comune di residenza obbligatorio`
    if (!p.codice_fiscale) return `${label}: Codice Fiscale obbligatorio`
  }
  return null
}

/**
 * Gestisce il flusso di invio:
 * 1. Valida che la firma principale NON sia vuota
 * 2. Valida che tutte le firme dei minori NON siano vuote
 * 3. Estrae la firma in Base64
 * 4. Costruisce il payload consolidato
 * 5. POST al backend — successo SOLO se il server risponde 2xx
 */
async function handleSubmit () {
  // ── 1. VALIDAZIONE FIRMA PRINCIPALE ──
  if (store.tutorParticipates || !store.hasMinors) {
    const sigPadInstance = mainSigRef.value
    if (!sigPadInstance || sigPadInstance.isEmpty()) {
      $q.notify({
        type: 'negative',
        icon: 'draw',
        message: t.value.errors.signature_missing,
        caption: 'La firma è obbligatoria per procedere.',
        position: 'top',
        timeout: 4000
      })
      return
    }
  }

  // Validazione firme minori
  if (store.hasMinors) {
    for (let i = 0; i < store.minors.length; i++) {
      const minorSig = minorSigRefs[i]
      if (!minorSig || minorSig.isEmpty()) {
        $q.notify({
          type: 'negative',
          icon: 'draw',
          message: `${t.value.review.minor_sig_title} #${i + 1}: ${t.value.errors.signature_missing}`,
          position: 'top',
          timeout: 4000
        })
        return
      }
    }
  }

  // ── 2. VALIDAZIONE DATI ANAGRAFICI ──
  const errors = []
  if (store.tutorParticipates || !store.hasMinors) {
    const err = validatePerson(store.guardian.ocrData, store.hasMinors ? t.value.summary.tutor_title : t.value.summary.participant_title)
    if (err) errors.push(err)
  }
  store.minors.forEach((m, i) => {
    const err = validatePerson(m.ocrData, `${t.value.summary.minors_title} ${i + 1}`)
    if (err) errors.push(err)
  })

  if (errors.length > 0) {
    $q.notify({ type: 'negative', message: errors[0], position: 'top', timeout: 4000 })
    return
  }

  // ── 3. ESTRAI FIRMA BASE64 ──
  const guardianSignatureBase64 = mainSigRef.value
    ? mainSigRef.value.getImage()
    : store.guardian.ocrData.signature

  // ── 4. COSTRUZIONE PAYLOAD & INVIO ──
  submitting.value = true
  $q.loading.show({ message: 'Invio registrazione in corso...' })

  // Flag per tracciare successo reale (solo dopo risposta 2xx dal server)
  let submitSucceeded = false

  const finalContact = {
    email: store.contact.email,
    telefono: `${store.contact.prefix} ${store.contact.telefono}`.trim()
  }

  try {
    // 4a. Gestione Adulto/Tutore
    if (store.tutorParticipates || !store.hasMinors) {
      const payload = {
        participant: {
          nome: store.guardian.ocrData.nome,
          cognome: store.guardian.ocrData.cognome,
          data_nascita: store.guardian.ocrData.data_nascita,
          stato_nascita: store.guardian.ocrData.stato_nascita,
          comune_nascita: store.guardian.ocrData.comune_nascita,
          stato_residenza: store.guardian.ocrData.stato_residenza,
          comune_residenza: store.guardian.ocrData.comune_residenza,
          codice_fiscale: store.guardian.ocrData.codice_fiscale,
          tipo_documento: store.guardian.ocrData.tipo_documento,
          numero_documento: store.guardian.ocrData.numero_documento,
          scadenza_documento: store.guardian.ocrData.scadenza_documento,
          legal: { ...store.guardian.ocrData.legal }
        },
        contact: finalContact,
        signature_base64: guardianSignatureBase64,
        signature_biometrics: store.guardian.ocrData.signatureBiometrics || null,
        is_minor: false,
        language: store.language,
        tutorParticipates: store.tutorParticipates,
        hasMinors: store.hasMinors,
        // Cantiere 6.3: collega al desk order per Slot Consumption
        order_id: currentOrderId.value
      }

      console.log('PAYLOAD INVIATO (Adulto/Tutore):', payload)
      const response = await api.post('/registration/submit', payload)

      // Verifica esplicita: solo 2xx è successo
      if (!response || response.status < 200 || response.status >= 300) {
        throw new Error(`Risposta inattesa dal server: HTTP ${response?.status}`)
      }
    }

    // 4b. Gestione Minori
    if (store.hasMinors) {
      for (let i = 0; i < store.minors.length; i++) {
        const minor = store.minors[i]
        const minorSig = minorSigRefs[i]
        const minorSignatureBase64 = minorSig
          ? minorSig.getImage()
          : (minor.ocrData.signature || guardianSignatureBase64)

        const payload = {
          participant: {
            nome: minor.ocrData.nome,
            cognome: minor.ocrData.cognome,
            data_nascita: minor.ocrData.data_nascita,
            stato_nascita: minor.ocrData.stato_nascita,
            comune_nascita: minor.ocrData.comune_nascita,
            stato_residenza: minor.ocrData.stato_residenza,
            comune_residenza: minor.ocrData.comune_residenza,
            codice_fiscale: minor.ocrData.codice_fiscale,
            tipo_documento: minor.ocrData.tipo_documento,
            numero_documento: minor.ocrData.numero_documento,
            scadenza_documento: minor.ocrData.scadenza_documento,
            legal: { ...minor.ocrData.legal }
          },
          guardian: {
            nome: store.guardian.ocrData.nome,
            cognome: store.guardian.ocrData.cognome,
            codice_fiscale: store.guardian.ocrData.codice_fiscale,
            numero_documento: store.guardian.ocrData.numero_documento
          },
          contact: finalContact,
          signature_base64: minorSignatureBase64,
          signature_biometrics: minor.ocrData.signatureBiometrics || null,
          is_minor: true,
          language: store.language,
          tutorParticipates: store.tutorParticipates,
          hasMinors: store.hasMinors,
          // Cantiere 6.3: collega al desk order per Slot Consumption
          order_id: currentOrderId.value
        }

        console.log(`PAYLOAD INVIATO (Minore #${i + 1}):`, payload)
        const response = await api.post('/registration/submit', payload)

        if (!response || response.status < 200 || response.status >= 300) {
          throw new Error(`Risposta inattesa dal server per minore #${i + 1}: HTTP ${response?.status}`)
        }
      }
    }

    // ── 5. SUCCESSO CONFERMATO DAL SERVER ──
    // Arriviamo qui SOLO se tutte le api.post() hanno restituito 2xx
    submitSucceeded = true

  } catch (e) {
    // ── ERRORE: Connessione fallita o risposta non-2xx ──
    console.error('Errore invio registrazione:', e)

    const detail = e.response?.data?.detail
    const statusCode = e.response?.status

    let errorMessage = 'Errore di connessione al server o salvataggio fallito.'
    if (typeof detail === 'string') {
      errorMessage = detail
    } else if (Array.isArray(detail)) {
      // Pydantic 422 validation errors
      errorMessage = detail.map(d => d.msg || JSON.stringify(d)).join('; ')
    } else if (statusCode === 404) {
      errorMessage = 'Endpoint non ancora implementato (404). Il payload è stato loggato in console.'
    } else if (statusCode === 422) {
      errorMessage = 'Dati non validi. Verifica i campi obbligatori.'
    } else if (statusCode >= 500) {
      errorMessage = 'Errore interno del server. Riprova più tardi.'
    } else if (!e.response) {
      errorMessage = 'Impossibile contattare il server. Verifica la connessione.'
    }

    $q.notify({
      type: 'negative',
      icon: 'error',
      message: errorMessage,
      position: 'top',
      timeout: 6000
    })
  } finally {
    // Nascondi sempre loading e spinner, sia su successo che errore
    $q.loading.hide()
    submitting.value = false
  }

  // ── POST-FINALLY: Azioni di successo SOLO se il server ha confermato ──
  // Questo blocco è FUORI dal try/catch/finally, quindi eseguito solo
  // se submitSucceeded è stato impostato a true (tutte le POST 2xx)
  if (submitSucceeded) {
    $q.dialog({
      title: 'Fatto!',
      message: 'Registrazione completata con successo.',
      color: 'positive',
      persistent: true
    }).onOk(() => {
      // RESET KIOSK: Ricarica brutalmente la pagina per svuotare la RAM,
      // lo store Pinia e riportare il tablet allo Step 1,
      // pronto e pulito per il cliente successivo.
      window.location.reload()
    })
  }
}
</script>
