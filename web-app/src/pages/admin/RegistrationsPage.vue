<template>
  <q-page class="registrations-page q-pa-md">
    <!-- HEADER -->
    <div class="row items-center q-col-gutter-sm q-mb-lg">
      <div class="col">
        <div class="text-h5 text-weight-bold text-grey-9">
          <q-icon name="folder_shared" class="q-mr-sm" color="primary" size="sm" />
          Archivio Consensi
        </div>
        <div class="text-caption text-grey-6">
          Elenco dei consensi informati ricevuti dal Kiosk. Puoi visualizzare il PDF firmato per ciascun partecipante.
        </div>
      </div>

      <div class="col-12 col-sm-auto">
        <q-input
          v-model="filter"
          dense
          outlined
          debounce="300"
          placeholder="Cerca nome, email, telefono..."
          clearable
          class="search-input"
        >
          <template #prepend><q-icon name="search" /></template>
        </q-input>
      </div>

      <div class="col-auto">
        <q-btn
          outline
          icon="refresh"
          label="Aggiorna"
          :loading="loading"
          @click="load"
          color="primary"
        />
      </div>
    </div>

    <!-- STATS BADGES -->
    <div class="row q-gutter-sm q-mb-md">
      <q-badge color="primary" class="q-pa-sm text-body2">
        <q-icon name="people" class="q-mr-xs" /> Totale: {{ rows.length }}
      </q-badge>
      <q-badge color="green-7" class="q-pa-sm text-body2">
        <q-icon name="person" class="q-mr-xs" /> Adulti: {{ adultsCount }}
      </q-badge>
      <q-badge color="orange-7" class="q-pa-sm text-body2">
        <q-icon name="child_care" class="q-mr-xs" /> Minori: {{ minorsCount }}
      </q-badge>
    </div>

    <!-- TABLE -->
    <q-table
      :rows="filteredRows"
      :columns="columns"
      row-key="registration_id"
      :loading="loading"
      :pagination="pagination"
      @update:pagination="val => pagination = val"
      flat
      bordered
      separator="horizontal"
      class="registrations-table"
      :rows-per-page-options="[10, 20, 50, 100]"
      no-data-label="Nessuna registrazione trovata"
      loading-label="Caricamento in corso..."
    >
      <!-- Data/Ora -->
      <template #body-cell-timestamp_iso="props">
        <q-td :props="props">
          <div class="text-body2 text-weight-medium">{{ formatDate(props.value) }}</div>
          <div class="text-caption text-grey-6">{{ formatTime(props.value) }}</div>
        </q-td>
      </template>

      <!-- Nominativo -->
      <template #body-cell-nominativo="props">
        <q-td :props="props">
          <div class="text-body2 text-weight-bold text-grey-9">
            {{ props.row.participant_cognome }} {{ props.row.participant_nome }}
          </div>
        </q-td>
      </template>

      <!-- Contatti -->
      <template #body-cell-contatti="props">
        <q-td :props="props">
          <div v-if="props.row.email" class="text-body2">
            <q-icon name="email" size="xs" color="grey-6" class="q-mr-xs" />
            {{ props.row.email }}
          </div>
          <div v-if="props.row.telefono" class="text-caption text-grey-7">
            <q-icon name="phone" size="xs" color="grey-6" class="q-mr-xs" />
            {{ props.row.telefono }}
          </div>
        </q-td>
      </template>

      <!-- Tipo (Adulto/Minore) -->
      <template #body-cell-tipo="props">
        <q-td :props="props" class="text-center">
          <q-chip
            :color="props.row.is_minor ? 'orange-2' : 'green-2'"
            :text-color="props.row.is_minor ? 'orange-9' : 'green-9'"
            size="sm"
            dense
            :icon="props.row.is_minor ? 'child_care' : 'person'"
          >
            {{ props.row.is_minor ? 'Minore' : 'Adulto' }}
          </q-chip>
        </q-td>
      </template>

      <!-- Lock status -->
      <template #body-cell-locked="props">
        <q-td :props="props" class="text-center">
          <q-toggle
            :model-value="props.row.locked"
            @update:model-value="val => onToggleLock(props.row, val)"
            checked-icon="lock"
            unchecked-icon="lock_open"
            color="red-5"
          />
        </q-td>
      </template>

      <!-- Azioni -->
      <template #body-cell-actions="props">
        <q-td :props="props" class="text-right">
          <q-btn
            dense
            flat
            round
            icon="picture_as_pdf"
            color="negative"
            @click="openPdf(props.row.registration_id)"
          >
            <q-tooltip>Apri PDF firmato</q-tooltip>
          </q-btn>
          <q-btn
            dense
            flat
            round
            icon="visibility"
            color="primary"
            @click="openDetails(props.row)"
          >
            <q-tooltip>Dettagli &amp; Storico</q-tooltip>
          </q-btn>
          <q-btn
            dense
            flat
            round
            icon="edit"
            color="grey-7"
            @click="editRegistration(props.row.registration_id)"
          >
            <q-tooltip>Modifica Registrazione</q-tooltip>
          </q-btn>
        </q-td>
      </template>
    </q-table>

    <!-- DETAILS DIALOG -->
    <q-dialog v-model="detailsOpen" persistent>
      <q-card style="min-width: 550px; max-width: 95vw;">
        <q-card-section class="row items-center bg-primary text-white">
          <q-icon name="info" class="q-mr-sm" />
          <div class="text-h6">Dettagli Registrazione</div>
          <q-space />
          <q-btn flat round dense icon="close" color="white" v-close-popup />
        </q-card-section>

        <q-separator />

        <q-card-section v-if="loadingDetails" class="flex flex-center" style="min-height: 200px">
          <q-spinner-dots size="3em" color="primary" />
        </q-card-section>

        <q-card-section v-else-if="detailsFull">
          <div class="row q-col-gutter-md q-mb-lg">
            <div class="col-12 col-sm-6">
              <div class="text-caption text-grey-7">ID Registrazione</div>
              <div class="text-body2 text-weight-bold text-primary text-break">{{ detailsFull.registration_id }}</div>
            </div>
            <div class="col-12 col-sm-6">
              <div class="text-caption text-grey-7">Ultima Modifica</div>
              <div class="text-body2">{{ formatFull(detailsFull.timestamp_iso) }}</div>
            </div>

            <div class="col-12">
              <div class="text-caption text-grey-7">Partecipante</div>
              <div class="text-body1">
                {{ getPersonName(detailsFull.participant) }}
                <span v-if="detailsFull.contact?.email" class="text-grey-7 text-caption">({{ detailsFull.contact.email }})</span>
              </div>
            </div>
          </div>

          <div class="row q-gutter-sm q-mb-lg">
            <q-btn outline icon="edit" label="Modifica" color="primary" @click="editRegistration(detailsFull.registration_id)" />
            <q-btn outline icon="picture_as_pdf" label="Apri PDF" color="negative" @click="openPdf(detailsFull.registration_id)" />
          </div>

          <q-separator class="q-my-md" />

          <div class="text-subtitle1 text-weight-bold q-mb-md text-grey-8">
            <q-icon name="history" /> Storico Modifiche
          </div>

          <div v-if="!detailsFull.audit_log || detailsFull.audit_log.length === 0" class="text-grey-6 text-center q-pa-md">
            Nessuna modifica registrata.
          </div>

          <q-timeline v-else color="secondary">
            <q-timeline-entry
              v-for="(log, idx) in detailsFull.audit_log"
              :key="idx"
              :title="translateAction(log.action)"
              :subtitle="formatFull(log.iso_date)"
              :icon="getActionIcon(log.action)"
              :color="getActionColor(log.action)"
            >
              <div class="text-grey-8">
                {{ log.details || 'Nessun dettaglio' }}
              </div>
            </q-timeline-entry>
          </q-timeline>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from 'src/boot/axios'
