<template>
  <q-page padding>
    <h4 class="q-mt-none q-mb-md">Il Mangiasoldi — Cassa &amp; CRM</h4>

    <q-tabs v-model="activeTab" dense align="left" class="text-primary q-mb-md" indicator-color="primary">
      <q-tab name="libro" label="Libro Mastro" icon="menu_book" />
      <q-tab name="anagrafica" label="Anagrafica" icon="people" />
    </q-tabs>

    <q-tab-panels v-model="activeTab" animated>
      <!-- ═══════════════ TAB 1: LIBRO MASTRO ═══════════════ -->
      <q-tab-panel name="libro">

        <!-- I TRE CASSETTI -->
        <div class="row q-col-gutter-md q-mb-md">
          <div class="col-12 col-md-4">
            <q-card flat bordered class="bg-teal-1">
              <q-card-section>
                <div class="text-caption text-grey-8">CASH</div>
                <div class="text-h5 text-weight-bold text-teal-9">€ {{ totaliMetodo.CASH.total.toFixed(2) }}</div>
                <div class="text-caption text-grey-6">{{ totaliMetodo.CASH.count }} transazioni</div>
              </q-card-section>
            </q-card>
          </div>
          <div class="col-12 col-md-4">
            <q-card flat bordered class="bg-blue-1">
              <q-card-section>
                <div class="text-caption text-grey-8">POS</div>
                <div class="text-h5 text-weight-bold text-blue-9">€ {{ totaliMetodo.POS.total.toFixed(2) }}</div>
                <div class="text-caption text-grey-6">{{ totaliMetodo.POS.count }} transazioni</div>
              </q-card-section>
            </q-card>
          </div>
          <div class="col-12 col-md-4">
            <q-card flat bordered class="bg-orange-1">
              <q-card-section>
                <div class="text-caption text-grey-8">TRANSFER</div>
                <div class="text-h5 text-weight-bold text-orange-9">€ {{ totaliMetodo.TRANSFER.total.toFixed(2) }}</div>
                <div class="text-caption text-grey-6">{{ totaliMetodo.TRANSFER.count }} transazioni</div>
              </q-card-section>
            </q-card>
          </div>
        </div>

        <q-table
          title="Transazioni"
          :rows="transactions"
          :columns="txColumns"
          row-key="id"
          :loading="loadingTx"
          flat
          bordered
          dense
          :pagination="{ rowsPerPage: 25 }"
        />
      </q-tab-panel>

      <!-- ═══════════════ TAB 2: ANAGRAFICA ═══════════════ -->
      <q-tab-panel name="anagrafica">
        <q-input
          v-model="customerFilter"
          outlined
          dense
          placeholder="Cerca cliente (nome, email, telefono)..."
          class="q-mb-md"
          clearable
        >
          <template v-slot:prepend>
            <q-icon name="search" />
          </template>
        </q-input>

        <q-table
          title="Clienti"
          :rows="filteredCustomers"
          :columns="custColumns"
          row-key="id"
          :loading="loadingCust"
          flat
          bordered
          dense
          class="cursor-pointer"
          :pagination="{ rowsPerPage: 25 }"
          @row-click="apriFascicolo"
        />
      </q-tab-panel>
    </q-tab-panels>

    <!-- ═══════════════ DIALOG: FASCICOLO CLIENTE ═══════════════ -->
    <q-dialog v-model="dossierAperto" position="right" maximized>
      <q-card style="width: 600px; max-width: 100vw;">
        <!-- Header -->
        <q-card-section class="row items-center q-pb-sm bg-grey-2">
          <div>
            <div class="text-h6 text-weight-bold">{{ clienteAttivo?.full_name || 'Cliente' }}</div>
            <div class="text-caption text-grey-7">
              {{ clienteAttivo?.email || '—' }} · {{ clienteAttivo?.phone || '—' }}
            </div>
          </div>
          <q-space />
          <q-btn flat round icon="close" v-close-popup />
        </q-card-section>

        <q-separator />

        <!-- Body -->
        <q-card-section class="scroll" style="max-height: calc(100vh - 80px); overflow-y: auto;">
          <q-inner-loading :showing="loadingDossier" />

          <div v-if="!loadingDossier && ordiniCliente.length === 0" class="text-center text-grey-5 q-pa-lg">
            <q-icon name="inbox" size="48px" class="q-mb-sm" />
            <div>Nessun ordine trovato per questo cliente.</div>
          </div>

          <q-card
            v-for="ordine in ordiniCliente"
            :key="ordine.id"
            flat
            bordered
            class="q-mb-md"
          >
            <q-card-section>
              <!-- Riga 1: Intestazione -->
              <div class="row items-center q-mb-xs">
                <div class="col">
                  <span class="text-weight-bold">Ordine del {{ formatDate(ordine.created_at) }}</span>
                </div>
                <div class="col-auto text-right row items-center">
                  <q-badge :color="debitoOrdine(ordine) > 0 ? 'negative' : 'positive'" class="text-subtitle2">
                    {{ debitoOrdine(ordine) > 0 ? `DEBITO: € ${debitoOrdine(ordine).toFixed(2)}` : 'SALDATO' }}
                  </q-badge>
                  <q-btn v-if="debitoOrdine(ordine) > 0" size="sm" color="primary" icon="payments" label="Incassa Saldo" class="q-ml-md" @click="apriPagamento(ordine)" />
                </div>
              </div>

              <div class="row text-caption text-grey-7 q-mb-sm">
                <div class="col">Pax: <strong>{{ ordine.pax || '—' }}</strong></div>
                <div class="col">Discesa: <strong>{{ ordine.rides ? formatDate(ordine.rides.ride_date) + ' ' + (ordine.rides.ride_time || '') : '—' }}</strong></div>
              </div>

              <q-separator class="q-my-sm" />

              <!-- Riga 2: Finanze -->
              <div class="row text-body2 q-mb-sm">
                <div class="col">Totale: <strong>€ {{ Number(ordine.price_total || 0).toFixed(2) }}</strong></div>
                <div class="col">Pagato: <strong>€ {{ Number(ordine.price_paid || 0).toFixed(2) }}</strong></div>
              </div>

              <q-separator class="q-my-sm" />

              <!-- Riga 3: Pagamenti -->
              <div class="text-caption text-weight-bold q-mb-xs">Pagamenti</div>
              <div v-if="!ordine.transactions || ordine.transactions.length === 0" class="text-caption text-grey-5">
                Nessun pagamento registrato.
              </div>
              <div v-else>
                <div
                  v-for="tx in ordine.transactions"
                  :key="tx.id"
                  class="row text-caption q-py-xs"
                  style="border-bottom: 1px dashed #e0e0e0;"
                >
                  <div class="col-5">{{ formatDate(tx.created_at) }}</div>
                  <div class="col-3">{{ tx.method || '—' }}</div>
                  <div class="col-4 text-right text-weight-bold">€ {{ Number(tx.amount || 0).toFixed(2) }}</div>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- ═══════════════ DIALOG: MODALE INCASSO ═══════════════ -->
    <q-dialog v-model="modalePagamento">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">Registra Incasso</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input v-model.number="formPagamento.amount" type="number" step="0.01" label="Importo (€)" autofocus />
          <q-select v-model="formPagamento.method" :options="opzioniMetodo" label="Metodo" class="q-mt-md" />
        </q-card-section>
        <q-card-actions align="right" class="text-primary">
          <q-btn flat label="Annulla" v-close-popup />
          <q-btn flat label="Conferma" @click="eseguiPagamento" :loading="loadingPagamento" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { supabase } from 'src/supabase'

