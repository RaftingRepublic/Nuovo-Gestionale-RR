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

    <!-- Codice Fiscale: Visibile solo se Residente in Italia (Caso A, C) -->
    <div v-if="isItalian(modelValue.stato_residenza)" class="col-12">
      <q-input 
        :model-value="modelValue.codice_fiscale" 
        v-on:update:model-value="v => update('codice_fiscale', v.toUpperCase())"
        :label="t.person.fiscal_code" 
        outlined dense :readonly="readonly"
        mask="AAAAAA##A##A###A"
        :rules="[val => val.length === 16 || t.errors.format_cf]"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRegistrationStore } from 'stores/registration-store'
import { translations } from 'src/constants/translations'
import { ALL_COUNTRIES, ALL_MUNICIPALITIES } from 'src/constants/geoData'

const props = defineProps(['modelValue', 'isAdult', 'readonly'])
const emit = defineEmits(['update:modelValue'])

const store = useRegistrationStore()
const t = computed(() => translations[store.language] || translations.it)

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
</script>