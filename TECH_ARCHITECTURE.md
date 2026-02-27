# TECH ARCHITECTURE - RAFTING REPUBLIC

Ultimo aggiornamento: 27/02/2026 16:53 (Documento Definitivo — Fase 6.J)

1. # STACK TECNOLOGICO

Frontend:

- Framework: Vue 3 (Composition API, <script setup>)
- UI Kit: Quasar Framework v2.18.6
- State Management: Pinia (resource-store.js)
- Bundler: Vite (via @quasar/app-vite 2.4.0)
- Cloud SDK: Supabase JS Client
- Firma Digitale: Canvas HTML5 nativo (signature pad nel ConsentFormPage)
- QR Code: API esterna qrserver (generazione Magic Link per Kiosk)

Backend:

- Framework: FastAPI (Python)
- ORM: SQLAlchemy (esclusivamente per catalogo locale e Motore Predittivo)
- DB Locale: SQLite (rafting.db)
- DB Cloud: Supabase (PostgreSQL via PostgREST)
- HTTP Client: httpx (Sync Sonda, Dual-Write, comunicazione Supabase)
- WSGI Bridge: a2wsgi (deploy Passenger su Ergonet)
- AI Vision: Azure OCR (Cognitive Services — API REST)
- PDF Generation: reportlab (certificati, manleve, consensi)

Deploy (Ergonet CloudLinux):

- Hard Limit: 1GB RAM (LVE). Vietati modelli AI locali.
- Reverse Proxy: Apache + Passenger (passenger_wsgi.py)
- Frontend: SPA statica servita da Apache
- Azure OCR: invocato via API REST cloud, zero consumo RAM locale.
  Questa scelta garantisce stabilità e rispetto del tetto di 1GB
  senza caricare modelli neurali in memoria sul server.

2. # ARCHITETTURA IBRIDA (DUAL DATABASE)

REGOLA FONDAMENTALE:
Il Catalogo vive su SQLite. I Dati Transazionali vivono SOLO su Supabase.

SQLite (Locale — Catalogo Deterministico):
┌─────────────────────┬──────────────────────────────────────────────────┐
│ Tabella │ Ruolo │
├─────────────────────┼──────────────────────────────────────────────────┤
│ activities │ Catalogo attività + workflow_schema (JSON BPMN) │
│ daily_rides │ Turni materializzati + status semaforo + override│
│ staff │ Anagrafica guide/autisti, contratti, brevetti │
│ fleet │ Mezzi: RAFT, VAN (has_tow_hitch), TRAILER │
│ system_settings │ Variabili globali EAV (raft_capacity, van_seats) │
│ activity_sub_periods│ Override stagionali (yellow_threshold, etc.) │
│ resource_exceptions │ Ferie, manutenzioni, disponibilità extra │
│ registrations │ Slot consenso Check-in (Auto-Slotting Pac-Man) │
└─────────────────────┴──────────────────────────────────────────────────┘

Supabase (Cloud — Dati Caldi Operativi e Transazionali):
┌─────────────────────┬──────────────────────────────────────────────────┐
│ Tabella │ Ruolo │
├─────────────────────┼──────────────────────────────────────────────────┤
│ rides │ Turni operativi (FK per orders, stessa UUID) │
│ orders │ Ordini clienti (pax, price_total, price_paid) │
│ transactions │ Libro Mastro pagamenti (amount, method, type) │
│ registrations │ Partecipanti individuali (consensi, FIRAFT) │
│ customers │ Anagrafica CRM cloud │
│ ride_allocations │ Assegnazione risorse (metadata JSONB) │
└─────────────────────┴──────────────────────────────────────────────────┘