// ── State ──
const activeTab = ref('libro')

// Libro Mastro
const transactions = ref([])
const loadingTx = ref(false)

// Anagrafica
const customers = ref([])
const loadingCust = ref(false)
const customerFilter = ref('')

// Fascicolo Cliente
const dossierAperto = ref(false)
const clienteAttivo = ref(null)
const ordiniCliente = ref([])
const loadingDossier = ref(false)

// Leva dello Strozzino (Incasso)
const modalePagamento = ref(false)
const formPagamento = ref({ order_id: null, amount: 0, method: 'CASH' })
const opzioniMetodo = ['CASH', 'POS', 'TRANSFER']
const loadingPagamento = ref(false)

// ── Colonne tabella transazioni ──
const txColumns = [
  { name: 'created_at', label: 'Data', field: 'created_at', sortable: true, format: v => v ? new Date(v).toLocaleString('it-IT') : '-' },
  { name: 'type', label: 'Tipo', field: 'type', sortable: true },
  { name: 'method', label: 'Metodo', field: 'method', sortable: true },
  { name: 'amount', label: 'Importo (€)', field: 'amount', sortable: true, format: v => v != null ? Number(v).toFixed(2) : '-' },
  { name: 'notes', label: 'Note', field: 'notes' },
]

// ── Colonne tabella clienti ──
const custColumns = [
  { name: 'full_name', label: 'Nome', field: 'full_name', sortable: true },
  { name: 'email', label: 'Email', field: 'email', sortable: true },
  { name: 'phone', label: 'Telefono', field: 'phone', sortable: true },
  { name: 'created_at', label: 'Creato il', field: 'created_at', sortable: true, format: v => v ? new Date(v).toLocaleDateString('it-IT') : '-' },
]