import { useQuasar } from 'quasar'
import { useRouter } from 'vue-router'

const $q = useQuasar()
const router = useRouter()

const loading = ref(false)
const rows = ref([])
const filter = ref('')

const detailsOpen = ref(false)
const loadingDetails = ref(false)
const detailsFull = ref(null)

const pagination = ref({
  sortBy: 'timestamp_iso',
  descending: true,
  rowsPerPage: 20
})

// Computed stats
const adultsCount = computed(() => rows.value.filter(r => !r.is_minor).length)
const minorsCount = computed(() => rows.value.filter(r => r.is_minor).length)

const columns = [
  {
    name: 'timestamp_iso',
    label: 'Data / Ora',
    field: 'timestamp_iso',
    sortable: true,
    align: 'left',
    style: 'width: 140px'
  },
  {
    name: 'nominativo',
    label: 'Nominativo',
    field: row => `${row.participant_cognome || ''} ${row.participant_nome || ''}`.trim(),
    sortable: true,
    align: 'left'
  },
  {
    name: 'contatti',
    label: 'Contatti',
    field: 'email',
    sortable: true,
    align: 'left'
  },
  {
    name: 'tipo',
    label: 'Tipo',
    field: 'is_minor',
    sortable: true,
    align: 'center',
    style: 'width: 100px'
  },
  {
    name: 'locked',
    label: 'Bloccata',
    field: 'locked',
    align: 'center',
    style: 'width: 90px'
  },
  {
    name: 'actions',
    label: 'Azioni',
    field: 'actions',
    align: 'right',
    style: 'width: 140px'
  }
]