Regola Dual-Write:
I Turni (rides/daily_rides) esistono in ENTRAMBI i DB con lo STESSO UUID.
Questo è il perno anti-Split-Brain: qualsiasi operazione che crea o modifica
un turno deve scrivere su entrambi i sistemi nella stessa transazione logica.
Gli Ordini e le Transazioni vivono SOLO su Supabase (via httpx PostgREST).
Il Catalogo (activities, staff, fleet) vive SOLO su SQLite.
SQLAlchemy è DEPRECATO per i flussi commerciali (cassa e POS).

3. # API ENDPOINTS (Backend FastAPI)

Router: /api/v1/calendar/
GET /activities → Lista attività attive (SQLite)
POST /activities → Crea attività
PUT /activities/{id} → Aggiorna attività
GET /daily-rides?date=YYYY-MM-DD → Turni + Engine (filtro status≠X)
POST /daily-rides/close → Kill-Switch turno vuoto (status=X)
PATCH /daily-rides/{id}/status → Semaforo manuale Dual-Write SQLite
GET /daily-rides/export-firaft → Export CSV FIRAFT
GET /daily-rides/{id} → Dettaglio singolo turno

Router: /api/v1/orders/
POST /desk → Crea ordine POS (httpx → Supabase + CRM Silente)
POST /{order_id}/transactions → Registra pagamento (Supabase)

Router: /api/v1/firaft/
POST /register-bulk → Registrazione bulk partecipanti

Router: /api/v1/logistics/
GET /staff → Lista staff attivo (SQLite)
GET /fleet → Lista mezzi attivi (SQLite)

Router: /api/v1/resources/
GET/POST/PUT /staff → CRUD staff (SQLite)
GET/POST/PUT /fleet → CRUD mezzi (SQLite)
GET /activity-rules → Regole attività (SQLite)

Router: /api/v1/vision/
POST /analyze → Analisi documento identità (Azure OCR)

Router: /api/v1/public/ (NO AUTH — Kiosk Mobile / Magic Link)
GET /orders/{order_id}/info → Info discesa per header form consenso
POST /orders/{order_id}/fill-slot → Auto-Slotting: consuma slot EMPTY (Pac-Man)

Router: /api/v1/availability/
GET /{activity_id}?date= → Calcolo disponibilità singola attività

4. # MOTORE PREDITTIVO (availability_engine.py)

Struttura a 2 Passaggi:

Pass 1 — River Ledger (Cronologico):
Per ogni turno ordinato per orario: 1. Se status='X' → skip (turno chiuso manualmente via Kill-Switch) 2. Se is_overridden=True → bypass completo, restituisci status DB
(Mappa: A→VERDE, B→GIALLO, C→ROSSO, D→BLU). Nessun calcolo. 3. Altrimenti: calcola booked_pax (da external_pax_map Supabase o ORM locale) 4. Harvesting ARR: consuma posti barche già in acqua a valle 5. Calcola barche fisiche necessarie per questo turno (needed_boats) 6. Lancia nuove barche sul fiume (genera posti vuoti in cascata ARR) 7. Costruisci timeline BPMN (Two-Pass: anchor start + end) 8. Registra in rides_data per Pass 2

Pass 2 — Semaforo Asimmetrico:
Per ogni turno in rides_data: 1. Invoca \_evaluate_ride_capacity (Time-Array Slicer 1440 minuti) 2. Calcola total_capacity = (max_boats \* raft_capacity) + arr_bonus_seats 3. Applica soglie:
remaining_seats ≤ -overbooking_limit → ROSSO
yield_warning OR remaining_seats ≤ yellow_threshold → GIALLO
else → VERDE

Funzione \_evaluate_ride_capacity (Time-Array Slicer):

- 3 array di 1440 interi: usage_rafts, usage_guides, usage_vans
- Per ogni turno concorrente: "colora" i minuti occupati con risorse richieste
- Per il turno target: trova il minuto peggiore (collo di bottiglia)
- Safety Kayak: guides_needed = max(min_guides_absolute, needed_boats)
- yield_warning = True se pool_vans insufficienti (Soft Limit / Eccezione di Sarre)
- Formula furgoni: math.ceil(booked_pax / van_net_seats) — VIETATO il margine +1

