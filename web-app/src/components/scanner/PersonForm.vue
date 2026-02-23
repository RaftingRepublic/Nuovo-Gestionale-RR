<template>
  <div class="row q-col-gutter-sm">
    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- GRUPPO 1: Dati Anagrafici Base (sempre visibili)        -->
    <!-- ═══════════════════════════════════════════════════════ -->

    <!-- Nome -->
    <div class="col-12 col-md-6">
      <q-input
        :model-value="modelValue.nome"
        v-on:update:model-value="v => update('nome', v)"
        :label="t.person.name"
        outlined dense :readonly="readonly"
        :rules="[val => !!val || t.errors.required]"
      />
    </div>

    <!-- Cognome -->
    <div class="col-12 col-md-6">
      <q-input
        :model-value="modelValue.cognome"
        v-on:update:model-value="v => update('cognome', v)"
        :label="t.person.surname"
        outlined dense :readonly="readonly"
        :rules="[val => !!val || t.errors.required]"
      />
    </div>

    <!-- Data di Nascita -->
    <div class="col-12 col-md-4">
      <q-input
        :model-value="modelValue.data_nascita"
        v-on:update:model-value="v => update('data_nascita', v)"
        :label="t.person.birth_date"
        outlined dense :readonly="readonly"
        mask="##/##/####"
        :rules="[val => /^\d{2}\/\d{2}\/\d{4}$/.test(val) || t.errors.format_date]"
      >
        <template v-slot:append v-if="!readonly">
          <q-icon name="event" class="cursor-pointer">
            <q-popup-proxy cover transition-show="scale" transition-hide="scale">
              <q-date :model-value="modelValue.data_nascita" v-on:update:model-value="v => update('data_nascita', v)" mask="DD/MM/YYYY" />
            </q-popup-proxy>
          </q-icon>
        </template>
      </q-input>
    </div>

    <!-- Sesso -->
    <div class="col-12 col-md-2">
      <q-select
        :model-value="modelValue.sesso"
        v-on:update:model-value="v => update('sesso', v)"
        :options="['M', 'F']"
        label="Sesso *"
        outlined dense
        :readonly="readonly"
        :rules="[val => !!val || 'Campo obbligatorio']"
      />
    </div>

    <!-- Età (auto-calcolata, readonly) -->
    <div class="col-12 col-md-2">
      <q-input :model-value="age" :label="t.person.age" outlined dense readonly bg-color="grey-2" />
    </div>

    <!-- Stato di Nascita -->
    <div class="col-12 col-md-6">
      <q-select
        :model-value="modelValue.stato_nascita"
        v-on:update:model-value="v => update('stato_nascita', v)"
        :options="optsStatoNascita"
        :label="t.person.birth_country"
        outlined dense
        :readonly="readonly"
        use-input
        fill-input
        hide-selected
        input-debounce="0"
        @filter="filterStatoNascita"
        behavior="menu"
      >
        <template v-slot:no-option>
          <q-item><q-item-section class="text-grey">Nessun risultato</q-item-section></q-item>
        </template>
      </q-select>
    </div>

    <!-- Stato di Residenza -->
    <div class="col-12 col-md-6">
      <q-select
        :model-value="modelValue.stato_residenza"
        v-on:update:model-value="v => update('stato_residenza', v)"
        :options="optsStatoResidenza"
        :label="t.person.residence_country"
        outlined dense
        :readonly="readonly"
        use-input
        fill-input
        hide-selected
        input-debounce="0"
        @filter="filterStatoResidenza"
        behavior="menu"
      />
    </div>

    <!-- ═══════════════════════════════════════════════════════ -->
    <!-- GRUPPO 2: Campi condizionali e Documento                -->
    <!-- ═══════════════════════════════════════════════════════ -->

    <!-- Separatore visivo -->
    <div class="col-12">
      <q-separator class="q-my-xs" />
    </div>

    <!-- Comune di Nascita: Visibile solo se Nato in Italia (Caso A, B) -->
    <div v-if="isItalian(modelValue.stato_nascita)" class="col-12 col-md-6">
      <q-select
        :model-value="modelValue.comune_nascita"
        v-on:update:model-value="v => update('comune_nascita', v)"
        :options="optsComuneNascita"
        :label="t.person.birth_city"
        outlined dense
        :readonly="readonly"
        use-input
        fill-input
        hide-selected
        input-debounce="0"
        @filter="filterComuneNascita"
      >
        <template v-slot:no-option>
          <q-item><q-item-section class="text-grey">Nessun comune trovato</q-item-section></q-item>
        </template>
      </q-select>
    </div>

    <!-- Comune Residenza: Visibile solo se Residente in Italia (Caso A, C) -->
    <div v-if="isItalian(modelValue.stato_residenza)" class="col-12 col-md-6">
      <q-select
        :model-value="modelValue.comune_residenza"
        v-on:update:model-value="v => update('comune_residenza', v)"
        :options="optsComuneResidenza"
        :label="t.person.residence_city"
        outlined dense
        :readonly="readonly"
        use-input
        fill-input
        hide-selected
        input-debounce="0"
        @filter="filterComuneResidenza"
      >
        <template v-slot:no-option>
          <q-item><q-item-section class="text-grey">Nessun comune trovato</q-item-section></q-item>
        </template>
      </q-select>
    </div>

    <!-- Tipo Documento -->
    <div class="col-12 col-md-4">
      <q-select
        :model-value="modelValue.tipo_documento"
        v-on:update:model-value="v => update('tipo_documento', v)"
        :options="docTypeOptions"
        :label="t.person.doc_type"
        outlined dense
        :readonly="readonly"
        emit-value
        map-options
      />
    </div>

    <!-- Numero Documento -->
    <div class="col-12 col-md-4">
      <q-input
        :model-value="modelValue.numero_documento"
        v-on:update:model-value="v => update('numero_documento', v)"
        :label="t.person.doc_number"
        outlined dense :readonly="readonly"
        :rules="[val => !!val && val.length >= 2 || t.errors.min_chars]"
      />
    </div>

    <!-- Scadenza Documento -->
    <div class="col-12 col-md-4">
      <q-input
        :model-value="modelValue.scadenza_documento"
        v-on:update:model-value="v => update('scadenza_documento', v)"
        :label="t.person.doc_expiry"
        outlined dense :readonly="readonly"
        mask="##/##/####"
        :rules="[val => /^\d{2}\/\d{2}\/\d{4}$/.test(val) || t.errors.format_date]"
      >
        <template v-slot:append v-if="!readonly">
          <q-icon name="event" class="cursor-pointer">
            <q-popup-proxy cover transition-show="scale" transition-hide="scale">
              <q-date :model-value="modelValue.scadenza_documento" v-on:update:model-value="v => update('scadenza_documento', v)" mask="DD/MM/YYYY" />
            </q-popup-proxy>
          </q-icon>
        </template>
      </q-input>
    </div>

    <!-- Codice Fiscale: Visibile solo se Nato in Italia -->
    <div v-if="isItalianBorn" class="col-12">
      <q-input
        :model-value="modelValue.codice_fiscale"
        v-on:update:model-value="v => update('codice_fiscale', v.toUpperCase())"
        :label="t.person.fiscal_code"
        outlined dense :readonly="readonly"
        mask="AAAAAA##A##A###A"
        :rules="isItalianBorn ? [val => (val && val.length === 16) || t.errors.format_cf] : []"
      >
        <template v-slot:append v-if="!readonly">
          <q-btn round dense flat icon="auto_fix_high" color="primary" @click="calcCF" title="Calcola C.F. in automatico" />
        </template>
      </q-input>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useQuasar } from 'quasar'
