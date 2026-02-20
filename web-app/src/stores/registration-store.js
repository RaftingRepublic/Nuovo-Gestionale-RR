import { defineStore } from 'pinia'
import VisionService from 'src/services/VisionService'
import { api } from 'src/boot/axios'

// Helper per struttura dati persona vuota
const createEmptyPerson = (sourceType = 'MANUALE') => ({
  nome: '',
  cognome: '',
  data_nascita: '',

  // Geografici
  stato_nascita: 'ITALIA',
  comune_nascita: '',
  stato_residenza: 'ITALIA',
  comune_residenza: '',
  codice_fiscale: '',

  // Documento
  tipo_documento: 'CIE',
  numero_documento: '',
  scadenza_documento: '',

  // Fonte del dato (OCR_AUTO, MANUALE, CAMERA_SMART, ecc.)
  source: sourceType,

  // Dati di Debug e Warning
  debug: null,
  warning_mismatch: false,

  // Consensi SPECIFICI per questa persona
  legal: {
    privacy: false,
    informedConsent: false,
    tesseramento: false,
    photoConsent: null, // true/false/null
    newsletterConsent: null, // true/false/null
    isComplete: false // Helper flag
  },

  signature: null,
  // NUOVO: Dati vettoriali per FEA (Coordinate, Pressione, Tempo)
  signatureBiometrics: null
})