Colonne critiche daily_rides:

- status: A(verde), B(giallo), C(rosso), D(blu), X(chiuso)
- is_overridden: Boolean. Se True → Dogma Override: Engine non ricalcola.

Sync Sonda (Bypass Split-Brain):
Il router calendar.py usa httpx per estrarre i booked_pax reali da Supabase
e li inietta nel Motore Predittivo come external_pax_map (Dependency Injection).
Questo disinnsca il bug "Zero Assoluto" (ORM locale isolato dal cloud).

5. # FRONTEND ARCHITECTURE

Pagine principali:
/admin/operativo → PlanningPage.vue (Vista Giorno: griglia turni con semaforo)
/admin/timeline → TimelinePage.vue (Vista Gantt + Ruoli + Barra Saturazione)
/admin/settings → SettingsPage.vue (Costruttore Flussi BPMN a mattoncini)
/admin/resources → ResourcesPage.vue (CRUD Staff & Fleet — organo vitale)
/consenso → ConsentFormPage.vue (Kiosk Pubblico — Magic Link, mobile-first)

Componenti chiave:
RideDialog.vue → Modale Omni-Board (Tabs: Ordini Esistenti + Nuova Prenotazione)
Header con Semaforo Manuale (VERDE/BLU/GIALLO/ROSSO/AUTO)
e bottone CHIUDI TURNO (Kill-Switch, solo se booked_pax=0)
DeskBookingForm.vue → Form POS estratto (Ledger Misto, Spacca-Conto, CRM Silente)
CalendarComponent → Calendario mensile con colori semaforo dinamici

Composables:
useCheckin.js → getMagicLink, copyMagicLink, openQrModal, shareWhatsApp

6. # KIOSK PUBBLICO (Modulo Attivo e Operativo)

Il Kiosk è un modulo CHECK-IN DIGITALE già costruito e funzionante.
Interfaccia mobile-first, accessibile senza autenticazione via Magic Link.

Flusso Operativo:

1. La Segreteria crea un ordine via POS (DeskBookingForm nella modale)
2. Il sistema genera un Magic Link: {base_url}#/consenso?order_id={uuid}
3. La Segreteria lo invia al cliente via WhatsApp (useCheckin.shareWhatsApp)
   oppure mostra il QR Code (useCheckin.openQrModal)
4. Il cliente apre il link su smartphone → ConsentFormPage.vue si carica
5. Compila il form multi-step, firma sul Canvas, invia
6. Il backend consuma lo slot e genera il PDF manleva

ConsentFormPage.vue — Stepper a 6 passi (Operativo):
Step 1: Scelta lingua (Italiano / English / Deutsch / Français)
Step 2: Dati anagrafici (nome, cognome, data nascita)
Step 3: Contatti (email, telefono)
Step 4: Privacy e consenso informato (manleva, accettazione GDPR)
Step 5: Firma grafometrica su Canvas HTML5 (touch-optimized per mobile)
Step 6: Conferma completamento e messaggio di successo

Auto-Slotting Backend (Pac-Man):
POST /public/orders/{order_id}/fill-slot
Il backend cerca il primo slot con status="EMPTY" nell'ordine e lo riempie
coi dati del consenso. Opera in modalità FIFO (ordinato per ID).
Se tutti gli slot sono già compilati → HTTP 400.

AI Vision (Azure OCR):
POST /api/v1/vision/analyze
Riceve fronte (e opzionalmente retro) del documento di identità.
Azure Cognitive Services esegue l'OCR nel cloud.
Il backend estrae: nome, cognome, data nascita, codice fiscale, numero documento,
scadenza, cittadinanza. Supporta CIE, Passaporto e Patente italiana.
Nessun modello AI viene caricato in memoria locale (rispetto limite 1GB Ergonet).

PDF Manleva (reportlab):
Dopo la compilazione del consenso, il backend genera un PDF contenente:

- Dati anagrafici del partecipante
- Informazioni discesa (attività, data, ora — da OrderDB → DailyRideDB → ActivityDB)
- Firma grafometrica (immagine base64 catturata dal Canvas)
- Testo integrale della manleva e dell'informativa GDPR

7. # FIRMA GRAFOMETRICA SU CANVAS

Implementazione:

- Canvas HTML5 nel ConsentFormPage.vue (Step 5)
- Touch-optimized: eventi pointer per compatibilità mobile
- Il tracciato viene catturato come immagine PNG via canvas.toDataURL()
- L'immagine base64 viene allegata alla registrazione
- Il PDF finale (reportlab) include la firma come immagine inline

Vincoli GDPR (Compliance):

- Le firme sono dati biometrici → trattate in RAM, non persistite su disco
- Nessuna immagine di documenti (CIE/Passaporti) viene salvata in chiaro
- Solo audit.json con logica append-only per tracciabilità operativa

8. # PINIA STORE (resource-store.js)

State centralizzato:
staffList, fleetList, dailySchedule, activities, selectedDate,
timelineViewMode ('DISC' | 'ROLE'), loading, selectedResourceId

Getter vitali:
activeStaff, riverGuides, shuttleDrivers, towVans, trailers,
totalDailyPool { guides, drivers, vans, trailers }

Action fetchDailySchedule — Merge Difensivo:

1. Fetch rides da Supabase (verità fisica: ordini, allocazioni, pax reali)
2. Fetch engineRides da FastAPI /daily-rides (calcoli Motore Predittivo)
3. Merge per Firma Operativa (activity_name + ride_time normalizzato)
4. Idratazione: total_capacity dal motore, fallback a Supabase se assente
5. Override Guard: se is_overridden=True → status Engine accettato immutato
6. Kill-Switch Client (solo se !is_overridden):
   - capacità 0 + pax > 0 → forza ROSSO (overbooking innegabile)
   - capacità 0 + pax = 0 → forza GIALLO (turno senza risorse)
7. Ghost Slots: genera slot vuoti da activities.default_times per date future

8. # FLUSSI DATI CRITICI

Prenotazione POS (Dual-Write):
DeskBookingForm → POST /orders/desk
→ httpx → Supabase: INSERT orders, transactions, rides (UUID condiviso)
→ SQLAlchemy → SQLite: INSERT/UPDATE daily_rides (stesso UUID)
→ CRM Silente: UPSERT customers (Supabase)

Semaforo Manuale (Dual-Write):
RideDialog [ROSSO] → await Supabase rides.update(status='C', is_overridden=true)
→ await PATCH /daily-rides/{id}/status → SQLite (status='C', is_overridden=1)
→ Store Pinia: aggiornamento reattivo immediato
→ console.log("✅ [DUAL-WRITE] Semaforo C → Supabase OK, SQLite OK")

Kill-Switch Turno Vuoto:
PlanningPage [🗑️] → dialog conferma → POST /daily-rides/close
→ SQLite: status='X', is_overridden=1, note += "[CHIUSO MANUALMENTE]"
→ Store: dailySchedule.splice(idx, 1) — rimozione reattiva immediata
→ fetchDailySchedule() in background (sincronizzazione)

Check-in Digitale (Magic Link):
Segreteria → useCheckin.getMagicLink(order) → WhatsApp / QR Code
Cliente → ConsentFormPage (6 step) → POST /public/fill-slot
→ RegistrationDB: status EMPTY → COMPLETED, dati anagrafici + firma
→ Generazione PDF manleva (reportlab)

Refresh Pagina:
PlanningPage onMounted → fetchDailySchedule(date)
→ Supabase: rides + orders + allocations (verità fisica)
→ FastAPI: /daily-rides?date= → Sync Sonda + Engine.calculate_availability()
→ Merge Difensivo con Override Guard → UI aggiornata
