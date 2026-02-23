<template>
  <q-page class="q-pa-md bg-grey-2">
    <!-- Header Pagina -->
    <div class="row items-center justify-between q-mb-md">
      <div class="text-h5 text-weight-bold text-blue-grey-9">
        {{ isSegreteria ? 'Segreteria (POS)' : 'Calendario Operativo' }}
      </div>
      <div class="row q-gutter-sm items-center">
        <!-- Filtri Visivi Globali -->
        <q-btn-group outline>
          <q-btn :color="viewFilter === 'discese' ? 'primary' : 'white'" :text-color="viewFilter === 'discese' ? 'white' : 'grey-8'" label="DISCESE" @click="viewFilter = 'discese'" size="sm" />
          <q-btn :color="viewFilter === 'staff' ? 'primary' : 'white'" :text-color="viewFilter === 'staff' ? 'white' : 'grey-8'" label="STAFF" @click="viewFilter = 'staff'" size="sm" />
          <q-btn :color="viewFilter === 'tutto' ? 'primary' : 'white'" :text-color="viewFilter === 'tutto' ? 'white' : 'grey-8'" label="TUTTO" @click="viewFilter = 'tutto'" size="sm" />
        </q-btn-group>
        <q-btn color="blue-grey" icon="tune" label="Configura Stagione" outline @click="seasonDialog.isOpen = true" />
        <q-btn color="primary" icon="add" label="Nuova Prenotazione" unelevated @click="openBookingForm(null, null)" />
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- VISTA MESE — Calendario mensile con mattoncini cliccabili         -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <div v-if="viewMode === 'MONTH'" class="fit-height-card">
      <CalendarComponent
        :year="currentYear"
        :month="currentMonth"
        :month-data="monthOverview"
        :view-filter="viewFilter"
        v-model:viewMode="calendarDisplayMode"
        @update:month="changeMonth"
        @day-click="openDayDetail"
        @ride-click="onRideClickFromMonth"
      />
    </div>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- VISTA GIORNO — Dettaglio turni                                    -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <div v-else class="column" style="min-height: calc(100vh - 140px);">
      <!-- Header navigazione giornaliera -->
      <div class="row items-center q-mb-md q-gutter-sm">
        <q-btn flat icon="arrow_back" label="Torna al Mese" color="primary" @click="goToMonthView" />
        <q-separator vertical class="q-mx-sm" />
        <q-btn round flat icon="chevron_left" @click="prevDay" color="primary" />
        <span class="text-h6 text-weight-bold text-uppercase q-mx-md">{{ formatSelectedDate }}</span>
        <q-btn round flat icon="chevron_right" @click="nextDay" color="primary" />
        <q-space />
        <q-btn outline icon="download" label="Export FIRAFT (CSV)" color="teal" size="sm" @click="exportFiraft" />
      </div>

      <!-- Griglia turni — OPERATIVO -->
      <div v-if="!isSegreteria" class="col scroll">
        <div v-if="store.loading" class="flex flex-center" style="min-height: 300px;"><q-spinner size="3em" color="primary" /></div>
        <div v-else-if="!filteredDailySchedule || filteredDailySchedule.length === 0" class="flex flex-center text-grey-5 column" style="min-height: 300px;">
          <q-icon name="event_busy" size="4em" />
          <div class="text-h6 q-mt-sm">Nessuna attività programmata per oggi.</div>
        </div>

        <div v-else class="row q-col-gutter-md justify-center">
          <div class="col-12 col-sm-6 col-md-4 col-lg-3" v-for="(slot, idx) in filteredDailySchedule" :key="idx">
            <q-card bordered class="slot-card transition-generic cursor-pointer" :style="{ opacity: slot.booked_pax === 0 ? 0.85 : 1 }" @click="openRideDialog(slot)" v-ripple>
              <q-item>
                <q-item-section avatar>
                  <q-avatar :style="{ backgroundColor: slot.color_hex }" text-color="white" size="48px" font-size="13px">{{ slot.time?.slice(0,5) }}</q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">{{ slot.activity_type }}</q-item-label>
                  <q-item-label caption>
                    <span :style="{ color: slot.color_hex, fontWeight: 'bold' }">{{ slot.status_desc }}</span>
                    <q-icon v-if="slot.is_overridden" name="lock" size="xs" color="grey-6" class="q-ml-xs" />
                  </q-item-label>
                </q-item-section>
              </q-item>
              <q-separator />
              <q-card-section class="q-pa-sm text-center" :class="getSlotBgClass(slot)" v-show="viewFilter === 'tutto' || viewFilter === 'discese'">
                <span class="text-h5 text-weight-bold" :style="{ color: slot.color_hex }">{{ slot.booked_pax }}</span>
                <span class="text-caption text-grey-6 q-ml-xs">/ {{ slot.total_capacity || '—' }} pax</span>
                <q-linear-progress :value="Math.min(1, (slot.booked_pax || 0) / Math.max(1, slot.total_capacity || 16))" :color="getProgressBarColor(slot.booked_pax, slot.total_capacity || 16)" class="q-mt-xs" rounded />
              </q-card-section>
              <!-- Badge Risorse Assegnate -->
              <q-card-section class="q-pa-xs q-pt-none" v-show="viewFilter === 'tutto' || viewFilter === 'staff'">
                <div class="row q-gutter-xs q-mb-xs wrap" v-if="slot.assigned_guides?.length > 0 || slot.assigned_boats?.length > 0 || slot.assigned_vans?.length > 0 || slot.assigned_trailers?.length > 0">
                  <q-badge color="blue-grey-1" text-color="blue-grey-9" v-if="slot.assigned_guides?.length > 0">
                    <q-icon name="person" class="q-mr-xs" size="14px" /> {{ slot.assigned_guides.length }} Guide
                  </q-badge>
                  <q-badge color="light-blue-1" text-color="light-blue-9" v-if="slot.assigned_boats?.length > 0">
                    <q-icon name="rowing" class="q-mr-xs" size="14px" /> {{ slot.assigned_boats.length }} Gommoni
                  </q-badge>
                  <q-badge color="orange-1" text-color="orange-10" v-if="slot.assigned_vans?.length > 0">
                    <q-icon name="directions_bus" class="q-mr-xs" size="14px" /> {{ slot.assigned_vans.length }} Furgoni
                  </q-badge>
                  <q-badge color="brown-1" text-color="brown-10" v-if="slot.assigned_trailers?.length > 0">
                    <q-icon name="rv_hookup" class="q-mr-xs" size="14px" /> {{ slot.assigned_trailers.length }} Carrelli
                  </q-badge>
                </div>
                <div class="row q-gutter-xs q-mb-xs" v-if="slot.assigned_staff?.length || slot.assigned_fleet?.length">
                  <q-chip v-for="s in slot.assigned_staff" :key="'s'+s.id" dense icon="person" color="blue-1" text-color="primary" size="sm">{{ s.name }}</q-chip>
                  <q-chip v-for="f in slot.assigned_fleet" :key="'f'+f.id" dense :icon="f.category === 'RAFT' ? 'rowing' : 'local_shipping'" :color="f.category === 'RAFT' ? 'teal-1' : 'orange-1'" :text-color="f.category === 'RAFT' ? 'teal-9' : 'orange-9'" size="sm">{{ f.name }}</q-chip>
                </div>
                <q-btn flat dense icon="groups" label="Assegna Risorse" color="primary" class="full-width" size="sm" @click.stop="openResourcePanel(slot)" />
              </q-card-section>
            </q-card>
          </div>
        </div>
        <!-- Legenda Stati -->
        <div class="q-mt-lg q-pa-sm">
          <div class="row wrap justify-center q-gutter-md items-center text-caption text-grey-7">
            <div class="row items-center"><q-badge color="green" class="q-mr-xs" /> Da Caricare</div>
            <div class="row items-center"><q-badge color="blue" class="q-mr-xs" /> Confermato</div>
            <div class="row items-center"><q-badge color="amber" class="q-mr-xs" /> Quasi Pieno</div>
            <div class="row items-center"><q-badge color="red" class="q-mr-xs" /> Pieno / Chiuso</div>
          </div>
        </div>
      </div>

      <!-- Contenuto SEGRETERIA -->
      <div v-else class="col scroll">
        <DeskDashboardPage :external-date="selectedDate ? selectedDate.replace(/\//g, '-') : null" :hide-calendar="true" />
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- MODALE CENTRALE — Dettaglio Turno (popup con overlay scuro)       -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <q-dialog v-model="showRideDialog">
      <q-card class="ride-dialog-card">
        <!-- Header dinamico con colore basato su stato -->
        <q-card-section :class="rideHeaderBgClass" class="text-white q-py-sm col-auto">
          <div class="row items-center justify-between">
            <div>
              <div class="text-h6">{{ rideData?.activity_name }}</div>
              <div class="text-caption">
                {{ rideData?.ride_date }} · {{ rideData?.ride_time }}
                <q-badge color="white" text-color="dark" class="q-ml-sm text-weight-bold">
                  {{ rideData?.booked_pax || 0 }} / {{ rideData?.max_pax || '—' }} pax
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
                <q-btn unelevated dense color="blue-7" text-color="white" icon="add" label="NUOVA PRENOTAZIONE" size="sm" @click.stop="openBookingForm(null, rideData)" />
                <q-btn unelevated dense color="red-7" text-color="white" icon="delete" label="CANCELLA ORARIO" size="sm"
                  v-if="String(rideData?.id || '').startsWith('custom')"
                  @click.stop="deleteCustomRideLocally(rideData)" />
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

        <!-- Loading -->
        <div v-if="rideLoading" class="flex flex-center q-pa-xl col">
          <q-spinner size="3em" color="primary" />
        </div>

        <!-- Corpo: Ordini a Fisarmonica -->
        <q-card-section v-else-if="rideData" class="col scroll q-pa-none" style="overflow-x: hidden; min-height: 0;">
          <div v-if="!rideData.orders || rideData.orders.length === 0" class="text-center text-grey q-pa-xl">
            <q-icon name="event_seat" size="4em" />
            <div class="q-mt-sm text-h6">Nessun ordine per questo turno</div>
          </div>

          <q-list v-else separator class="q-pa-sm">
            <q-expansion-item
              v-for="order in rideData.orders"
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
                    <q-btn outline dense color="primary" icon="group" label="PARTECIPANTI" size="sm" @click.stop="openFiraftModal(order)" />
                    <q-btn outline dense color="primary" icon="edit" label="MODIFICA" size="sm" @click.stop="openBookingForm(order)" />
                    <q-btn outline dense color="negative" icon="delete" size="sm" @click.stop="deleteOrderLocally(rideData, order)" title="Cancella Prenotazione" />
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
                      <q-btn outline dense color="primary" icon="edit" label="MODIFICA" @click.stop="openBookingForm(order)" class="q-mb-xs full-width" />
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
                          @click="syncRideState(rideData?.id); $q.notify({ type: 'positive', message: 'Drop-outs e Pax ricalcolati ✅' })" />
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
                    <!-- Lista pagamenti (fittizia) -->
                    <q-list bordered dense class="rounded-borders bg-white q-mb-sm" v-if="order.paid_amount > 0">
                      <q-item dense>
                        <q-item-section avatar><q-icon name="payment" color="green" /></q-item-section>
                        <q-item-section>€ {{ (order.paid_amount || 0).toFixed(2) }} — SUMUP</q-item-section>
                        <q-item-section side class="text-caption text-grey">{{ rideData?.ride_date }}</q-item-section>
                      </q-item>
                    </q-list>
                    <div v-else class="text-caption text-grey-4 q-mb-sm">Nessun pagamento registrato</div>
                    <!-- Form rapido pagamento -->
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
                      @blur="rideData ? syncRideState(rideData.id) : null"
                    />
                  </div>

                  <q-separator />

                  <!-- ─── E) Lista Partecipanti ─── -->
                  <div>
                    <div class="row justify-between items-center q-mb-sm">
                      <div class="text-subtitle2 text-blue-grey-8"><q-icon name="group" class="q-mr-xs" />Lista Partecipanti</div>
                      <q-btn v-if="isFiraftRequired(rideData)" size="sm" color="positive" text-color="white" label="TESSERA SELEZIONATI" icon="security" @click="openFiraftModal(order)" />
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
        </q-card-section>
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



    <SeasonConfigDialog ref="seasonDialog" />

    <!-- Pannello Risorse (componente isolato) -->
    <ResourcePanel v-model="resourcePanelOpen" :ride="activeResourceSlot" @saved="onResourcePanelSaved" />

    <!-- Dialog Partecipanti del Turno (accesso rapido dalla card) -->
    <q-dialog v-model="slotParticipantsDialog.open">
      <q-card style="width: 500px; max-width: 95vw;">
        <q-card-section class="bg-teal-8 text-white row items-center justify-between q-py-sm">
          <div>
            <div class="text-h6">Lista Partecipanti</div>
            <div class="text-caption" v-if="slotParticipantsDialog.slot">{{ slotParticipantsDialog.slot.activity_type }} — {{ slotParticipantsDialog.slot.time?.slice(0,5) }}</div>
          </div>
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-separator />
        <q-card-section class="text-center text-grey-5 q-pa-lg">
          <q-icon name="construction" size="3em" class="q-mb-sm" />
          <div>Apri il dettaglio turno per visualizzare i partecipanti dei singoli ordini.</div>
          <q-btn class="q-mt-md" color="primary" label="Apri Dettaglio Turno" unelevated @click="slotParticipantsDialog.open = false; openRideDialog(slotParticipantsDialog.slot)" />
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Smart Modal: Prenotazione (componente isolato) -->
    <BookingDialog
      v-model="bookingDialogOpen"
      :ride-context="bookingRideContext"
      :edit-order="bookingEditOrder"
      :selected-date="selectedDate"
      @saved="onBookingSaved"
    />

    <!-- FIRAFT Dialog (componente isolato) -->
    <FiraftDialog
      v-model="firaftModalOpen"
      :order="activeFiraftOrder"
      :ride-context="rideData"
      @registered="onFiraftRegistered"
    />

    <!-- ═══ MODALE QR CODE (Magic Link) ═══ -->
    <q-dialog v-model="qrDialogForLink.open">
      <q-card style="width: 350px; text-align: center;" class="q-pa-md">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6"><q-icon name="qr_code" class="q-mr-sm" />Scansiona per Check-in</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>
        <q-card-section class="flex flex-center q-pt-md">
          <img v-if="qrDialogForLink.url" :src="qrDialogForLink.url" style="width: 300px; height: 300px; margin: 0 auto;" alt="QR Code" />
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { supabase } from 'src/supabase'
import { useRoute } from 'vue-router'
import { useResourceStore } from 'stores/resource-store'
import { useQuasar, date as qdate } from 'quasar'
import { api } from 'boot/axios'
import CalendarComponent from 'components/CalendarComponent.vue'
import SeasonConfigDialog from 'components/SeasonConfigDialog.vue'
import ResourcePanel from 'components/ResourcePanel.vue'
import BookingDialog from 'components/BookingDialog.vue'
import FiraftDialog from 'components/FiraftDialog.vue'
import DeskDashboardPage from 'pages/DeskDashboardPage.vue'

