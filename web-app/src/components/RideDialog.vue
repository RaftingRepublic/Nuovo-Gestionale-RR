<template>
  <!-- ═══════════════════════════════════════════════════════════════════ -->
  <!-- MODALE CENTRALE — Dettaglio Turno                                -->
  <!-- ═══════════════════════════════════════════════════════════════════ -->
  <q-dialog v-model="isOpen">
    <q-card class="ride-dialog-card">
      <!-- Header dinamico con colore basato su stato -->
      <q-card-section :class="rideHeaderBgClass" class="text-white q-py-sm col-auto">
        <div class="row items-center justify-between">
          <div>
            <div class="text-h6">{{ localRide?.activity_name }}</div>
            <div class="text-caption">
              {{ localRide?.ride_date }} · {{ localRide?.ride_time }}
              <q-badge color="white" text-color="dark" class="q-ml-sm text-weight-bold">
                {{ localRide?.booked_pax || 0 }} / {{ localRide?.max_pax || '—' }} pax
              </q-badge>
            </div>
            <!-- Risorse sotto il titolo -->
            <div class="row q-gutter-xs q-mt-xs" v-if="currentSlotData?.assigned_staff?.length || currentSlotData?.assigned_fleet?.length">
              <q-chip v-for="s in currentSlotData?.assigned_staff" :key="'ds'+s.id" dense icon="person" color="rgba(255,255,255,0.2)" text-color="white" size="sm">{{ s.name }}</q-chip>
              <q-chip v-for="f in currentSlotData?.assigned_fleet" :key="'df'+f.id" dense :icon="f.category === 'RAFT' ? 'rowing' : 'local_shipping'" color="rgba(255,255,255,0.2)" text-color="white" size="sm">{{ f.name }}</q-chip>
            </div>
          </div>
          <div class="column items-end q-gutter-sm">
            <q-btn flat round dense icon="close" color="white" v-close-popup />
            <div class="row q-gutter-xs no-wrap">
              <q-btn unelevated dense color="red-7" text-color="white" icon="delete" label="CANCELLA ORARIO" size="sm"
                v-if="String(localRide?.id || '').startsWith('custom')"
                @click.stop="deleteCustomRideLocally()" />
            </div>
            <!-- Semaforo Manuale -->
            <q-btn-group outline class="semaphore-group">
              <q-btn dense size="xs" class="bg-white" text-color="green-8" label="VERDE" @click="setOverride('A')" />
              <q-btn dense size="xs" class="bg-white" text-color="blue-8" label="BLU" @click="setOverride('D')" />
              <q-btn dense size="xs" class="bg-white" text-color="amber-9" label="GIALLO" @click="setOverride('B')" />
              <q-btn dense size="xs" class="bg-white" text-color="red-8" label="ROSSO" @click="setOverride('C')" />
              <q-btn dense size="xs" class="bg-white" text-color="grey-8" label="AUTO" @click="clearOverride()" />
            </q-btn-group>
          </div>
        </div>
      </q-card-section>

      <q-separator />

      <!-- ═══ TABS OMNI-BOARD ═══ -->
      <q-tabs v-model="activeTab" class="text-primary bg-white col-auto" dense align="left" active-color="primary" indicator-color="primary" narrow-indicator>
        <q-tab name="existing" icon="receipt_long" label="ORDINI ESISTENTI" />
        <q-tab name="new" icon="add_circle" label="NUOVA PRENOTAZIONE" />
      </q-tabs>
      <q-separator />

      <!-- Loading -->
      <div v-if="rideLoading" class="flex flex-center q-pa-xl col">
        <q-spinner size="3em" color="primary" />
      </div>

      <!-- ═══ TAB PANELS ═══ -->
      <q-tab-panels v-model="activeTab" animated v-else-if="localRide" class="col scroll q-pa-none" style="overflow-x: hidden; min-height: 0;">
        <q-tab-panel name="existing" class="q-pa-none">

        <!-- Info Disponibilità (Engine Dashboard) -->
        <q-card-section class="q-pb-none" v-if="localRide && localRide.total_capacity !== undefined">
           <q-banner :class="localRide.status === 'GIALLO' ? 'bg-warning text-dark' : (localRide.status === 'ROSSO' ? 'bg-negative text-white' : 'bg-positive text-white')" rounded dense>
              <template v-slot:avatar>
                 <q-icon :name="localRide.status === 'GIALLO' ? 'local_shipping' : (localRide.status === 'ROSSO' ? 'warning' : 'check_circle')" />
              </template>
              <div class="text-weight-bold">Stato Motore: {{ localRide.status }}</div>
              <div class="text-caption">
                 Capacità Totale: {{ localRide.total_capacity }} pax ({{ localRide.total_capacity - (localRide.arr_bonus_seats || 0) }} Base + {{ localRide.arr_bonus_seats || 0 }} Fluviali ARR)
              </div>
              <div class="text-caption">Posti Residui: {{ localRide.remaining_seats }}</div>
           </q-banner>
        </q-card-section>

        <div v-if="!localRide.orders || localRide.orders.length === 0" class="text-center text-grey q-pa-xl">
          <q-icon name="event_seat" size="4em" />
          <div class="q-mt-sm text-h6">Nessun ordine per questo turno</div>
        </div>

        <q-list v-else separator class="q-pa-sm">
          <q-expansion-item
            v-for="order in localRide.orders"
            :key="order.id"
            group="orders"
            header-class="rounded-borders q-mb-xs"
            :header-style="{ backgroundColor: order.order_status === 'CONFERMATO' ? '#f0fdf4' : (order.order_status === 'IN_ATTESA' ? '#fffbeb' : '#f8fafc') }"
            expand-icon-class="text-primary"
          >
            <!-- ══ HEADER ORDINE ══ -->
            <template v-slot:header>
              <q-item-section avatar>
                <q-avatar :color="orderStatusColor(order.order_status)" text-color="white" icon="receipt" size="40px" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-bold text-body1">{{ order.customer_name || 'Senza nome' }}</q-item-label>
                <q-item-label caption>
                  <span class="text-weight-medium">{{ getEffectivePax(order) }} pax</span> · € {{ order.price_total?.toFixed(2) }}
                  <span v-if="order.discount_applied > 0" class="text-green-8"> (-{{ (order.discount_applied * 100).toFixed(0) }}%)</span>
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <div class="row items-center q-gutter-xs no-wrap">
                  <q-btn outline dense color="primary" icon="group" label="PARTECIPANTI" size="sm" @click.stop="emit('open-firaft', order)" />
                  <q-btn outline dense color="primary" icon="edit" label="MODIFICA" size="sm" @click.stop="emit('edit-order', order, localRide)" />
                  <q-btn outline dense color="negative" icon="delete" size="sm" @click.stop="emit('delete-order', localRide, order)" title="Cancella Prenotazione" />
                  <div class="column items-end q-gutter-xs">
                  <q-badge :color="orderStatusColor(order.order_status)">{{ order.order_status }}</q-badge>
                  <q-badge v-if="order.order_status === 'IN_ATTESA'" color="orange-2" text-color="orange-10" class="text-caption">
                    <q-icon name="visibility_off" size="12px" class="q-mr-xs" />Fantasma
                  </q-badge>
                  <q-badge v-if="order.is_exclusive_raft" color="purple-2" text-color="purple-10" class="text-caption">🚣 Esclusiva</q-badge>
                  </div>
                </div>
              </q-item-section>
            </template>

            <!-- ══ CORPO ESPANSO — Cruscotto Segreteria ══ -->
            <q-card flat class="bg-grey-1 q-ma-sm" bordered style="overflow: hidden;">
              <q-card-section class="q-gutter-md column">
                <!-- ─── A) Intestazione + Stato Ordine ─── -->
                <div class="row q-col-gutter-md items-center wrap">
                  <div class="col-12 col-sm-3">
                    <div class="text-caption text-grey-6">Referente</div>
                    <div class="text-weight-bold">{{ order.customer_name || '—' }}</div>
                  </div>
                  <div class="col-12 col-sm-2">
                    <div class="text-caption text-grey-6">Email</div>
                    <div>{{ order.customer_email || '—' }}</div>
                  </div>
                  <div class="col-12 col-sm-1">
                    <div class="text-caption text-grey-6">Pax</div>
                    <div class="text-weight-bold text-h6">{{ getEffectivePax(order) }}</div>
                  </div>
                  <div class="col-12 col-sm-3">
                    <q-btn outline dense color="primary" icon="edit" label="MODIFICA" @click.stop="emit('edit-order', order, localRide)" class="q-mb-xs full-width" />
                  </div>
                  <div class="col-12 col-sm-3">
                    <q-select
                      :model-value="order.order_status"
                      :options="orderStatusOptions"
                      label="Stato Ordine"
                      dense outlined emit-value map-options
                      @update:model-value="onOrderStatusChange(order, $event)"
                      class="bg-white"
                    >
                      <template v-slot:prepend>
                        <q-icon name="flag" :color="orderStatusColor(order.order_status)" />
                      </template>
                    </q-select>
                  </div>
                </div>

                <q-separator />

                <!-- ─── B) Azioni Rapide — Check-in ─── -->
                <div>
                  <div class="text-subtitle2 text-blue-grey-8 q-mb-sm"><q-icon name="flash_on" class="q-mr-xs" />Azioni Rapide — Check-in</div>
                  <div class="row q-gutter-sm wrap">
                    <q-btn round outline color="primary" icon="link" size="sm" @click.stop="copyMagicLink(order)"><q-tooltip>Copia Link Consenso</q-tooltip></q-btn>
                    <q-btn round outline color="primary" icon="qr_code" size="sm" @click.stop="openQrModal(order)"><q-tooltip>Genera QR Code</q-tooltip></q-btn>
                    <q-btn round outline color="green" icon="chat" size="sm" @click.stop="shareWhatsApp(order)"><q-tooltip>WhatsApp</q-tooltip></q-btn>
                    <q-btn v-if="order.order_status === 'IN_ATTESA'" unelevated color="secondary" icon="check_circle" label="Conferma Bonifico" size="sm" :loading="confirmingOrderId === order.id" @click="confirmBonifico(order.id)" />
                  </div>
                </div>

                <q-separator />

                <!-- ─── C) Drop-outs & Penali ─── -->
                <div>
                  <div class="text-subtitle2 text-blue-grey-8 q-mb-sm"><q-icon name="person_remove" class="q-mr-xs" />Drop-outs &amp; Penali</div>
                  <div class="text-caption text-grey-5 q-mb-sm">Se il gruppo si presenta con meno persone, abbassa i pax e aggiungi le penali corrispondenti. (€ 20 / pax mancante, modificabile)</div>
                  <div class="row q-col-gutter-sm items-center wrap">
                    <div class="col-3">
                      <q-input
                        :model-value="order._actual_pax != null ? order._actual_pax : order.total_pax"
                        @update:model-value="val => onPaxChange(order, Number(val))"
                        type="number" :label="'Pax effettivi (di ' + order.total_pax + ')'" dense outlined class="bg-white"
                        hide-bottom-space
                      />
                    </div>
                    <div class="col-4">
                      <q-input
                        :model-value="order._penalty_amount != null ? order._penalty_amount : 0"
                        @update:model-value="val => { order._penalty_amount = Number(val) }"
                        type="number" label="Penali / Trattenute €" dense outlined prefix="€" class="bg-white"
                        hide-bottom-space
                      />
                    </div>
                    <div class="col-auto">
                      <q-btn unelevated color="orange-8" icon="update" label="Aggiorna Ordine" size="sm"
                        @click="syncRideState(); $q.notify({ type: 'positive', message: 'Drop-outs e Pax ricalcolati ✅' })" />
                    </div>
                  </div>
                </div>

                <q-separator />

                <!-- ─── D) Libro Mastro Transazioni ─── -->
                <div>
                  <div class="text-subtitle2 text-blue-grey-8 q-mb-sm"><q-icon name="account_balance" class="q-mr-xs" />Libro Mastro — Transazioni</div>
                  <div class="row q-gutter-sm q-mb-md wrap items-center">
                    <q-chip color="blue-1" text-color="blue-9" icon="euro" size="md" class="text-weight-bold">Totale: € {{ order.price_total?.toFixed(2) || '0.00' }}</q-chip>
                    <q-chip color="green-1" text-color="green-9" icon="check_circle" size="md" class="text-weight-bold">Pagato: € {{ (order.paid_amount || 0).toFixed(2) }}</q-chip>
                    <q-chip :color="(order.price_total || 0) - (order.paid_amount || 0) > 0 ? 'red-1' : 'grey-2'" :text-color="(order.price_total || 0) - (order.paid_amount || 0) > 0 ? 'red-9' : 'grey-6'" icon="pending" size="md" class="text-weight-bold">Rimane: € {{ ((order.price_total || 0) - (order.paid_amount || 0)).toFixed(2) }}</q-chip>
                    <span v-if="(order.price_total || 0) - (order.paid_amount || 0) > 0" class="text-caption text-grey-8 q-ml-sm">
                      (€ {{ (((order.price_total || 0) - (order.paid_amount || 0)) / (order._actual_pax || order.total_pax || 1)).toFixed(2) }} / pax)
                    </span>
                  </div>
                  <q-list bordered dense class="rounded-borders bg-white q-mb-sm" v-if="order.paid_amount > 0">
                    <q-item dense>
                      <q-item-section avatar><q-icon name="payment" color="green" /></q-item-section>
                      <q-item-section>€ {{ (order.paid_amount || 0).toFixed(2) }} — SUMUP</q-item-section>
                      <q-item-section side class="text-caption text-grey">{{ localRide?.ride_date }}</q-item-section>
                    </q-item>
                  </q-list>
                  <div v-else class="text-caption text-grey-4 q-mb-sm">Nessun pagamento registrato</div>
                  <div class="row q-col-gutter-sm items-end wrap">
                    <div class="col-3"><q-input model-value="" label="Euro (€)" dense outlined type="number" prefix="€" class="bg-white" /></div>
                    <div class="col-3">
                      <q-select model-value="CASH" :options="['CASH', 'SUMUP', 'BONIFICO', 'ALTRO']" label="Metodo" dense outlined class="bg-white" />
                    </div>
                    <div class="col-3"><q-input model-value="" label="Note" dense outlined class="bg-white" /></div>
                    <div class="col-auto"><q-btn unelevated color="green-8" icon="add" label="PAGA" size="sm" /></div>
                  </div>
                </div>

                <q-separator />

                <!-- ─── D-bis) Note Operative ─── -->
                <div class="q-mt-md q-mb-sm">
                  <div class="text-subtitle2 text-grey-8 q-mb-xs">
                    <q-icon name="edit_note" size="sm" class="q-mr-xs" /> Note Operative
                  </div>
                  <q-input
                    v-model="order.notes"
                    type="textarea"
                    outlined
                    dense
                    autogrow
                    placeholder="Nessuna nota presente. Clicca per aggiungere un appunto..."
                    @blur="syncRideState()"
                  />
                </div>

                <q-separator />

                <!-- ─── E) Lista Partecipanti ─── -->
                <div>
                  <div class="row justify-between items-center q-mb-sm">
                    <div class="text-subtitle2 text-blue-grey-8"><q-icon name="group" class="q-mr-xs" />Lista Partecipanti</div>
                    <q-btn v-if="isFiraftRequired(localRide)" size="sm" color="positive" text-color="white" label="TESSERA SELEZIONATI" icon="security" @click="emit('open-firaft', order)" />
                  </div>
                  <q-list bordered dense class="rounded-borders bg-white">
                    <!-- Referente -->
                    <q-item dense v-if="order.customer_name">
                      <q-item-section avatar><q-icon name="star" color="amber" /></q-item-section>
                      <q-item-section>
                        <q-item-label class="text-weight-bold">{{ order.customer_name }}</q-item-label>
                        <q-item-label caption>Referente gruppo</q-item-label>
                      </q-item-section>
                      <q-item-section side>
                        <q-badge v-if="order.registrations?.length > 0" color="green">Compilato</q-badge>
                        <q-badge v-else color="grey">In attesa</q-badge>
                      </q-item-section>
                    </q-item>
                    <!-- Posti compilati -->
                    <q-item dense v-for="reg in (order.registrations || [])" :key="reg.id" clickable @click="openParticipantForm(reg)">
                      <q-item-section avatar><q-icon name="person" color="primary" /></q-item-section>
                      <q-item-section>
                        <q-item-label>{{ reg.nome }} {{ reg.cognome }}</q-item-label>
                        <q-item-label caption>{{ reg.email || '—' }}</q-item-label>
                      </q-item-section>
                      <q-item-section side><q-badge color="green-2" text-color="green-9">Compilato</q-badge></q-item-section>
                    </q-item>
                    <!-- Posti vuoti -->
                    <q-item dense v-for="n in emptySlotCount(order)" :key="'empty-'+n">
                      <q-item-section avatar><q-icon name="person_outline" color="blue-3" /></q-item-section>
                      <q-item-section>
                        <q-item-label class="text-grey-5">Slot Vuoto #{{ n + 1 + (order.registrations?.length || 0) }}</q-item-label>
                        <q-item-label caption class="text-grey-4">—</q-item-label>
                      </q-item-section>
                      <q-item-section side><q-badge color="grey-2" text-color="grey-5">Vuoto</q-badge></q-item-section>
                    </q-item>
                  </q-list>
                </div>
              </q-card-section>
            </q-card>
          </q-expansion-item>
        </q-list>
        </q-tab-panel>
        <q-tab-panel name="new" class="q-pa-md">
          <DeskBookingForm
            :activity-id="localRide?.activity_id || currentSlotData?.activity_id"
            :date="localRide?.ride_date"
            :time="localRide?.ride_time"
            :unit-price="localRide?._unit_price || currentSlotData?.price || 0"
            @success="onBookingSuccess"
          />
        </q-tab-panel>
      </q-tab-panels>
    </q-card>
  </q-dialog>

  <!-- ═══════════════════════════════════════════════════════════════════ -->
  <!-- DIALOGO PARTECIPANTI                                              -->
  <!-- ═══════════════════════════════════════════════════════════════════ -->
  <q-dialog v-model="showParticipantsDialog">
    <q-card style="width: 600px; max-width: 95vw;" v-if="selectedOrder">
      <q-card-section class="bg-teal-8 text-white row items-center justify-between q-py-sm">
        <div>
          <div class="text-h6">Lista Partecipanti</div>
          <div class="text-caption">{{ selectedOrder.registrations?.length || 0 }} / {{ selectedOrder.total_pax }} — {{ selectedOrder.customer_name || 'N/D' }}</div>
        </div>
        <q-btn flat round dense icon="close" v-close-popup />
      </q-card-section>
      <q-separator />
      <q-card-section class="scroll q-pa-none" style="max-height: 60vh;">
        <q-list separator>
          <q-item v-for="reg in selectedOrder.registrations" :key="reg.id" clickable v-ripple @click="openParticipantForm(reg)">
            <q-item-section side v-if="reg.firaft_status === 'DA_TESSERARE'">
              <q-checkbox :model-value="selectedRegistrations.includes(reg.id)" @update:model-value="toggleRegistration(reg.id)" @click.stop dense color="primary" />
            </q-item-section>
            <q-item-section side v-else><div style="width: 40px"></div></q-item-section>
            <q-item-section>
              <q-item-label class="text-weight-bold">{{ reg.nome }} {{ reg.cognome }}</q-item-label>
              <q-item-label caption>{{ reg.email || '—' }}</q-item-label>
            </q-item-section>
            <q-item-section side><q-icon name="thumb_up" :color="reg.nome ? 'green' : 'grey-4'" size="sm"><q-tooltip>Consenso informato</q-tooltip></q-icon></q-item-section>
            <q-item-section side><q-icon :name="firaftIcon(reg.firaft_status)" :color="firaftColor(reg.firaft_status)" size="sm"><q-tooltip>{{ firaftLabel(reg.firaft_status) }}</q-tooltip></q-icon></q-item-section>
            <q-item-section side><q-icon name="chevron_right" color="grey-5" /></q-item-section>
          </q-item>
        </q-list>
      </q-card-section>
      <q-separator />
      <q-card-actions class="bg-grey-2 q-pa-md">
        <div class="text-caption text-grey-7 q-mr-auto" v-if="selectedRegistrations.length > 0">
          {{ selectedRegistrations.length }} selezionat{{ selectedRegistrations.length > 1 ? 'i' : 'o' }}
        </div>
        <q-btn label="Tessera Selezionati" color="primary" icon="card_membership" unelevated :disable="selectedRegistrations.length === 0" :loading="tesseringInProgress" @click="tesseraSelezionati" />
      </q-card-actions>
    </q-card>
  </q-dialog>

  <!-- DIALOGO DETTAGLIO PARTECIPANTE -->
  <q-dialog v-model="showParticipantFormDialog">
    <q-card style="width: 550px; max-width: 95vw;" v-if="selectedParticipant">
      <q-card-section class="bg-indigo-8 text-white row items-center justify-between q-py-sm">
        <div class="text-h6">Dettaglio Partecipante</div>
        <q-btn flat round dense icon="close" v-close-popup />
      </q-card-section>
      <q-separator />
      <q-card-section class="q-gutter-md scroll" style="max-height: 70vh;">
        <div class="text-subtitle2 text-blue-grey-8 q-mb-xs">Anagrafica</div>
        <div class="row q-col-gutter-sm">
          <div class="col-6"><q-input v-model="partForm.nome" label="Nome" outlined dense readonly /></div>
          <div class="col-6"><q-input v-model="partForm.cognome" label="Cognome" outlined dense readonly /></div>
        </div>
        <div class="row q-col-gutter-sm">
          <div class="col-6"><q-input v-model="partForm.email" label="Email" outlined dense readonly /></div>
          <div class="col-6"><q-input v-model="partForm.telefono" label="Telefono" outlined dense readonly /></div>
        </div>
        <div class="row q-col-gutter-sm">
          <div class="col-4"><q-input v-model="partForm.data_nascita" label="Data Nascita" outlined dense readonly /></div>
          <div class="col-4"><q-input v-model="partForm.sesso" label="Sesso" outlined dense readonly /></div>
          <div class="col-4"><q-input :model-value="partForm.is_minor ? 'Sì' : 'No'" label="Minore" outlined dense readonly /></div>
        </div>
        <q-input v-model="partForm.residenza" label="Residenza" outlined dense readonly />
        <q-separator class="q-my-sm" />
        <div class="text-subtitle2 text-blue-grey-8 q-mb-xs">Stato Tesseramento</div>
        <div class="row items-center q-gutter-sm">
          <q-icon :name="firaftIcon(partForm.firaft_status)" :color="firaftColor(partForm.firaft_status)" size="md" />
          <span class="text-weight-bold">{{ firaftLabel(partForm.firaft_status) }}</span>
        </div>
        <q-separator class="q-my-sm" />
        <div class="text-subtitle2 text-blue-grey-8 q-mb-xs">Consensi</div>
        <div class="column q-gutter-xs">
          <q-toggle v-model="partForm.consenso_privacy" label="Privacy" disable dense />
          <q-toggle v-model="partForm.consenso_foto" label="Autorizzazione foto/video" disable dense />
          <q-toggle v-model="partForm.consenso_medico" label="Dichiarazione medica" disable dense />
        </div>
      </q-card-section>
      <q-separator />
      <q-card-actions align="right" class="bg-grey-1 q-pa-md"><q-btn flat label="Chiudi" v-close-popup /></q-card-actions>
    </q-card>
  </q-dialog>

  <!-- QR Dialog (componente condiviso) -->
  <QrDialog v-model="qrDialogOpen" :url="qrUrl" />
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useQuasar } from 'quasar'
import { useResourceStore } from 'stores/resource-store'
import { supabase } from 'src/supabase'
import { api } from 'boot/axios'
import { useCheckin } from 'src/composables/useCheckin'
import QrDialog from 'src/components/QrDialog.vue'
import DeskBookingForm from 'src/components/DeskBookingForm.vue'