import CodiceFiscale from 'codice-fiscale-js'
import { useRegistrationStore } from 'stores/registration-store'
import { translations } from 'src/constants/translations'
import { ALL_COUNTRIES, ALL_MUNICIPALITIES } from 'src/constants/geoData'

const props = defineProps(['modelValue', 'isAdult', 'readonly'])
const emit = defineEmits(['update:modelValue'])

const store = useRegistrationStore()
const $q = useQuasar()
const t = computed(() => translations[store.language] || translations.it)

// Helper: estrae stringa sicura da q-select (che può emettere {label,value} o stringa)
const getStr = (val) => (typeof val === 'object' && val !== null) ? (val.label || val.value || '') : String(val || '')

// Computed: nato in Italia?
const isItalianBorn = computed(() => {
  const s = getStr(props.modelValue.stato_nascita).toUpperCase().trim()
  return s === 'ITALIA' || s === 'IT'
})

// --- Opzioni Tipo Documento ---
const docTypeOptions = [
  { label: 'CIE', value: 'CIE' },
  { label: 'Passaporto', value: 'PASSAPORTO' },
  { label: 'Patente', value: 'PATENTE' },
  { label: 'Altro', value: 'ALTRO' }
]

// --- Filtri Autocomplete ---
const optsStatoNascita = ref(ALL_COUNTRIES)
const optsStatoResidenza = ref(ALL_COUNTRIES)
const optsComuneNascita = ref(ALL_MUNICIPALITIES)
const optsComuneResidenza = ref(ALL_MUNICIPALITIES)

// Helper per filtro case-insensitive
function filterFn (val, update, optionsRef, sourceList) {
  if (val === '') {
    update(() => { optionsRef.value = sourceList })
    return
  }
  update(() => {
    const needle = val.toLowerCase()
    optionsRef.value = sourceList.filter(v => v.toLowerCase().indexOf(needle) > -1)
  })
}