const route = useRoute()
const store = useResourceStore()
const $q = useQuasar()
const seasonDialog = ref(null)
const selectedDate = ref(new Date().toISOString().split('T')[0].replace(/-/g, '/'))

// Ambiente determinato dalla rotta
const isSegreteria = computed(() => route.path.includes('segreteria'))

// Opzioni stato ordine per il q-select nel cruscotto
const orderStatusOptions = [
  { label: 'Confermato', value: 'CONFERMATO' },
  { label: 'In Attesa (Fantasma)', value: 'IN_ATTESA' },
  { label: 'Da Saldare', value: 'DA_SALDARE' },
  { label: 'Manuale', value: 'MANUALE' },
  { label: 'Completato', value: 'COMPLETATO' },
  { label: 'Cancellato', value: 'CANCELLATO' },
]

// Slot Participants Dialog (accesso rapido da card turno)
const slotParticipantsDialog = reactive({ open: false, slot: null })

// Smart Modal: Booking (delegato a BookingDialog.vue)
const bookingDialogOpen = ref(false)
const bookingRideContext = ref(null)
const bookingEditOrder = ref(null)

// Resource Panel State (from Supabase)
const resourcePanelOpen = ref(false)
const activeResourceSlot = ref(null)


// Calendar view state
const viewMode = ref('MONTH')
const calendarDisplayMode = ref('DESCENTS')
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const monthOverview = ref([])