const props = defineProps({
  modelValue: Boolean,
  ride: Object
})
const emit = defineEmits([
  'update:modelValue', 'edit-order', 'delete-order',
  'open-resources', 'open-firaft', 'refresh'
])

const $q = useQuasar()
const store = useResourceStore()
const { qrDialogOpen, qrUrl, copyMagicLink, openQrModal, shareWhatsApp } = useCheckin()

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// ═══ TABS OMNI-BOARD ═══
const activeTab = ref('existing')

function onBookingSuccess () {
    activeTab.value = 'existing'
    emit('refresh')
}

// Ride state locale
const localRide = ref(null)
const rideLoading = ref(false)
const currentSlotId = ref(null)
const currentSlotData = computed(() => store.dailySchedule.find(s => s.id === currentSlotId.value) || null)

// Header dinamico modale
const rideHeaderBgClass = computed(() => {
  const status = localRide.value?.status || currentSlotData.value?.engine_status
  if (status === 'ROSSO' || status === 'C') return 'bg-red-8'
  if (status === 'GIALLO' || status === 'B') return 'bg-amber-8'
  if (status === 'VERDE' || status === 'A') return 'bg-green-8'
  if (status === 'D') return 'bg-blue-8'
  return 'bg-primary'
})

// Order State
const selectedOrder = ref(null)
const confirmingOrderId = ref(null)