function filterStatoNascita (val, update) { filterFn(val, update, optsStatoNascita, ALL_COUNTRIES) }
function filterStatoResidenza (val, update) { filterFn(val, update, optsStatoResidenza, ALL_COUNTRIES) }
function filterComuneNascita (val, update) { filterFn(val, update, optsComuneNascita, ALL_MUNICIPALITIES) }
function filterComuneResidenza (val, update) { filterFn(val, update, optsComuneResidenza, ALL_MUNICIPALITIES) }

function isItalian(val) {
  return val && (val.toUpperCase() === 'ITALIA' || val.toUpperCase() === 'IT')
}

// --- LOGICA AUTO-MATCHING POTENZIATA ---
function findBestMatch(rawVal, list) {
  if (!rawVal) return rawVal

  const normalize = (str) => {
    return str
      .toUpperCase()
      .replace(/\(.*\)/g, '')
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/[^A-Z0-9]/g, '')
  }

  const searchKey = normalize(rawVal.toString())
  const found = list.find(item => normalize(item) === searchKey)

  return found || rawVal
}

watch(() => props.modelValue.comune_nascita, (newVal) => {
  if (isItalian(props.modelValue.stato_nascita)) {
    const match = findBestMatch(newVal, ALL_MUNICIPALITIES)
    if (match !== newVal) update('comune_nascita', match)
  }
})

watch(() => props.modelValue.comune_residenza, (newVal) => {
  if (isItalian(props.modelValue.stato_residenza)) {
    const match = findBestMatch(newVal, ALL_MUNICIPALITIES)
    if (match !== newVal) update('comune_residenza', match)
  }
})

watch(() => props.modelValue.stato_nascita, (newVal) => {
  const match = findBestMatch(newVal, ALL_COUNTRIES)
  if (match !== newVal) update('stato_nascita', match)
})

watch(() => props.modelValue.stato_residenza, (newVal) => {
  const match = findBestMatch(newVal, ALL_COUNTRIES)
  if (match !== newVal) update('stato_residenza', match)
})

const age = computed(() => {
  const d = props.modelValue
  if (!d.data_nascita || d.data_nascita.length !== 10) return '-'
  const parts = d.data_nascita.split('/')
  if(parts.length !== 3) return '-'
  const birth = new Date(parts[2], parts[1]-1, parts[0])
  const now = new Date()
  let a = now.getFullYear() - birth.getFullYear()
  const m = now.getMonth() - birth.getMonth()
  if (m < 0 || (m === 0 && now.getDate() < birth.getDate())) a--
  return a
})

function update(field, value) {
  if (props.modelValue[field] === value) return
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}

// ─── AUTO-CALCOLO CODICE FISCALE ─────────────────────────
function calcCF() {
  const d = props.modelValue
  if (!d.nome || !d.cognome || !d.data_nascita || !d.sesso || !d.comune_nascita) {
    $q.notify({ color: 'warning', message: 'Compila Nome, Cognome, Data di nascita, Sesso e Comune di nascita prima di calcolare il CF.', position: 'top' })
    return
  }
  try {
    // Estrazione safe da q-select objects
    const rawComune = getStr(d.comune_nascita)
    const cleanComune = rawComune.split('/')[0].split('(')[0].trim().toUpperCase()
    const sesso = getStr(d.sesso).charAt(0).toUpperCase()
    const dateStr = getStr(d.data_nascita)

    // Parsing data: gestisce YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY
    const parts = dateStr.split(/[-/]/)
    if (parts.length !== 3) throw new Error('Formato data non valido')
    let day, month, year
    if (parts[0].length === 4) {
      // Formato YYYY-MM-DD (q-date HTML5)
      year = parseInt(parts[0], 10)
      month = parseInt(parts[1], 10)
      day = parseInt(parts[2], 10)
    } else {
      // Formato DD/MM/YYYY o DD-MM-YYYY
      day = parseInt(parts[0], 10)
      month = parseInt(parts[1], 10)
      year = parseInt(parts[2], 10)
    }

    const cf = new CodiceFiscale({
      name: getStr(d.nome),
      surname: getStr(d.cognome),
      gender: sesso,
      day: day,
      month: month,
      year: year,
      birthplace: cleanComune
    })
    update('codice_fiscale', cf.code)
    $q.notify({ type: 'positive', message: `CF calcolato: ${cf.code}`, position: 'top', timeout: 3000 })
  } catch (e) {
    console.error('Errore calcolo CF:', e)
    $q.notify({ color: 'negative', message: 'Errore C.F.: Controllare dati o Comune (' + e.message + ')', position: 'top', timeout: 5000 })
  }
}
</script>
