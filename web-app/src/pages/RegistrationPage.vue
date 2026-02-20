<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-col-gutter-sm q-mb-md">
      <div class="col">
        <div class="text-h5 text-weight-bold">Registrazioni</div>
        <div class="text-caption text-grey-7">
          Elenco registrazioni inviate (payload + PDF). In futuro verranno collegate alle prenotazioni.
        </div>
      </div>

      <div class="col-12 col-sm-auto">
        <q-input v-model="filter" dense outlined debounce="250" placeholder="Cerca nome, email, ID..." clearable>
          <template #prepend><q-icon name="search" /></template>
        </q-input>
      </div>

      <div class="col-12 col-sm-auto">
        <q-btn outline icon="refresh" label="Aggiorna" :loading="loading" @click="load" />
      </div>
    </div>

    <q-table
      :rows="filteredRows"
      :columns="columns"
      row-key="registration_id"
      :loading="loading"
      :pagination="pagination"
      flat
      bordered
    >
      <template #body-cell-is_minor="props">
        <q-td :props="props" class="text-center">
          <q-badge :color="props.value ? 'orange' : 'green'" rounded>
            {{ props.value ? 'Sì' : 'No' }}
          </q-badge>
        </q-td>
      </template>

      <template #body-cell-locked="props">
        <q-td :props="props" class="text-center">
          <q-toggle
            v-model="props.row.locked"
            @update:model-value="val => onToggleLock(props.row, val)"
          />
        </q-td>
      </template>

      <template #body-cell-actions="props">
        <q-td :props="props" class="text-right">
          <q-btn dense flat icon="edit" color="primary" @click="editRegistration(props.row.registration_id)">
            <q-tooltip>Modifica Dati</q-tooltip>
          </q-btn>
          <q-btn dense flat icon="picture_as_pdf" @click="openPdf(props.row.registration_id)">
             <q-tooltip>Apri PDF</q-tooltip>
          </q-btn>
          <q-btn dense flat icon="info" @click="openDetails(props.row)">
             <q-tooltip>Dettagli & Storico</q-tooltip>
          </q-btn>
        </q-td>
      </template>
    </q-table>

    <q-dialog v-model="detailsOpen">
      <q-card style="min-width: 500px; max-width: 95vw;">
        <q-card-section class="row items-center bg-grey-2">
          <div class="text-h6">Dettagli Registrazione</div>
          <q-space />
          <q-btn flat round dense icon="close" v-close-popup />
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
               <div class="text-body2">{{ fmtDate(detailsFull.timestamp_iso) }}</div>
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
            <q-btn outline icon="picture_as_pdf" label="Apri PDF" @click="openPdf(detailsFull.registration_id)" />
          </div>

          <q-separator class="q-my-md" />

          <div class="text-h6 q-mb-md text-grey-8">
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
              :subtitle="fmtDate(log.iso_date)"
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
const detailsFull = ref(null) // Contiene i dati completi dall'API (incluso audit_log)

const pagination = ref({
  sortBy: 'timestamp_iso',
  descending: true,
  rowsPerPage: 20
})

const columns = [
  { name: 'timestamp_iso', label: 'Data/Ora', field: 'timestamp_iso', sortable: true, format: v => fmtDate(v) },
  { name: 'participant', label: 'Partecipante', field: row => `${row.participant_nome || ''} ${row.participant_cognome || ''}`.trim(), sortable: true },
  { name: 'email', label: 'Email', field: 'email', sortable: true },
  { name: 'is_minor', label: 'Minore', field: 'is_minor', sortable: true, align: 'center' },
  { name: 'locked', label: 'Bloccata', field: 'locked', align: 'center' },
  { name: 'actions', label: '', field: 'actions', align: 'right' }
]

function fmtDate (iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('it-IT')
}

const filteredRows = computed(() => {
  const q = filter.value.trim().toLowerCase()
  if (!q) return rows.value
  return rows.value.filter(r => {
    const hay = [r.registration_id, r.participant_nome, r.participant_cognome, r.email]
      .map(x => (x || '').toString().toLowerCase()).join(' ')
    return hay.includes(q)
  })
})

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

function openPdf (registrationId) {
  const url = api.getUri({ url: `/registration/${registrationId}/pdf` })
  window.open(url, '_blank')
}

// Nuova logica: Carica dettagli completi dall'API
async function openDetails (row) {
  detailsOpen.value = true
  loadingDetails.value = true
  detailsFull.value = null
  
  try {
    const res = await api.get(`/registration/details/${row.registration_id}`)
    detailsFull.value = res.data
  } catch (e) {
    console.error("Err caricamento dettagli:", e)
    $q.notify({ type: 'negative', message: 'Errore caricamento dettagli' })
    detailsOpen.value = false
  } finally {
    loadingDetails.value = false
  }
}

function editRegistration (registrationId) {
  router.push(`/scanner/${registrationId}`)
}

async function onToggleLock (row, locked) {
  const prev = !locked
  try {
    await api.post(`/registration/${row.registration_id}/lock`, { locked })
    $q.notify({ type: 'positive', message: locked ? 'Registrazione bloccata' : 'Registrazione sbloccata' })
  } catch (e) {
    console.error(e)
    row.locked = prev
    $q.notify({ type: 'negative', message: 'Errore aggiornando il blocco' })
  }
}

// Helpers per il template
function getPersonName(p) {
  if (!p) return 'Sconosciuto'
  return `${p.nome || ''} ${p.cognome || ''}`.trim()
}

// Helpers per Audit Log
function translateAction(action) {
  const map = {
    'CREATE': 'Registrazione Creata',
    'UPDATE': 'Modifica Dati',
    'EMAIL_SENT': 'Email Inviata',
    'EMAIL_ERROR': 'Errore Email',
    'LOCK_CHANGE': 'Stato Blocco Modificato'
  }
  return map[action] || action
}

function getActionIcon(action) {
  if (action === 'CREATE') return 'add_circle'
  if (action === 'UPDATE') return 'edit'
  if (action === 'EMAIL_SENT') return 'mail'
  if (action === 'EMAIL_ERROR') return 'error'
  if (action === 'LOCK_CHANGE') return 'lock'
  return 'info'
}

function getActionColor(action) {
  if (action === 'CREATE') return 'green'
  if (action === 'UPDATE') return 'orange'
  if (action === 'EMAIL_SENT') return 'blue'
  if (action === 'EMAIL_ERROR') return 'red'
  if (action === 'LOCK_CHANGE') return 'grey-8'
  return 'grey'
}

onMounted(load)
</script>

<style scoped>
.text-break {
  word-break: break-all;
}
</style>