// Participants Dialog State
const showParticipantsDialog = ref(false)
const selectedRegistrations = ref([])
const tesseringInProgress = ref(false)

// Participant Form State
const showParticipantFormDialog = ref(false)
const selectedParticipant = ref(null)
const partForm = reactive({
  nome: '', cognome: '', email: '', telefono: '',
  data_nascita: '', sesso: '', is_minor: false, residenza: '',
  firaft_status: 'NON_RICHIESTO',
  consenso_privacy: false, consenso_foto: false, consenso_medico: false,
})

// Opzioni stato ordine
const orderStatusOptions = [
  { label: 'Confermato', value: 'CONFERMATO' },
  { label: 'In Attesa (Fantasma)', value: 'IN_ATTESA' },
  { label: 'Da Saldare', value: 'DA_SALDARE' },
  { label: 'Manuale', value: 'MANUALE' },
  { label: 'Completato', value: 'COMPLETATO' },
  { label: 'Cancellato', value: 'CANCELLATO' },
]



// Pre-popola quando il dialog si apre
watch(() => props.ride, (slot) => {
  if (!slot) return
  currentSlotId.value = slot.id
  activeTab.value = 'existing'

  const localSlot = store.dailySchedule.find(r => r.id === slot.id) || slot
  localRide.value = {
    id: localSlot.id,
    activity_id: localSlot.activity_id || slot.activity_id || '',
    activity_name: localSlot.activity_type || localSlot.title || 'Turno',
    ride_date: localSlot.ride_date || '',
    ride_time: localSlot.time || '',
    status: localSlot.engine_status || localSlot.status || 'VERDE',
    booked_pax: localSlot.booked_pax || 0,
    max_pax: localSlot.total_capacity || 16,
    orders: localSlot.orders || [],
    assigned_staff: localSlot.assigned_staff || [],
    assigned_fleet: localSlot.assigned_fleet || [],
    color_hex: localSlot.color_hex || '#1976D2',
    notes: localSlot.notes || '',
    is_overridden: localSlot.is_overridden || false,
    _unit_price: localSlot.price || localSlot._unit_price || slot.price || 0,
    // Preserve extra fields for business rules
    manager: localSlot.manager || localSlot.gestore || '',
    activity_type: localSlot.activity_type || '',
  }
  rideLoading.value = false
}, { deep: false })