export const useRegistrationStore = defineStore('registration', {
  state: () => ({
    // Edit Mode State
    editRegistrationId: null, // Se popolato, siamo in modifica

    // Step 1
    language: 'it',

    // Step 2
    tutorParticipates: true,
    hasMinors: false,

    // Modalità di Input: 'SCAN' (Default) o 'MANUAL' (Fallback/Emergency)
    inputMode: 'SCAN',

    guardian: {
      frontFile: null,
      backFile: null,
      ocrData: createEmptyPerson('MANUALE'),
      ocrPromise: null,
      isAnalyzed: false
    },

    minors: [], // Array di oggetti { id, frontFile, backFile, ocrData: createEmptyPerson(), ... }

    // Step 3
    contact: {
      email: '',
      prefix: '+39',
      telefono: ''
    },

    // Global settings
    tesseramentoRequired: true,

    // Step 5 (Firma principale/tutore)
    signatureBase64: null
  }),

  getters: {
    isEditMode: (state) => !!state.editRegistrationId,
    isManualMode: (state) => state.inputMode === 'MANUAL'
  },

  actions: {
    setLanguage (lang) {
      // Supporto per IT, EN, FR
      const supported = ['it', 'en', 'fr']
      this.language = supported.includes(lang) ? lang : 'it'
    },

    /**
     * Imposta la modalità di inserimento.
     * Se MANUAL, inizializza i dati vuoti e bypassa le richieste di file.
     * Escape Hatch implementation.
     */
    setInputMode (mode) {
      this.inputMode = mode
      if (mode === 'MANUAL') {
        this.guardian.ocrData = createEmptyPerson('MANUALE')
        this.guardian.isAnalyzed = true // Consideriamo "analizzato" (skip OCR)
        // Reset file se presenti
        this.guardian.frontFile = null
        this.guardian.backFile = null
      } else {
        // Reset stato se torniamo a SCAN
        this.guardian.isAnalyzed = false
      }
    },

    addMinor () {
      if (this.minors.length >= 10) return
      // Se siamo in manual mode, il minore nasce già "analizzato" e manuale
      const isManual = this.inputMode === 'MANUAL'
      this.minors.push({
        id: Date.now(),
        frontFile: null,
        backFile: null,
        ocrData: createEmptyPerson(isManual ? 'MANUALE' : 'OCR_AUTO'),
        ocrPromise: null,
        isAnalyzed: isManual
      })
    },

    removeMinor (index) {
      this.minors.splice(index, 1)
    },

    resetGuardianScanState () {
      this.guardian.isAnalyzed = false
      this.guardian.ocrPromise = null
    },

    resetMinorScanState (index) {
      const minor = this.minors[index]
      if (!minor) return
      minor.isAnalyzed = false
      minor.ocrPromise = null
    },

    startGuardianScan () {
      if (!this.guardian.frontFile) return

      // Passiamo il tipo documento come hint
      const docHint = this.guardian.ocrData.tipo_documento || 'AUTO'

      this.guardian.ocrPromise = VisionService.analyzeDocument(
        this.guardian.frontFile,
        this.guardian.backFile,
        docHint
      ).then(data => {
        const mapped = this.mapOcrToForm(data)
        // Merge dati mantenendo legal esistente
        this.guardian.ocrData = {
          ...this.guardian.ocrData,
          ...mapped,
          source: 'OCR_HYBRID', // Tracciamo che viene dall'AI
          legal: this.guardian.ocrData.legal
        }
        this.guardian.isAnalyzed = true
        return data
      }).catch(err => {
        console.error('Errore background Guardian:', err)
      })
    },

    startMinorScan (index) {
      const minor = this.minors[index]
      if (!minor?.frontFile) return

      const docHint = minor.ocrData.tipo_documento || 'AUTO'

      minor.ocrPromise = VisionService.analyzeDocument(
        minor.frontFile,
        minor.backFile,
        docHint
      ).then(data => {
        const mapped = this.mapOcrToForm(data)
        minor.ocrData = {
          ...minor.ocrData,
          ...mapped,
          source: 'OCR_HYBRID',
          legal: minor.ocrData.legal
        }
        minor.isAnalyzed = true
        return data
      }).catch(err => {
        console.error('Errore background Minore:', err)
      })
    },

    mapOcrToForm (data) {
      if (!data || data.error) return {}

      // Logica di fallback cittadinanza (usata solo se il backend non è esplicito)
      const nat = (data.cittadinanza || data.mrz_nationality || '').toString().toUpperCase().trim()
      const isItalian = !nat || nat === 'ITA' || nat === 'IT' || nat === 'ITALIANA'

      return {
        nome: data.nome || '',
        cognome: data.cognome || '',
        data_nascita: data.data_nascita || '',

        // Mappatura esplicita backend o fallback
        stato_nascita: data.stato_nascita || (isItalian ? 'ITALIA' : (data.nazione_nascita || '')),
        stato_residenza: data.stato_residenza || (isItalian ? 'ITALIA' : ''),

        comune_nascita: data.comune_nascita || data.luogo_nascita || '',
        comune_residenza: data.comune_residenza || '',

        codice_fiscale: data.codice_fiscale || '',

        tipo_documento: data.tipo_documento || 'ALTRO',
        numero_documento: data.numero_documento || '',
        scadenza_documento: data.scadenza_documento || data.data_scadenza || '',

        source: data.source || 'OCR_AUTO',
        debug: data._debug_info || null,
        warning_mismatch: !!data.warning_mismatch
      }
    },

    async resolveAllOcr () {
      // Se siamo in manual mode, non c'è nulla da attendere
      if (this.inputMode === 'MANUAL') return

      const promises = []
      if (this.guardian.ocrPromise) promises.push(this.guardian.ocrPromise)
      this.minors.forEach(m => {
        if (m.ocrPromise) promises.push(m.ocrPromise)
      })
      await Promise.allSettled(promises)
    },

    // --- LOGICA EDIT MODE ---
    async fetchRegistration (id) {
      this.resetStore()
      this.editRegistrationId = id

      try {
        const res = await api.get(`/registration/details/${id}`)
        const data = res.data

        // 1. Setta Lingua e Contatti
        this.language = data.language || 'it'
        if (data.contact) {
          this.contact.email = data.contact.email || ''
          this.contact.telefono = data.contact.telefono || ''
          // Gestione prefisso basic se presente nel numero
          if (this.contact.telefono.startsWith('+')) {
            this.contact.prefix = this.contact.telefono.substring(0, 3)
            this.contact.telefono = this.contact.telefono.substring(3)
          }
        }

        // Helper per mappare i dati anagrafici nel form
        const mapPersonData = (source) => {
          const empty = createEmptyPerson(source.source || 'DB_FETCH')
          if (!source) return empty

          // Mappatura diretta campi
          const dest = { ...empty, ...source }

          // Mappatura sub-oggetti geografici (gestione retrocompatibilità)
          if (source.italian) {
            dest.comune_nascita = source.italian.comune_nascita || source.comune_nascita
            dest.comune_residenza = source.italian.comune_residenza || source.comune_residenza
            dest.codice_fiscale = source.italian.codice_fiscale || source.codice_fiscale
          }

          // Mappatura Consensi:
          const oldLegal = source.legal_consents || source.legal || {}
          dest.legal = {
            privacy: true, // Pre-accettato
            informedConsent: true, // Pre-accettato
            tesseramento: true,
            photoConsent: oldLegal.photo,
            newsletterConsent: oldLegal.newsletter,
            isComplete: false // Forziamo l'utente a confermare
          }

          return dest
        }

        // 2. Popolamento Persone
        const isMinorReg = data.is_minor || false

        if (!isMinorReg) {
          // Caso Adulto
          this.tutorParticipates = true
          this.hasMinors = false
          this.guardian.ocrData = mapPersonData(data.participant)
          this.guardian.isAnalyzed = true // Evita OCR
        } else {
          // Caso Minore
          this.hasMinors = true
          this.tutorParticipates = data.tutor_participates // Dovrebbe venire dal payload

          // Popola Tutore
          if (data.guardian) {
            this.guardian.ocrData = mapPersonData(data.guardian)
            this.guardian.isAnalyzed = true
          }

          // Popola Minore
          this.addMinor()
          this.minors[0].ocrData = mapPersonData(data.participant)
          this.minors[0].isAnalyzed = true
        }

      } catch (e) {
        console.error("Errore fetch registration", e)
        throw e
      }
    },

    resetStore () {
      this.$reset()
      // Assicuriamoci che inputMode torni al default
      this.inputMode = 'SCAN'
    }
  }
})