// Filtri visivi (DISCESE / STAFF / TUTTO)
const viewFilter = ref('tutto')
const filteredDailySchedule = computed(() => {
  if (viewFilter.value === 'discese') {
    // Nasconde gli slot vuoti, mostra solo quelli con pax o ordini
    return store.dailySchedule.filter(slot => slot.booked_pax > 0 || (slot.orders && slot.orders.length > 0))
  }
  // Staff o Tutto: mostra l'ossatura completa inclusi slot vuoti
  return store.dailySchedule
})

// Smart Default: cambia filtro in base alla vista
watch(viewMode, (newVal) => {
  if (newVal === 'MONTH') {
    viewFilter.value = 'tutto'
  } else {
    viewFilter.value = 'tutto'
  }
}, { immediate: true })

// FIRAFT Simulator State
const firaftModalOpen = ref(false)
const activeFiraftOrder = ref(null)
// Ride Dialog State
const showRideDialog = ref(false)
const rideData = ref(null)
const rideLoading = ref(false)
const currentSlotId = ref(null)
const currentSlotData = computed(() => store.dailySchedule.find(s => s.id === currentSlotId.value) || null)

// Header dinamico modale
const rideHeaderBgClass = computed(() => {
  const status = rideData.value?.status || currentSlotData.value?.engine_status
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

// Opzioni tendine per Smart Modal



// ═══════════════════════════════════════════════════════════
// COMPUTED
// ═══════════════════════════════════════════════════════════
const formatSelectedDate = computed(() => {
  if (!selectedDate.value) return ''
  const d = new Date(selectedDate.value.replace(/\//g, '-'))
  return d.toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
})

// ═══════════════════════════════════════════════════════════
// LIFECYCLE
// ═══════════════════════════════════════════════════════════
onMounted(async () => {
  $q.loading.show({ message: 'Inizializzazione...' })
  try {
    // Carica cataloghi Supabase PRIMA di tutto (servono per i ghost slots)
    await store.fetchCatalogs()
    console.log('🟢 [SUPABASE] Attività:', store.activities.length, '| Risorse:', store.resources.length)

    await Promise.all([
      store.fetchActivityRules(),
      store.fetchStaff(),
      store.fetchFleet(),
    ])
    const [y, m] = selectedDate.value.split('/')
    currentYear.value = parseInt(y)
    currentMonth.value = parseInt(m)
    await updateMonthOverview(currentYear.value, currentMonth.value)

    $q.notify({ type: 'positive', message: '🔄 Sincronizzazione completata', position: 'top', timeout: 2000 })
  } catch(e) {
    console.error('Error in PlanningPage mounted', e)
    $q.notify({
      type: 'negative',
      message: `Errore inizializzazione: ${e.message || 'sconosciuto'}`,
      position: 'top',
      timeout: 0,
      actions: [{ icon: 'close', color: 'white' }]
    })
  } finally {
    $q.loading.hide()
  }
})

// ═══════════════════════════════════════════════════════════
// CALENDAR NAVIGATION
// ═══════════════════════════════════════════════════════════
async function updateMonthOverview(year, month) {
  $q.loading.show({ message: 'Aggiornamento calendario...' })
  try {
    const data = await store.fetchMonthOverviewSupabase(year, month)
    monthOverview.value = Array.isArray(data) ? data : []
    console.log('[PlanningPage] monthOverview aggiornato:', monthOverview.value.length, 'giorni')
  } catch(e) {
    console.error(e)
    monthOverview.value = []
    $q.notify({ type: 'negative', message: 'Errore caricamento calendario' })
  } finally {
    $q.loading.hide()
  }
}

function changeMonth(m, y) { currentMonth.value = m; currentYear.value = y; updateMonthOverview(y, m) }
function goToMonthView() { viewMode.value = 'MONTH'; updateMonthOverview(currentYear.value, currentMonth.value) }
function openDayDetail(data) {
  if (!data) return
  const dateStr = data?.scope?.timestamp?.date || data?.timestamp?.date || data?.date || data
  if (dateStr && typeof dateStr === 'string') {
    selectedDate.value = String(dateStr).replace(/-/g, '/')
    viewMode.value = 'DETAIL'
    loadSchedule()
  }
}

// Shortcut: click su mattoncino nel mese → apri direttamente la modale turno
async function onRideClickFromMonth({ date, ride }) {
  // Prima carica il giorno per avere i dati del daily schedule
  selectedDate.value = date.replace(/-/g, '/')
  viewMode.value = 'DETAIL'
  await loadSchedule()
  // Trova lo slot corrispondente nel daily schedule
  const slot = store.dailySchedule.find(s =>
    s.time?.startsWith(ride.time) || s.activity_type === ride.activity_code
  )
  if (slot) {
    openRideDialog(slot)
  }
}

// ═══════════════════════════════════════════════════════════
// DAY NAVIGATION
// ═══════════════════════════════════════════════════════════
function prevDay() {
  const current = new Date(selectedDate.value.replace(/\//g, '-'))
  const prev = qdate.subtractFromDate(current, { days: 1 })
  selectedDate.value = qdate.formatDate(prev, 'YYYY/MM/DD')
  currentYear.value = prev.getFullYear()
  currentMonth.value = prev.getMonth() + 1
  loadSchedule()
}

function nextDay() {
  const current = new Date(selectedDate.value.replace(/\//g, '-'))
  const next = qdate.addToDate(current, { days: 1 })
  selectedDate.value = qdate.formatDate(next, 'YYYY/MM/DD')
  currentYear.value = next.getFullYear()
  currentMonth.value = next.getMonth() + 1
  loadSchedule()
}

async function loadSchedule() {
  $q.loading.show({ message: 'Caricamento giornata...' })
  try {
    const d = selectedDate.value.replace(/\//g, '-')
    await store.fetchDailyScheduleSupabase(d)
  } catch(e) { console.error(e); $q.notify({ type: 'negative', message: 'Errore caricamento' }) }
  finally { $q.loading.hide() }
}

// eslint-disable-next-line no-unused-vars
function onReservationSaved() { loadSchedule(); updateMonthOverview(currentYear.value, currentMonth.value) }

// ═══════════════════════════════════════════════════════════
// RIDE DIALOG — Modale Centrale
// ═══════════════════════════════════════════════════════════
async function openRideDialog(slot) {
  showRideDialog.value = true
  rideLoading.value = true
  rideData.value = null
  currentSlotId.value = slot.id

  // ── FULL MOCK MODE ──
  // Disabilita la fetch API per evitare sovrascritture dal mock server.
  // Tutti i dati vengono letti esclusivamente dallo store.dailySchedule locale.
  const localSlot = store.dailySchedule.find(r => r.id === slot.id) || slot

  rideData.value = {
    id: localSlot.id,
    activity_name: localSlot.activity_type || localSlot.title || 'Turno',
    ride_date: selectedDate.value ? String(selectedDate.value).replace(/\//g, '-') : '',
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
  }
  rideLoading.value = false

  // NOTA: Quando il backend sarà pronto, riattivare questa fetch:
  // try {
  //   const res = await api.get(`/calendar/daily-rides/${slot.id}`)
  //   rideData.value = res.data
  // } catch(e) {
  //   console.error(e)
  //   $q.notify({ type: 'negative', message: 'Errore caricamento dettagli discesa' })
  // } finally {
  //   rideLoading.value = false
  // }
}

function reloadRideData() {
  if (!currentSlotId.value) return
  // FULL MOCK MODE: ricarica dallo store locale
  const localSlot = store.dailySchedule.find(r => r.id === currentSlotId.value)
  if (localSlot) {
    rideData.value = {
      ...rideData.value,
      orders: localSlot.orders || [],
      booked_pax: localSlot.booked_pax || 0,
    }
  }
}

// Override / Semaforo — Supabase diretto
async function setOverride(status) {
  const rideId = currentSlotId.value
  if (!rideId || String(rideId).startsWith('ghost')) return

  try {
    const { error } = await supabase.from('rides').update({
      status: status,
      is_overridden: true
    }).eq('id', rideId)
    if (error) throw error

    // Aggiorna lo state locale per reattività istantanea
    const localSlot = store.dailySchedule.find(r => r.id === rideId)
    if (localSlot) {
      localSlot.status = status
      localSlot.is_overridden = true
      localSlot.engine_status = status === 'A' ? 'VERDE' : status === 'B' ? 'GIALLO' : status === 'C' ? 'ROSSO' : 'BLU'
      localSlot.status_desc = status === 'A' ? 'Disponibile' : status === 'B' ? 'Quasi Pieno' : status === 'C' ? 'Pieno / Chiuso' : 'Fuori Stagione'
    }
    if (rideData.value && rideData.value.id === rideId) {
      rideData.value.status = status
      rideData.value.is_overridden = true
    }

    $q.notify({ type: 'positive', message: 'Stato forzato ☁️' })
    updateMonthOverview(currentYear.value, currentMonth.value)
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

    // Ricalcola lo status automatico basato sui pax
    const localSlot = store.dailySchedule.find(r => r.id === rideId)
    if (localSlot) {
      localSlot.is_overridden = false
      const pax = localSlot.booked_pax || 0
      const max = localSlot.total_capacity || 16
      localSlot.engine_status = pax >= max ? 'ROSSO' : pax >= max * 0.75 ? 'GIALLO' : 'VERDE'
      localSlot.status_desc = pax >= max ? 'Pieno / Chiuso' : pax >= max * 0.75 ? 'Quasi Pieno' : 'Disponibile'
      localSlot.status = localSlot.engine_status === 'ROSSO' ? 'C' : localSlot.engine_status === 'GIALLO' ? 'B' : 'A'
    }
    if (rideData.value && rideData.value.id === rideId) {
      rideData.value.is_overridden = false
    }

    $q.notify({ type: 'positive', message: 'Semaforo automatico ripristinato ☁️' })
    updateMonthOverview(currentYear.value, currentMonth.value)
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

    // Aggiorna reattivamente lo stato locale dell'ordine
    if (rideData.value && rideData.value.orders) {
      const localOrder = rideData.value.orders.find(o => o.id === orderId)
      if (localOrder) localOrder.order_status = 'CONFERMATO'
    }

    $q.notify({ type: 'positive', message: 'Bonifico confermato! 👻→✅', icon: 'check_circle' })
    updateMonthOverview(currentYear.value, currentMonth.value)
  } catch(e) {
    console.error('[confirmBonifico] Errore Supabase:', e)
    $q.notify({ type: 'negative', message: 'Errore nella conferma: ' + (e.message || e) })
  } finally {
    confirmingOrderId.value = null
  }
}

// Cambio stato ordine dal q-select
async function onOrderStatusChange(order, newStatus) {
  try {
    const { error } = await supabase.from('orders').update({ status: newStatus }).eq('id', order.id)
    if (error) throw error

    // Aggiorna reattivamente lo stato locale
    order.order_status = newStatus
    $q.notify({ type: 'positive', message: `Stato aggiornato: ${newStatus} ☁️` })
  } catch(e) {
    console.error('[onOrderStatusChange] Errore Supabase:', e)
    $q.notify({ type: 'negative', message: 'Errore aggiornamento stato: ' + (e.message || e) })
  }
}

// Drop-out: calcolo automatico penale (€20/pax mancante), override manuale consentito
function onPaxChange(order, val) {
  const originalPax = order.total_pax || 0
  order._actual_pax = val
  const diff = originalPax - val
  order._penalty_amount = diff > 0 ? diff * 20 : 0
  // Ricalcola pax globali e sincronizza
  if (rideData.value) syncRideState(rideData.value.id)
}

// ═══════════════════════════════════════════════════════════
// MAGIC LINK — Check-in Digitale (Cantiere 3)
// ═══════════════════════════════════════════════════════════
const qrDialogForLink = reactive({ open: false, url: '' })

function getMagicLink(order) {
  if (!order || !order.id) return ''
  const baseUrl = window.location.origin + window.location.pathname
  return `${baseUrl}#/consenso?order_id=${order.id}`
}

function copyMagicLink(order) {
  if (!order || !order.id) return
  navigator.clipboard.writeText(getMagicLink(order))
    .then(() => {
      $q.notify({ type: 'positive', message: 'Link copiato negli appunti!', icon: 'content_copy', position: 'top' })
    })
    .catch(err => console.error('Errore clipboard:', err))
}

function openQrModal(order) {
  if (!order || !order.id) return
  qrDialogForLink.url = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(getMagicLink(order))}`
  qrDialogForLink.open = true
}

function shareWhatsApp(order) {
  if (!order || !order.id) return
  const name = order.customer_name || 'Referente'
  const text = encodeURIComponent(`Ciao ${name}! Ecco il link per compilare velocemente le liberatorie prima della discesa: ${getMagicLink(order)}`)
  window.open(`https://wa.me/?text=${text}`, '_blank')
}

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
    await reloadRideData()
    if (selectedOrder.value && rideData.value) {
      const fresh = rideData.value.orders.find(o => o.id === selectedOrder.value.id)
      if (fresh) selectedOrder.value = fresh
    }
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
// SMART MODAL: Booking (Nuovo / Modifica)
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

function openBookingForm(order, contextRide) {
  // Vaccino anti-Event: se Vue passa un MouseEvent come argomento, azzeralo
  if (order instanceof Event || (order && typeof order === 'object' && order.type === 'click')) order = null
  if (contextRide instanceof Event || (contextRide && typeof contextRide === 'object' && contextRide.type === 'click')) contextRide = null

  bookingEditOrder.value = order || null
  bookingRideContext.value = contextRide || rideData.value || null
  bookingDialogOpen.value = true
}

async function onBookingSaved() {
  // Ricarica daily schedule e month overview dopo salvataggio
  const dateStr = selectedDate.value.replace(/\//g, '-')
  await store.fetchDailyScheduleSupabase(dateStr)
  const [yyyy, mm] = dateStr.split('-')
  const monthData = await store.fetchMonthOverviewSupabase(parseInt(yyyy), parseInt(mm))
  monthOverview.value = Array.isArray(monthData) ? monthData : []
  // Se la modale turno è aperta, aggiorna i dati del turno visualizzato
  if (showRideDialog.value && rideData.value) {
    const freshSlot = store.dailySchedule.find(s => s.id === rideData.value.id)
    if (freshSlot) Object.assign(rideData.value, freshSlot)
    syncRideState(rideData.value?.id)
  }
}
// ═══════════════════════════════════════════════════════════
// CANCELLAZIONE REALE SU SUPABASE (con cleanup ride vuota)
// ═══════════════════════════════════════════════════════════
function deleteOrderLocally(ride, order) {
  $q.dialog({
    title: 'Cancella Prenotazione',
    message: `Confermi la cancellazione dell'ordine di ${order.customer_name || 'Senza nome'} (${order.total_pax || 1} pax)? L'azione è irreversibile.`,
    cancel: { flat: true, label: 'Annulla' },
    ok: { color: 'negative', label: 'Cancella', unelevated: true },
    persistent: true,
  }).onOk(async () => {
    try {
      // 1. Elimina l'ordine dal DB
      if (order.id && typeof order.id === 'string' && order.id.length > 10) {
        const { error } = await supabase.from('orders').delete().eq('id', order.id)
        if (error) throw error
      }

      // 2. Se era l'ultimo ordine del ride, elimina anche il ride
      const remainingOrders = (ride?.orders || []).filter(o => o.id !== order.id)
      if (remainingOrders.length === 0 && ride?.id && typeof ride.id === 'string' && ride.id.length > 10) {
        // Prima elimina eventuali allocazioni
        await supabase.from('ride_allocations').delete().eq('ride_id', ride.id)
        // Poi elimina il ride
        const { error: rideErr } = await supabase.from('rides').delete().eq('id', ride.id)
        if (rideErr) console.warn('Errore cleanup ride:', rideErr)
      }

      // 3. Ricarica dati dal DB
      const dateStr = selectedDate.value.replace(/\//g, '-')
      await store.fetchDailyScheduleSupabase(dateStr)
      const [yyyy, mm] = dateStr.split('-')
      const monthData2 = await store.fetchMonthOverviewSupabase(parseInt(yyyy), parseInt(mm))
      monthOverview.value = Array.isArray(monthData2) ? monthData2 : []

      // 4. Aggiorna la modale se aperta
      if (showRideDialog.value && rideData.value && rideData.value.id === ride?.id) {
        const freshSlot = store.dailySchedule.find(s => s.id === ride.id)
        if (freshSlot) {
          Object.assign(rideData.value, freshSlot)
        } else {
          // Il ride è stato eliminato, chiudi la modale
          showRideDialog.value = false
        }
      }

      $q.notify({ type: 'positive', message: 'Prenotazione eliminata dal cloud ✅', icon: 'delete' })
    } catch (err) {
      console.error('Delete order error:', err)
      $q.notify({ type: 'negative', message: 'Errore eliminazione: ' + err.message })
    }
  })
}

// ═══════════════════════════════════════════════════════════
// SINCRONIZZAZIONE GLOBALE PAX (Vaso Comunicante + Semafori)
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

function syncRideState(rideId) {
  if (!rideId) return
  const globalRide = store.dailySchedule.find(r => r.id === rideId)

  // Se la modale è aperta su questo turno, la fonte della verità è rideData.value
  if (showRideDialog.value && rideData.value && rideData.value.id === rideId) {
    const totalPax = (rideData.value.orders || []).reduce((sum, order) => {
      const pax = order._actual_pax !== undefined && order._actual_pax !== null
        ? order._actual_pax
        : (order.total_pax || order.pax || 1)
      return sum + Number(pax)
    }, 0)

    updateSemaphore(rideData.value, totalPax)

    if (globalRide) {
      // Riversa il clone aggiornato nel tabellone globale
      globalRide.orders = JSON.parse(JSON.stringify(rideData.value.orders))
      updateSemaphore(globalRide, totalPax)
    }
  } else if (globalRide) {
    // Fallback: ricalcolo se la modale è chiusa
    const totalPax = (globalRide.orders || []).reduce((sum, order) => {
      const pax = order._actual_pax !== undefined && order._actual_pax !== null
        ? order._actual_pax
        : (order.total_pax || order.pax || 1)
      return sum + Number(pax)
    }, 0)
    updateSemaphore(globalRide, totalPax)
  }
}

function getProgressBarColor(pax, max = 16) {
  if (pax >= max) return 'negative'
  if (pax >= max - 4 && pax > 0) return 'warning'
  return 'primary'
}

function getSlotBgClass(slot) {
  const pax = slot.booked_pax || 0
  const max = slot.total_capacity || 16
  if (pax >= max) return 'bg-red-1'
  if (pax >= max - 4 && pax > 0) return 'bg-orange-1'
  return 'bg-green-1'
}

function deleteCustomRideLocally(ride) {
  if (!ride || !String(ride.id).startsWith('custom')) return
  $q.dialog({
    title: 'Cancella Turno Extra',
    message: 'Vuoi eliminare questo turno fuori standard e liberare tutte le risorse associate?',
    cancel: { flat: true, label: 'Annulla' },
    ok: { color: 'negative', label: 'Elimina Turno', unelevated: true },
    persistent: true,
  }).onOk(() => {
    // Chiudi modale
    showRideDialog.value = false
    rideData.value = null
    // Rimuovi dallo schedule
    const idx = store.dailySchedule.findIndex(r => r.id === ride.id)
    if (idx !== -1) store.dailySchedule.splice(idx, 1)
    $q.notify({ type: 'positive', message: 'Turno extra eliminato', icon: 'delete' })
  })
}

// ═══════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════
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



// ═══════════════════════════════════════════════════════════
// PANNELLO RISORSE (delegato a ResourcePanel.vue)
// ═══════════════════════════════════════════════════════════
function openResourcePanel(slot) {
  activeResourceSlot.value = slot
  resourcePanelOpen.value = true
}

async function onResourcePanelSaved() {
  // Ricarica daily schedule e aggiorna eventuale modale turno aperta
  const dateStr = selectedDate.value.replace(/\//g, '-')
  await store.fetchDailyScheduleSupabase(dateStr)
  if (showRideDialog.value && rideData.value && activeResourceSlot.value) {
    const freshSlot = store.dailySchedule.find(s => s.id === activeResourceSlot.value.id)
    if (freshSlot) Object.assign(rideData.value, freshSlot)
  }
  updateMonthOverview(currentYear.value, currentMonth.value)
}

// ═══════════════════════════════════════════════════════════
// BUSINESS RULE: Anatre vs Grape (Tesseramento FIRAFT)
// ═══════════════════════════════════════════════════════════
function isFiraftRequired(ride) {
  if (!ride) return false
  const manager = String(ride.manager || ride.gestore || '').toLowerCase()
  if (manager.includes('anatre')) return true
  if (manager.includes('grape')) return false
  // Fallback Mock: 'Rafting Family' gestito da Anatre, il resto da Grape
  const name = String(ride.activity_name || ride.activity_type || ride.title || '').toLowerCase()
  if (name.includes('family') || name.includes('anatre')) return true
  return false
}

// Export FIRAFT CSV
function exportFiraft () {
  const d = selectedDate.value.replace(/\//g, '-')
  window.open(`/api/v1/calendar/daily-rides/export-firaft?date=${d}`, '_blank')
}

// ═══════════════════════════════════════════════════════════
// SIMULATORE FIRAFT (delegato a FiraftDialog.vue)
// ═══════════════════════════════════════════════════════════
function openFiraftModal(order) {
  if (!order) return
  activeFiraftOrder.value = order
  firaftModalOpen.value = true
}

async function onFiraftRegistered() {
  // Ricarica daily schedule dopo tesseramento
  const dateStr = selectedDate.value.replace(/\//g, '-')
  await store.fetchDailyScheduleSupabase(dateStr)
  if (showRideDialog.value && rideData.value) {
    const freshSlot = store.dailySchedule.find(s => s.id === rideData.value.id)
    if (freshSlot) Object.assign(rideData.value, freshSlot)
  }
}
</script>

<style scoped>
.fit-height-card { min-height: calc(100vh - 140px); }
.slot-card { transition: transform 0.2s; }
.slot-card:hover { transform: translateY(-3px); box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
.transition-generic { transition: all 0.3s ease; }
.semaphore-group .q-btn { min-width: 52px; font-size: 10px; }

/* ═══ Modale Turno: forzatura layout verticale ═══ */
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

@media (max-width: 600px) {
  .q-pa-md { padding: 8px; }
}
</style>