// ═══════════════════════════════════════════════════════════
// Override / Semaforo — Supabase diretto
// ═══════════════════════════════════════════════════════════
async function setOverride(status) {
  const rideId = currentSlotId.value
  if (!rideId || String(rideId).startsWith('ghost')) return

  try {
    const { error } = await supabase.from('rides').update({
      status: status,
      is_overridden: true
    }).eq('id', rideId)
    if (error) throw error

    const localSlot = store.dailySchedule.find(r => r.id === rideId)
    if (localSlot) {
      localSlot.status = status
      localSlot.is_overridden = true
      localSlot.engine_status = status === 'A' ? 'VERDE' : status === 'B' ? 'GIALLO' : status === 'C' ? 'ROSSO' : 'BLU'
      localSlot.status_desc = status === 'A' ? 'Disponibile' : status === 'B' ? 'Quasi Pieno' : status === 'C' ? 'Pieno / Chiuso' : 'Fuori Stagione'
    }
    if (localRide.value && localRide.value.id === rideId) {
      localRide.value.status = status
      localRide.value.is_overridden = true
    }

    $q.notify({ type: 'positive', message: 'Stato forzato ☁️' })
    emit('refresh')
  } catch (e) {
    console.error('[setOverride] Errore Supabase:', e)
    $q.notify({ type: 'negative', message: 'Errore override: ' + (e.message || e) })
  }
}

