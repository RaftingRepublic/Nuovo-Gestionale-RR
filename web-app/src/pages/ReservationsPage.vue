<template>
  <q-page class="q-pa-md bg-grey-2">
    <div class="row items-center justify-between q-mb-md">
      <div class="text-h5 text-weight-bold text-blue-grey-9">Gestione Prenotazioni</div>
      <q-btn color="primary" icon="add" label="Nuova Prenotazione" @click="openDialog()" unelevated />
    </div>

    <!-- Filtri -->
    <q-card class="q-mb-md q-pa-sm shadow-1 rounded-borders">
      <div class="row q-col-gutter-md items-center">
        <div class="col-auto">
          <q-input v-model="filterDate" type="date" label="Data" outlined dense class="bg-white" @update:model-value="loadReservations" clearable />
        </div>
        <div class="col">
          <q-input v-model="searchText" placeholder="Cerca cliente..." dense outlined class="bg-white">
            <template v-slot:append><q-icon name="search" /></template>
          </q-input>
        </div>
      </div>
    </q-card>

    <!-- Tabella -->
    <q-card class="shadow-1 rounded-borders">
      <q-table
        :rows="filteredReservations"
        :columns="columns"
        row-key="id"
        flat
        :loading="loading"
        no-data-label="Nessuna prenotazione trovata"
      >
        <template v-slot:body-cell-status="props">
          <q-td :props="props">
            <q-chip dense color="blue-1" text-color="blue-9" icon="event">{{ props.row.status || 'Attiva' }}</q-chip>
          </q-td>
        </template>
        <template v-slot:body-cell-actions="props">
          <q-td :props="props" align="right">
            <q-btn flat round dense icon="delete" color="negative" @click="deleteReservation(props.row)" />
          </q-td>
        </template>
      </q-table>
    </q-card>

    <!-- Wizard Prenotazione -->
    <ReservationWizard v-model="wizardOpen" @saved="loadReservations" />

  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'
import ReservationWizard from 'components/ReservationWizard.vue'

const $q = useQuasar()
const loading = ref(false)
const wizardOpen = ref(false)
const filterDate = ref(null)
const searchText = ref('')
const reservations = ref([])

const columns = [
  { name: 'date', label: 'Data', field: 'date', align: 'left', sortable: true },
  { name: 'time', label: 'Ora', field: 'time', align: 'left', sortable: true },
  { name: 'activity', label: 'Attività', field: 'activity_type', align: 'left', sortable: true },
  { name: 'pax', label: 'Pax', field: 'pax', align: 'center', sortable: true },
  { name: 'customer', label: 'Cliente', field: 'customer_name', align: 'left', sortable: true },
  { name: 'contact', label: 'Contatti', field: 'contact_info', align: 'left' },
  { name: 'actions', label: '', field: 'actions', align: 'right' }
]

const filteredReservations = computed(() => {
  let list = reservations.value
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(r => 
      r.customer_name.toLowerCase().includes(q) || 
      (r.notes && r.notes.toLowerCase().includes(q))
    )
  }
  return list
})

onMounted(() => {
  loadReservations()
})

async function loadReservations() {
  loading.value = true
  try {
    const res = await api.get('/reservations/', { params: { date: filterDate.value } })
    reservations.value = res.data
  } catch (e) {
    console.error(e)
    $q.notify({ type: 'negative', message: 'Errore caricamento prenotazioni' })
  } finally {
    loading.value = false
  }
}

function openDialog() {
  wizardOpen.value = true
}

async function deleteReservation(row) {
  if (!confirm(`Eliminare prenotazione di ${row.customer_name}?`)) return
  try {
    await api.delete(`/reservations/${row.id}`)
    $q.notify({ type: 'positive', message: 'Eliminata' })
    loadReservations()
  } catch (e) {
    console.error(e)
    $q.notify({ type: 'negative', message: 'Errore eliminazione' })
  }
}
</script>