// Date formatting helpers
function formatDate (iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function formatTime (iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
}

function formatFull (iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('it-IT')
}

// Filter
const filteredRows = computed(() => {
  const q = (filter.value || '').trim().toLowerCase()
  if (!q) return rows.value
  return rows.value.filter(r => {
    const hay = [r.registration_id, r.participant_nome, r.participant_cognome, r.email, r.telefono]
      .map(x => (x || '').toString().toLowerCase()).join(' ')
    return hay.includes(q)
  })
})

// Data loading
async function load () {
  loading.value = true
  try {
    const res = await api.get('/registration/list', { params: { limit: 1000 } })
    rows.value = res.data?.items || []
  } catch (e) {
    console.error(e)
    $q.notify({ type: 'negative', message: 'Impossibile caricare le registrazioni' })
  } finally {
    loading.value = false
  }
}

// Actions
function openPdf (registrationId) {
  const url = api.getUri({ url: `/registration/${registrationId}/pdf` })
  window.open(url, '_blank')
}

async function openDetails (row) {
  detailsOpen.value = true
  loadingDetails.value = true
  detailsFull.value = null

  try {
    const res = await api.get(`/registration/details/${row.registration_id}`)
    detailsFull.value = res.data
  } catch (e) {
    console.error('Err caricamento dettagli:', e)
    $q.notify({ type: 'negative', message: 'Errore caricamento dettagli' })
    detailsOpen.value = false
  } finally {
    loadingDetails.value = false
  }
}

function editRegistration (registrationId) {
  router.push(`/admin/scanner/${registrationId}`)
}

async function onToggleLock (row, locked) {
  const prev = !locked
  try {
    await api.post(`/registration/${row.registration_id}/lock`, { locked })
    row.locked = locked
    $q.notify({ type: 'positive', message: locked ? 'Registrazione bloccata' : 'Registrazione sbloccata' })
  } catch (e) {
    console.error(e)
    row.locked = prev
    $q.notify({ type: 'negative', message: 'Errore aggiornando il blocco' })
  }
}

// Helpers
function getPersonName (p) {
  if (!p) return 'Sconosciuto'
  return `${p.nome || ''} ${p.cognome || ''}`.trim()
}

function translateAction (action) {
  const map = {
    CREATE: 'Registrazione Creata',
    UPDATE: 'Modifica Dati',
    EMAIL_SENT: 'Email Inviata',
    EMAIL_ERROR: 'Errore Email',
    LOCK_CHANGE: 'Stato Blocco Modificato',
    BIO_ERROR: 'Errore Biometria'
  }
  return map[action] || action
}

function getActionIcon (action) {
  if (action === 'CREATE') return 'add_circle'
  if (action === 'UPDATE') return 'edit'
  if (action === 'EMAIL_SENT') return 'mail'
  if (action === 'EMAIL_ERROR') return 'error'
  if (action === 'LOCK_CHANGE') return 'lock'
  if (action === 'BIO_ERROR') return 'warning'
  return 'info'
}

function getActionColor (action) {
  if (action === 'CREATE') return 'green'
  if (action === 'UPDATE') return 'orange'
  if (action === 'EMAIL_SENT') return 'blue'
  if (action === 'EMAIL_ERROR') return 'red'
  if (action === 'LOCK_CHANGE') return 'grey-8'
  if (action === 'BIO_ERROR') return 'deep-orange'
  return 'grey'
}

onMounted(load)
</script>

<style scoped>
.registrations-page {
  max-width: 1200px;
  margin: 0 auto;
}

.search-input {
  min-width: 280px;
}

.registrations-table :deep(.q-table__top) {
  padding: 8px 16px;
}

.registrations-table :deep(thead th) {
  font-weight: 700;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #546e7a;
}

.registrations-table :deep(tbody td) {
  padding-top: 10px;
  padding-bottom: 10px;
}

.text-break {
  word-break: break-all;
}
</style>