async function clearOverride() {
  const rideId = currentSlotId.value
  if (!rideId || String(rideId).startsWith('ghost')) return

  try {
    const { error } = await supabase.from('rides').update({
      status: 'Disponibile',
      is_overridden: false
    }).eq('id', rideId)
    if (error) throw error

    const localSlot = store.dailySchedule.find(r => r.id === rideId)
    if (localSlot) {
      localSlot.is_overridden = false
      const pax = localSlot.booked_pax || 0
      const max = localSlot.total_capacity || 16
      localSlot.engine_status = pax >= max ? 'ROSSO' : pax >= max * 0.75 ? 'GIALLO' : 'VERDE'
      localSlot.status_desc = pax >= max ? 'Pieno / Chiuso' : pax >= max * 0.75 ? 'Quasi Pieno' : 'Disponibile'
      localSlot.status = localSlot.engine_status === 'ROSSO' ? 'C' : localSlot.engine_status === 'GIALLO' ? 'B' : 'A'
    }
    if (localRide.value && localRide.value.id === rideId) {
      localRide.value.is_overridden = false
    }

    $q.notify({ type: 'positive', message: 'Semaforo automatico ripristinato ☁️' })
    emit('refresh')
  } catch (e) {
    console.error('[clearOverride] Errore Supabase:', e)
    $q.notify({ type: 'negative', message: 'Errore reset: ' + (e.message || e) })
  }
}