// ── I TRE CASSETTI: Totali per metodo (CASH, POS, TRANSFER — sempre visibili) ──
const totaliMetodo = computed(() => {
  const base = {
    CASH: { total: 0, count: 0 },
    POS: { total: 0, count: 0 },
    TRANSFER: { total: 0, count: 0 },
  }
  for (const tx of transactions.value) {
    const m = (tx.method || '').toUpperCase()
    if (base[m]) {
      base[m].total += Number(tx.amount) || 0
      base[m].count++
    }
  }
  return base
})

// ── Filtro clienti locale ──
const filteredCustomers = computed(() => {
  if (!customerFilter.value) return customers.value
  const q = customerFilter.value.toLowerCase()
  return customers.value.filter(c =>
    (c.full_name || '').toLowerCase().includes(q) ||
    (c.email || '').toLowerCase().includes(q) ||
    (c.phone || '').toLowerCase().includes(q)
  )
})

// ── Helpers ──
function formatDate (val) {
  if (!val) return '—'
  const d = new Date(val)
  return d.toLocaleDateString('it-IT')
}

function debitoOrdine (ordine) {
  return Number(ordine.price_total || 0) - Number(ordine.price_paid || 0)
}

// ── Fascicolo Cliente (Drill-down) ──
async function apriFascicolo (evt, row) {
  clienteAttivo.value = row
  ordiniCliente.value = []
  dossierAperto.value = true
  loadingDossier.value = true

  try {
    const { data, error } = await supabase
      .from('orders')
      .select('*, rides(ride_date, ride_time), transactions(*)')
      .eq('customer_id', row.id)
      .order('created_at', { ascending: false })

    if (error) {
      console.error('Errore Supabase (Fascicolo):', error)
      alert('ERRORE DATABASE: ' + error.message)
      loadingDossier.value = false
      return
    }
    ordiniCliente.value = data || []
  } catch (e) {
    console.error('[CassaPage] Errore fetch fascicolo cliente:', e)
    alert('ERRORE CRITICO: ' + (e.message || e))
  } finally {
    loadingDossier.value = false
  }
}

// ── Leva dello Strozzino (Incasso diretto) ──
const apriPagamento = (ordine) => {
  formPagamento.value.order_id = ordine.id
  formPagamento.value.amount = Number(ordine.price_total) - Number(ordine.price_paid || 0)
  formPagamento.value.method = 'CASH'
  modalePagamento.value = true
}

const eseguiPagamento = async () => {
  loadingPagamento.value = true
  try {
    // 1. Inserisce la transazione nel Libro Mastro
    const { error: txError } = await supabase.from('transactions').insert({
      order_id: formPagamento.value.order_id,
      amount: Number(formPagamento.value.amount),
      method: formPagamento.value.method,
      type: 'payment'
    })
    if (txError) throw txError

    // 2. Aggiorna il totale pagato nell'ordine
    const ordine = ordiniCliente.value.find(o => o.id === formPagamento.value.order_id)
    const nuovoPagato = Number(ordine.price_paid || 0) + Number(formPagamento.value.amount)

    const { error: ordError } = await supabase.from('orders')
      .update({ price_paid: nuovoPagato })
      .eq('id', formPagamento.value.order_id)
    if (ordError) throw ordError

    // 3. Ricarica i dati freschi
    modalePagamento.value = false
    await apriFascicolo(null, clienteAttivo.value)
    await fetchTransactions()

  } catch (err) {
    console.error('Errore incasso:', err)
    alert('Errore durante l\'incasso: ' + err.message)
  } finally {
    loadingPagamento.value = false
  }
}

// ── Fetch dati ──
async function fetchTransactions () {
  loadingTx.value = true
  try {
    const { data, error } = await supabase
      .from('transactions')
      .select('*')
      .order('created_at', { ascending: false })
    if (error) throw error
    transactions.value = data || []
  } catch (e) {
    console.error('[CassaPage] Errore fetch transactions:', e)
  } finally {
    loadingTx.value = false
  }
}

async function fetchCustomers () {
  loadingCust.value = true
  try {
    const { data, error } = await supabase
      .from('customers')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(200)
    if (error) throw error
    customers.value = data || []
  } catch (e) {
    console.error('[CassaPage] Errore fetch customers:', e)
  } finally {
    loadingCust.value = false
  }
}

onMounted(() => {
  fetchTransactions()
  fetchCustomers()
})
</script>