// ═══════════════════════════════════════════════════════════
// ORDINI — Azioni inline (Supabase diretto)
// ═══════════════════════════════════════════════════════════
async function confirmBonifico(orderId) {
  confirmingOrderId.value = orderId
  try {
    const { error } = await supabase.from('orders').update({ status: 'CONFERMATO' }).eq('id', orderId)
    if (error) throw error

    if (localRide.value && localRide.value.orders) {
      const localOrder = localRide.value.orders.find(o => o.id === orderId)
      if (localOrder) localOrder.order_status = 'CONFERMATO'
    }

    $q.notify({ type: 'positive', message: 'Bonifico confermato! 👻→✅', icon: 'check_circle' })
    emit('refresh')
  } catch(e) {
    console.error('[confirmBonifico] Errore Supabase:', e)
    $q.notify({ type: 'negative', message: 'Errore nella conferma: ' + (e.message || e) })
  } finally {
    confirmingOrderId.value = null
  }
}

async function onOrderStatusChange(order, newStatus) {
  try {
    const { error } = await supabase.from('orders').update({ status: newStatus }).eq('id', order.id)
    if (error) throw error
    order.order_status = newStatus
    $q.notify({ type: 'positive', message: `Stato aggiornato: ${newStatus} ☁️` })
  } catch(e) {
    console.error('[onOrderStatusChange] Errore Supabase:', e)
    $q.notify({ type: 'negative', message: 'Errore aggiornamento stato: ' + (e.message || e) })
  }
}

function onPaxChange(order, val) {
  const originalPax = order.total_pax || 0
  order._actual_pax = val
  const diff = originalPax - val
  order._penalty_amount = diff > 0 ? diff * 20 : 0
  syncRideState()
}

// MAGIC LINK / QR / WHATSAPP — delegato a useCheckin composable

// ═══════════════════════════════════════════════════════════
// PARTECIPANTI
// ═══════════════════════════════════════════════════════════
// eslint-disable-next-line no-unused-vars
function openParticipantsDialog(order) {
  if (order) selectedOrder.value = order
  selectedRegistrations.value = []
  showParticipantsDialog.value = true
}

function toggleRegistration(regId) {
  const idx = selectedRegistrations.value.indexOf(regId)
  if (idx > -1) selectedRegistrations.value.splice(idx, 1)
  else selectedRegistrations.value.push(regId)
}

async function tesseraSelezionati() {
  if (selectedRegistrations.value.length === 0) return
  tesseringInProgress.value = true
  try {
    const res = await api.post('/firaft/register-bulk', { registration_ids: selectedRegistrations.value })
    $q.notify({ type: 'positive', message: `Tesserati ${res.data.updated_count} partecipanti! 🎫`, caption: res.data.details?.join(', ') })
    selectedRegistrations.value = []
    emit('refresh')
  } catch {
    $q.notify({ type: 'negative', message: 'Errore tesseramento' })
  } finally {
    tesseringInProgress.value = false
  }
}

// ═══════════════════════════════════════════════════════════
// DETTAGLIO PARTECIPANTE
// ═══════════════════════════════════════════════════════════
function openParticipantForm(reg) {
  selectedParticipant.value = reg
  partForm.nome = reg.nome || ''
  partForm.cognome = reg.cognome || ''
  partForm.email = reg.email || ''
  partForm.telefono = reg.telefono || ''
  partForm.data_nascita = reg.data_nascita || ''
  partForm.sesso = reg.sesso || ''
  partForm.is_minor = reg.is_minor || false
  partForm.residenza = reg.residenza || ''
  partForm.firaft_status = reg.firaft_status || 'NON_RICHIESTO'
  partForm.consenso_privacy = reg.consenso_privacy || false
  partForm.consenso_foto = reg.consenso_foto || false
  partForm.consenso_medico = reg.consenso_medico || false
  showParticipantFormDialog.value = true
}

// ═══════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════
function getEffectivePax(order) {
  return order._actual_pax !== undefined ? order._actual_pax : (order.total_pax || order.pax || 0)
}

function emptySlotCount(order) {
  const regs = order.registrations?.length || 0
  const refSlot = order.customer_name ? 1 : 0
  const maxPax = Math.max(order.total_pax || order.pax || 0, order._actual_pax || 0)
  return Math.max(0, maxPax - regs - refSlot)
}

function orderStatusColor(status) {
  if (status === 'CONFERMATO') return 'green'
  if (status === 'CANCELLATO') return 'red'
  if (status === 'COMPLETATO') return 'blue'
  if (status === 'DA_SALDARE') return 'deep-orange'
  if (status === 'MANUALE') return 'purple'
  return 'orange'
}

function firaftIcon(status) {
  if (status === 'TESSERATO') return 'verified'
  if (status === 'DA_TESSERARE') return 'hourglass_empty'
  if (status === 'RIFIUTATO') return 'cancel'
  return 'remove_circle_outline'
}

function firaftColor(status) {
  if (status === 'TESSERATO') return 'green'
  if (status === 'DA_TESSERARE') return 'grey'
  if (status === 'RIFIUTATO') return 'red'
  return 'blue-grey'
}

function firaftLabel(status) {
  if (status === 'TESSERATO') return 'Tesserato ✅'
  if (status === 'DA_TESSERARE') return 'Da tesserare'
  if (status === 'RIFIUTATO') return 'Rifiutato'
  return 'Non richiesto'
}

function isFiraftRequired(ride) {
  if (!ride) return false
  const manager = String(ride.manager || ride.gestore || '').toLowerCase()
  if (manager.includes('anatre')) return true
  if (manager.includes('grape')) return false
  const name = String(ride.activity_name || ride.activity_type || ride.title || '').toLowerCase()
  if (name.includes('family') || name.includes('anatre')) return true
  return false
}

// ═══════════════════════════════════════════════════════════
// SINCRONIZZAZIONE PAX (Semafori)
// ═══════════════════════════════════════════════════════════
function updateSemaphore(rideObj, paxTotal) {
  if (!rideObj) return
  const max = rideObj.total_capacity || rideObj.max_pax || 16
  rideObj.booked_pax = paxTotal
  if (paxTotal >= max) {
    rideObj.engine_status = 'ROSSO'
    rideObj.status_desc = 'Pieno / Chiuso'
  } else if (paxTotal >= max - 4 && paxTotal > 0) {
    rideObj.engine_status = 'GIALLO'
    rideObj.status_desc = 'Quasi Pieno'
  } else {
    rideObj.engine_status = 'VERDE'
    rideObj.status_desc = 'Disponibile'
  }
}

function syncRideState() {
  const rideId = localRide.value?.id
  if (!rideId) return
  const globalRide = store.dailySchedule.find(r => r.id === rideId)

  const totalPax = (localRide.value.orders || []).reduce((sum, order) => {
    const pax = order._actual_pax !== undefined && order._actual_pax !== null
      ? order._actual_pax
      : (order.total_pax || order.pax || 1)
    return sum + Number(pax)
  }, 0)

  updateSemaphore(localRide.value, totalPax)

  if (globalRide) {
    globalRide.orders = JSON.parse(JSON.stringify(localRide.value.orders))
    updateSemaphore(globalRide, totalPax)
  }
}

function deleteCustomRideLocally() {
  const ride = localRide.value
  if (!ride || !String(ride.id).startsWith('custom')) return
  $q.dialog({
    title: 'Cancella Turno Extra',
    message: 'Vuoi eliminare questo turno fuori standard e liberare tutte le risorse associate?',
    cancel: { flat: true, label: 'Annulla' },
    ok: { color: 'negative', label: 'Elimina Turno', unelevated: true },
    persistent: true,
  }).onOk(() => {
    isOpen.value = false
    localRide.value = null
    const idx = store.dailySchedule.findIndex(r => r.id === ride.id)
    if (idx !== -1) store.dailySchedule.splice(idx, 1)
    $q.notify({ type: 'positive', message: 'Turno extra eliminato', icon: 'delete' })
  })
}
</script>

<style scoped>
.semaphore-group .q-btn { min-width: 52px; font-size: 10px; }

.ride-dialog-card {
  display: flex !important;
  flex-direction: column !important;
  width: 1000px;
  max-width: 90vw;
  max-height: 90vh;
  border-radius: 8px;
  overflow: hidden;
}
.ride-dialog-card > * {
  flex-shrink: 0;
  width: 100% !important;
}
.ride-dialog-card > .col {
  flex-shrink: 1;
  flex-grow: 1;
  min-height: 0;
}
</style>
