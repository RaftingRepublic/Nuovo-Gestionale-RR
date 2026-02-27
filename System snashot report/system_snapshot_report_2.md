# SYSTEM SNAPSHOT REPORT — RAFTING REPUBLIC GESTIONALE
**Data Generazione:** 27 Febbraio 2026, ore 21:14 CET
**Destinatario:** Tech Lead Entrante (Onboarding)
**Fase Corrente:** 7.E — Collaudo End-to-End Tetris Umano (Crew Builder)

---

## 1. QUADRO D'INSIEME ESECUTIVO

Rafting Republic Gestionale è un **ERP operativo verticale** per un'azienda di rafting, costruito con architettura ibrida Dual-Database (SQLite locale + Supabase Cloud PostgreSQL). Il sistema gestisce:

- **Prenotazioni e POS** (cassa digitale multi-pagamento)
- **Calendario Operativo** con semaforo di disponibilità predittivo
- **Crew Builder** (composizione equipaggi: guide + gommoni + passeggeri nominali)
- **Check-in Digitale** (Kiosk mobile con firma grafometrica e manleva PDF)
- **Timeline Flussi** (Gantt con Multi-Lane Packing e barra di saturazione)
- **OCR Documentale** (Azure Cognitive Services per CIE/Passaporti)

Il progetto ha attraversato **7 fasi evolutive** in rapida successione, con una massiccia ristrutturazione architetturale nella Fase 6 (risoluzione Split-Brain, motore predittivo, POS ibrido) e implementazione Crew Builder nella Fase 7.

---

## 2. STACK TECNOLOGICO

| Layer | Tecnologia | Note |
|-------|-----------|------|
| Frontend Framework | Vue 3 (Composition API, script setup) | SPA |
| UI Kit | Quasar Framework v2.18.6 | Componenti Material Design |
| State Management | Pinia | 6 store: resource, crew, auth, registration, settings, index |
| Bundler | Vite (via @quasar/app-vite 2.4.0) | Dev + Build |
| Cloud SDK | Supabase JS Client | Comunicazione diretta Supabase dal frontend |
| Backend Framework | FastAPI (Python) | API REST |
| ORM | SQLAlchemy | SOLO per catalogo locale, DEPRECATO per flussi commerciali |
| DB Locale | SQLite (rafting.db) | Catalogo, staff, fleet, settings, engine |
| DB Cloud | Supabase (PostgreSQL via PostgREST) | Ordini, transazioni, rides, allocazioni |
| HTTP Client Backend | httpx | Sync Sonda, Dual-Write, comunicazione Supabase |
| AI Vision | Azure OCR (Cognitive Services API REST) | Zero RAM locale |
| PDF | reportlab | Certificati, manleve, consensi |
| Deploy | CloudLinux (Ergonet) + Apache + Passenger | Hard Limit 1GB RAM (LVE) |
| WSGI Bridge | a2wsgi (passenger_wsgi.py) | NO uvicorn diretto in produzione |

---

## 3. ARCHITETTURA IBRIDA (DUAL DATABASE) — IL CUORE DEL SISTEMA

> [!IMPORTANT]
> Il sistema opera con **due database simultanei**. Questa è la scelta architetturale più critica da comprendere per il Tech Lead entrante.

### 3.1 SQLite (Locale — Catalogo Deterministico)

| Tabella | Ruolo | Righe tipo |
|---------|-------|------------|
| activities | Catalogo attività + workflow_schema (JSON BPMN con flussi a mattoncini) | FAMILY, CLASSICA, ecc. |
| daily_rides | Turni materializzati + status semaforo + is_overridden | Creati via Dual-Write |
| staff | Anagrafica guide/autisti, contratti, brevetti, ruoli multi-role (JSON) | UUID locali |
| fleet | Mezzi: RAFT, VAN (has_tow_hitch), TRAILER (max_rafts) | UUID locali |
| system_settings | Variabili globali EAV (raft_capacity, van_seats, ecc.) | Key-Value |
| activity_sub_periods | Override stagionali (prezzo, orari, soglia giallo, overbooking) | Per date specifiche |
| resource_exceptions | Ferie, manutenzioni, disponibilità extra staff | Diario unificato |
| registrations | Slot consenso Check-in (Auto-Slotting Pac-Man) | Per ordine |
| customers | Anagrafica CRM (locale legacy) | Ridondato in Supabase |
| orders | Ordini (locale legacy) | DEPRECATO per POS, usato solo da Engine |
| transactions | Transazioni (locale legacy) | DEPRECATO per POS |
| crew_assignments | Assegnazione equipaggi (locale) | TABELLA MORTA — 0 righe, mai usata |
| ride_staff_link | M2M ride-staff | TABELLA MORTA — 0 righe |
| ride_fleet_link | M2M ride-fleet | TABELLA MORTA — 0 righe |

### 3.2 Supabase (Cloud — Dati Caldi Operativi)

| Tabella | Ruolo | FK |
|---------|-------|-----|
| rides | Turni operativi (stessa UUID di daily_rides locale) | Perno Dual-Write |
| orders | Ordini clienti (pax, price_total, price_paid, extras, source) | FK → rides |
| transactions | Libro Mastro pagamenti (amount, method, type, note) | FK → orders (CASCADE) |
| registrations | Partecipanti individuali (consensi, FIRAFT) | FK → orders |
| customers | Anagrafica CRM cloud | FK → orders |
| ride_allocations | Assegnazione risorse con metadata JSONB (Crew Builder) | FK logica → rides. NO FK fisica verso staff/fleet |

### 3.3 Regola Dual-Write (Anti-Split-Brain)

Il turno (ride) è l'unica entità che vive in **entrambi** i database con lo **stesso UUID**. Qualsiasi operazione che crea un turno deve scrivere su SQLite (daily_rides) e su Supabase (rides) nella stessa transazione logica. Questo è il perno che tiene insieme i due mondi.

- **Ordini e Transazioni** → SOLO Supabase (via httpx PostgREST)
- **Catalogo (activities, staff, fleet)** → SOLO SQLite
- **SQLAlchemy** → DEPRECATO per la cassa. Rimane per Engine e catalogo.

### 3.4 Regola Anti-FK Cross-Database (Dogma 12)

Le chiavi esterne in Supabase che puntano a entità del catalogo locale (es. `resource_id` in `ride_allocations` verso `staff`/`fleet`) **NON devono avere vincoli fisici** (FOREIGN KEY constraints). Devono essere UUID liberi (Chiavi Logiche), validati solo applicativamente. Altrimenti il cloud va in conflitto con SQLite generando `409 Conflict` (`23503 foreign_key_violation`).

---

## 4. MAPPA BACKEND — ROUTERS E SERVIZI

### 4.1 Router FastAPI registrati in main.py

| # | Prefisso URL | File | Tag | Stato |
|---|-------------|------|-----|-------|
| 1 | /api/v1/vision | vision.py (1.7KB) | AI Vision | Operativo (Azure OCR) |
| 2 | /api/v1/registration | registration.py (10.8KB) | Registration | Operativo |
| 3 | /api/v1/resources | resources.py (2.6KB) | Resources | Operativo (CRUD Staff/Fleet) |
| 4 | /api/v1/reservations | reservations.py (1.3KB) | Reservations | Operativo |
| 5 | /api/v1/calendar | calendar.py (33.1KB) | Calendar | Operativo (BFF principale, Sync Sonda) |
| 6 | /api/v1/legacy-orders | orders.py (11.9KB) | Orders (Legacy) | DEPRECATO — backward-compat |
| 7 | /api/v1/firaft | firaft.py (4.6KB) | FiRaft | Operativo (Tesseramento) |
| 8 | /api/v1/logistics | logistics.py (9KB) | Logistics | Operativo |
| 9 | /api/v1/orders | desk.py (17KB) | Desk POS | Operativo (POS via httpx Supabase) |
| 10 | /api/v1/public | public.py (5.2KB) | Public Check-in | Operativo (NO AUTH, Kiosk) |
| 11 | /api/v1/availability | availability.py (1.2KB) | Availability Engine | Operativo |
| 12 | /api/v1/crew | crew.py (7.8KB) | Crew Builder | Operativo (Fase 7) |

### 4.2 Servizi Backend

| Servizio | File | Dimensione | Ruolo |
|----------|------|-----------|-------|
| Availability Engine | availability_engine.py | 22KB (483 linee) | Motore predittivo semaforo 2-Pass |
| Yield Engine | yield_engine.py | 22KB | Motore matematico disponibilità |
| Azure Document OCR | azure_document_service.py | 15.5KB | OCR cloud CIE/Passaporto |
| Local Vision (Legacy) | local_vision_service.py | 36KB | OCR locale (Paddle+YOLO+GLiNER) — NON USATO in prod |
| Waiver Service | waiver_service.py | 14KB | Generazione PDF manleve (reportlab) |
| Image Utils | image_utils.py | 12.6KB | Preprocessing immagini |
| Document Specs | document_specs.py | 4KB | Specifiche documenti identità |
| Waiver Mailer | waiver_mailer.py | 1.8KB | Invio email manleve |

### 4.3 Modelli SQLAlchemy (calendar.py — 271 linee)

- **ActivityDB** — Catalogo attività con workflow_schema JSON (BPMN)
- **ActivitySubPeriodDB** — Override stagionali per date specifiche
- **DailyRideDB** — Turni con status (A/B/C/D/X) e is_overridden
- **CustomerDB** — Anagrafica CRM
- **OrderDB** — Ordini con Ledger, extras, source, customer_id
- **TransactionDB** — Libro Mastro (amount, method, type)
- **StaffDB** — Staff con contratti JSON, ruoli multi-role, flag guide/driver
- **FleetDB** — Mezzi con capacity, has_tow_hitch, max_rafts
- **CrewAssignmentDB** — ☠️ MORTO (0 righe, mai usato — sostituito da Supabase JSONB)
- ride_staff_link / ride_fleet_link — ☠️ MORTI (tabelle M2M mai populate)

### 4.4 Schemi Pydantic (backend/app/schemas/)

| File | Contenuto |
|------|-----------|
| calendar.py (5.2KB) | Schema turni, attività, sub-periodi |
| desk.py (3KB) | Schema POS (DeskBookingRequest, LineItem, ecc.) |
| logistics.py (4KB) | Schema logistica (workflow, risorse) |
| orders.py (4.4KB) | Schema ordini legacy |
| registration.py (6.3KB) | Schema registrazioni/consensi |
| resources.py (5.6KB) | Schema CRUD staff/fleet |
| availability.py (0.5KB) | Schema response Engine |
| public.py (0.6KB) | Schema API pubblica |

---

## 5. MAPPA FRONTEND — PAGINE, COMPONENTI, STORE

### 5.1 Pagine (web-app/src/pages/)

| Path | File | Dim. | Ruolo | Stato |
|------|------|------|-------|-------|
| /admin/operativo | PlanningPage.vue | 35KB | Calendario Operativo — HUB SUPREMO | Operativo |
| /admin/timeline | TimelinePage.vue | 25KB | Gantt + Multi-Lane Packing + Barra Saturazione | Operativo |
| /admin/impostazioni | SettingsPage.vue | 38KB | Costruttore Flussi BPMN a mattoncini | Operativo |
| /admin/risorse | ResourcesPage.vue | 30KB | CRUD Staff e Fleet — ORGANO VITALE | Operativo |
| /admin/board | DailyBoardPage.vue | 10.6KB | Lavagna Operativa giornaliera | Operativo |
| /admin/registrazioni | RegistrationsPage.vue | 13.7KB | Archivio Consensi/Registrazioni | Operativo |
| /consenso | ConsentFormPage.vue | (in public/) | Kiosk Check-in Digitale — NO AUTH | Operativo |
| /admin/scanner/:id? | ScannerPage.vue | 28KB | Scanner documenti (OCR) | Operativo |
| /login | LoginPage.vue | 6.6KB | Autenticazione | Operativo |
| /admin/segreteria | PlanningPage.vue | redirect | Alias → operativo (backward compat) | |

### 5.2 Componenti (web-app/src/components/)

| File | Dim. | Ruolo |
|------|------|-------|
| RideDialog.vue | 48KB | Modale Omni-Board (3 Tab: Ordini + POS + Equipaggi) |
| CrewBuilderPanel.vue | 17.7KB | Tab Equipaggi del Crew Builder (Tetris Umano) |
| DeskBookingForm.vue | 10.6KB | Form POS estratto (Ledger Misto, Spacca-Conto) |
| CalendarComponent.vue | 17.9KB | Calendario mensile con colori semaforo |
| ResourcePanel.vue | 19.9KB | Pannello dettaglio risorse |
| SeasonConfigDialog.vue | 21KB | Dialog configurazione stagioni |
| CameraCapture.vue | 11.6KB | Cattura foto per OCR |
| FiraftDialog.vue | 5.9KB | Dialog tesseramento FIRAFT |
| QrDialog.vue | 0.9KB | QR Code per Magic Link |
| ModuleCard.vue | 1.4KB | Card generica modulo |
| scanner/* | 4 file | Componenti scanner documenti |

### 5.3 Store Pinia (web-app/src/stores/)

| File | Dim. | Ruolo |
|------|------|-------|
| resource-store.js | 35.5KB | Store principale: staff, fleet, dailySchedule, fetchDailySchedule (Merge Difensivo), Ghost Slots |
| crew-store.js | 4.3KB | Crew Builder: allocations, loadCrew, saveCrew, getter boatCount/assignedPax/unassignedPax |
| registration-store.js | 9.7KB | Registrazioni e consensi |
| settings-store.js | 3.4KB | Impostazioni sistema |
| auth-store.js | 1.6KB | Autenticazione |
| index.js | 0.5KB | Bootstrap Pinia |

### 5.4 Composables e Services

| File | Ruolo |
|------|-------|
| useCheckin.js | getMagicLink, copyMagicLink, openQrModal, shareWhatsApp |
| FiraftService.js | Servizio tesseramento |
| VisionService.js | Servizio OCR |
| ImageQualityService.js | Controllo qualità immagine |

---

## 6. MOTORE PREDITTIVO — AVAILABILITY ENGINE

Il cuore matematico del sistema. Calcola dinamicamente la disponibilità di ogni turno.

### 6.1 Architettura a 2 Passaggi

**Pass 1 — River Ledger (Cronologico):**

Per ogni turno ordinato per orario:
1. Se `status='X'` → skip (turno chiuso via Kill-Switch)
2. Se `is_overridden=True` → bypass completo, restituisci status DB (A→VERDE, B→GIALLO, C→ROSSO, D→BLU)
3. Calcola [booked_pax](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/availability_engine.py#457-465) (da `external_pax_map` Supabase o ORM locale)
4. Harvesting ARR: consuma posti barche già in acqua a valle
5. Calcola barche fisiche necessarie (`needed_boats`)
6. Lancia nuove barche (genera posti vuoti in cascata ARR)
7. Costruisci timeline BPMN (Two-Pass: anchor start + end)
8. Registra in `rides_data` per Pass 2

**Pass 2 — Semaforo Asimmetrico:**

Per ogni turno in rides_data:
1. Invoca [_evaluate_ride_capacity](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/availability_engine.py#136-200) (Time-Array Slicer 1440 minuti)
2. Calcola `total_capacity = (max_boats * raft_capacity) + arr_bonus_seats`
3. Applica soglie: ROSSO / GIALLO / VERDE

### 6.2 Time-Array Slicer (_evaluate_ride_capacity)

3 array di 1440 interi: `usage_rafts`, `usage_guides`, `usage_vans`. Per ogni turno concorrente, "colora" i minuti occupati con risorse richieste. Per il turno target, trova il minuto peggiore (collo di bottiglia).

- **Safety Kayak:** `guides_needed = max(min_guides_absolute, needed_boats)`
- **yield_warning** = True se `pool_vans` insufficienti (Soft Limit / Eccezione di Sarre)
- **Formula furgoni:** `math.ceil(booked_pax / van_net_seats)` — VIETATO il margine +1

### 6.3 Sync Sonda (Bypass Split-Brain)

[calendar.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py) usa httpx per estrarre i [booked_pax](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/availability_engine.py#457-465) reali da Supabase e li inietta nel Motore Predittivo come `external_pax_map` (Dependency Injection). Questo disinnesca il bug "Zero Assoluto" (ORM locale isolato dal cloud).

---

## 7. FLUSSI DATI CRITICI

### 7.1 Prenotazione POS (Dual-Write)

DeskBookingForm → `POST /orders/desk` → httpx → Supabase: INSERT orders, transactions, rides (UUID condiviso) → SQLAlchemy → SQLite: INSERT/UPDATE daily_rides (stesso UUID) → CRM Silente: UPSERT customers (Supabase)

### 7.2 Semaforo Manuale (Dual-Write)

RideDialog [ROSSO] → await Supabase rides.update(status='C', is_overridden=true) → await `PATCH /daily-rides/{id}/status` → SQLite (status='C', is_overridden=1) → Store Pinia: aggiornamento reattivo immediato

### 7.3 Kill-Switch Turno Vuoto

PlanningPage [Cestino] → dialog conferma → `POST /daily-rides/close` → SQLite: status='X', is_overridden=1 → Store: splice reattivo → fetchDailySchedule() background

### 7.4 Check-in Digitale (Magic Link)

Segreteria → useCheckin.getMagicLink(order) → WhatsApp / QR Code → Cliente apre ConsentFormPage (6 step) → `POST /public/fill-slot` → Auto-Slotting FIFO → Generazione PDF manleva (reportlab)

### 7.5 Crew Builder (Tetris Umano)

CrewBuilderPanel → crew-store `saveCrew(ride_id)` → `PUT /api/v1/crew/allocations` → Backend: DELETE vecchi record per ride_id + bulk INSERT nuovi → Supabase ride_allocations con metadata JSONB (groups: [{ order_id, customer_name, pax }])

### 7.6 Refresh Pagina (Merge Difensivo)

PlanningPage onMounted → fetchDailySchedule(date) → Supabase (rides + orders + allocations) + FastAPI /daily-rides (Engine) → Merge per Firma Operativa → Kill-Switch Client se !is_overridden → Ghost Slots da default_times

---

## 8. DEPLOY — INFRASTRUTTURA ERGONET

| Aspetto | Dettaglio |
|---------|-----------|
| Hosting | Ergonet (CloudLinux LVE) |
| Hard Limit RAM | **1GB** — CRITICO |
| Frontend | SPA statica in httpdocs/ (Quasar build) |
| Backend | /var/www/vhosts/raftingrepublic.com/backend/ |
| Processo | Gunicorn + UvicornWorker (2 workers, bind 127.0.0.1:8000) |
| Reverse Proxy | Nginx (direttive aggiuntive in Plesk) /api/ → :8000 |
| SSL | Let's Encrypt (automatico via Plesk) |
| AI in Produzione | DISABILITATA (requirements_production.txt esclude torch/paddle/yolo) |
| AI Attiva | Azure OCR (API REST cloud, zero overhead locale) |
| Dominio | gestionale.raftingrepublic.com |
| Admin venv | Python 3.9+ con venv |
| Bridge Legacy | api_bridge.php (4.5KB) — ponte per vecchie integrazioni |

**File da NON caricare in deploy:** venv/, __pycache__/, storage/debug_captures/, test/, tools/

---

## 9. STATO ATTUALE — FASE 7.E (CANTIERE ATTIVO)

### 9.1 Cosa è stato completato (Fasi 7.A → 7.D)

- **7.A** — Scaffold: Router crew.py, CrewBuilderPanel.vue, tab "Equipaggi" in RideDialog
- **7.B** — DDL Supabase ride_allocations (metadata JSONB, indici, RLS), Store Pinia crew-store.js
- **7.C** — UI Banchina d'Imbarco con righe dinamiche [Gommone] + [Guida] + [Pax]
- **7.C.2** — Tetris Umano: metadata gommoni con `groups: [{ order_id, customer_name, pax }]`
- **7.D** — Allineamento Backend: Schemi Pydantic, PUT accetta `List[CrewAllocationItem]`, Swap and Replace
- **7.D.fix** — Autopsia Tripla: JWT Auth fix, Pydantic mismatch fix, FK amputata, Ghost Limb curata

### 9.2 Obiettivi Fase 7.E (PROSSIMA SESSIONE)

- [ ] Warning UI se `SUM(groups.pax) != totale pax paganti` (mismatch imbarcati vs prenotati)
- [ ] Highlight barche piene / overflow sulla capienza del gommone fisico
- [ ] Collaudo end-to-end Tetris Umano: salva → ricarica → verifica persistenza Supabase
- [ ] Pulizia record orfani eventualmente creati durante il debugging Fase 7.D

---

## 10. BUG PENDENTI E DEBITO TECNICO

### 10.1 Debito Tecnico Residuale (Fase 6.K)

| ID | Descrizione | Severità | Impatto |
|----|-------------|----------|---------|
| DT-01 | Pulizia commenti JSDoc obsoleti nel codebase | Bassa | Manutenibilità |
| DT-02 | Consolidamento file requirements multipli (5 file: requirements.txt, _fixed, _frozen, _lock, _production) | Media | Confusione deploy, rischio installazione errata |

### 10.2 Potenziali Bug / Rischi Aperti (da Collaudo 7.E)

| ID | Descrizione | Severità | Stato |
|----|-------------|----------|-------|
| BUG-7E-01 | Persistenza Crew Builder non collaudata end-to-end (salva → chiudi → riapri → verifica dati) | Alta | Da verificare |
| BUG-7E-02 | Record orfani in ride_allocations creati durante debugging Fase 7.D | Media | Da pulire |
| BUG-7E-03 | Mancanza warning UI per mismatch pax imbarcati vs pax prenotati | Media | Da implementare |
| BUG-7E-04 | Nessun highlight visivo per barche piene/overflow | Media | Da implementare |

### 10.3 Tabelle Morte in SQLite (Fossili Geologici)

| Tabella | Stato | Note |
|---------|-------|------|
| crew_assignments | ☠️ MORTA (0 righe) | Sostituita da Supabase ride_allocations JSONB |
| ride_staff_link | ☠️ MORTA (0 righe) | M2M mai populata — fossile Fase 6.B |
| ride_fleet_link | ☠️ MORTA (0 righe) | M2M mai populata — fossile Fase 6.B |

> [!WARNING]
> Le tabelle morte occupano spazio nel modello SQLAlchemy e sono importate in main.py ([CrewAssignmentDB](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#223-235)). Non causano errori funzionali ma generano confusione per un nuovo sviluppatore.

### 10.4 Router Legacy

Il router [orders.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/orders.py) è montato su `/api/v1/legacy-orders` ed è marcato come DEPRECATO. Il POS ora usa [desk.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/desk.py) montato su `/api/v1/orders`. Il router legacy resta per backward-compatibility ma non dovrebbe ricevere traffico attivo.

### 10.5 File di Servizio Legacy nel Backend

| File | Note |
|------|------|
| local_vision_service.py (36KB) | OCR locale con Paddle+YOLO+GLiNER — NON USATO in produzione. Azure OCR lo ha sostituito. |
| 5 file requirements_* | Confusione: requirements.txt (dev), _fixed, _frozen, _lock, _production |

---

## 11. DOGMI ARCHITETTURALI (LORE VAULT — Regole Sacre)

Qui sotto le regole tassative che il Tech Lead DEVE conoscere prima di toccare il codice:

| # | Nome | Regola |
|---|------|--------|
| — | Hard Limit LVE | Server ha 1GB RAM. Zero modelli AI locali. Lazy Loading obbligatorio. gc.collect() dopo inferenza. |
| — | DDL Supabase | Ogni ALTER TABLE deve concludersi con `NOTIFY pgrst, 'reload schema'` per svuotare cache API. Pena: errore PGRST204. |
| — | Override Semaforo | Se `is_overridden=True` → Engine NON ricalcola. Bypass su Pass 1. Unica via per tornare ad AUTO: `is_overridden=False`. |
| 10 | Tetris Umano | Passeggeri mai anonimi. metadata JSONB deve contenere `groups: [{ order_id, customer_name, pax }]`. Si imbarcano frazioni di ordini. |
| 11 | Swap and Replace | Aggiornamento massivo equipaggi: DELETE per ride_id + bulk INSERT. Zero orfani, zero diff. |
| 12 | Chiavi Logiche Cross-DB | FK in Supabase verso entità SQLite = UUID liberi. NO vincoli fisici FK. Pena: `409 Conflict`. |
| 12c | Sindrome Arto Fantasma | Se FK amputata in cloud → epurare JOIN PostgREST frontend (`select(..., entita(*))`) → Pena: `PGRST200 Bad Request`. |
| — | Split-Brain Controllato | Catalogo in SQLite, Dati caldi in Supabase. Turni in Dual-Write (stesso UUID). Ordini SOLO cloud. |
| — | Formula Furgoni | `math.ceil(booked_pax / van_net_seats)`. VIETATO +1. Bug "Passeggero Fantasma" scoperto 27/02. |
| — | GDPR | Nessuna immagine documento salvata su disco. Solo RAM. audit.json append-only con hash chaining. |

---

## 12. STRUTTURA DATABASE DETTAGLIATA

### 12.1 SQLite — Schema Completo (rafting.db)

**activities**
- id: String(36) PK UUID
- code: String(20) UNIQUE (FAMILY, CLASSICA)
- name: String(100) NOT NULL
- price: Float
- duration_hours: Float (default 2.0)
- color_hex: String(7)
- river_segments: String(100) nullable
- manager: String(50) (Grape/Anatre — toggle FiRaft)
- season_start: Date nullable
- season_end: Date nullable
- default_times: JSON array (["09:00","14:00"])
- allow_intersections: Boolean (ARR cascata)
- activity_class: String(20) (RAFTING/HYDRO/KAYAK)
- yellow_threshold: Integer (soglia semaforo giallo)
- overbooking_limit: Integer
- workflow_schema: JSON (schema BPMN {"flows":[...],"logistics":{...}})
- is_active: Boolean

**daily_rides**
- id: String(36) PK UUID (DEVE coincidere con Supabase rides.id)
- activity_id: String(36) FK → activities.id
- ride_date: Date NOT NULL INDEX
- ride_time: Time NOT NULL INDEX
- status: String(1) — A(Verde), B(Giallo), C(Rosso), D(Blu), X(Chiuso)
- is_overridden: Boolean (Dogma Override)
- notes: Text nullable

**staff**
- id: String(36) PK UUID
- name: String(100) NOT NULL
- contract_type: String(20) (FISSO/EXTRA)
- is_guide: Boolean
- is_driver: Boolean (patente navetta)
- roles: JSON array (["RAF4","SK","NC"])
- contract_periods: JSON array ([{"start":"2026-05-01","end":"2026-09-30"}])
- is_active: Boolean

**fleet**
- id: String(36) PK UUID
- name: String(100) NOT NULL
- category: String(20) (RAFT/VAN/TRAILER)
- total_quantity: Integer
- capacity_per_unit: Integer (legacy)
- is_active: Boolean
- capacity: Integer (posti passeggeri per gommoni, sedili per furgoni)
- has_tow_hitch: Boolean (solo VAN)
- max_rafts: Integer (solo TRAILER)

**system_settings** (EAV Key-Value)
- key: String(50) PK (es. raft_capacity, van_seats)
- value: String(255)
- category: String(50) (raggruppamento UI)
- description: String(255) (label UI)

**activity_sub_periods**
- id: String(36) PK UUID
- activity_id: String(36) FK → activities.id CASCADE
- name: String(100)
- dates: JSON array (["2026-08-01","2026-08-02"])
- override_price: Float nullable
- override_times: JSON array
- is_closed: Boolean
- allow_intersections: Boolean nullable
- yellow_threshold: Integer nullable
- overbooking_limit: Integer nullable

**resource_exceptions**
- id: String(36) PK UUID
- resource_id: String(36) INDEX
- resource_type: String(20) (STAFF/FLEET)
- name: String(100) (Ferie, Guasto)
- is_available: Boolean (False=assenza per FISSI, True=presenza per EXTRA)
- dates: JSON array

**orders** (locale — DEPRECATO per POS, usato da Engine)
- id: String(36) PK UUID
- ride_id: String(36) FK → daily_rides.id
- order_status: String(20)
- total_pax: Integer
- price_total, price_paid: Float
- payment_type: String(50)
- is_exclusive_raft: Boolean
- discount_applied: Float
- customer_name, customer_email, customer_phone: String
- notes: Text
- booker_name, booker_phone, booker_email: String
- adjustments: Float
- extras: JSON array
- source: String(20) (WEB/DESK/PARTNER)
- customer_id: String(36) FK → customers.id

**transactions** (locale — DEPRECATO)
- id PK, order_id FK → orders CASCADE, amount, method, type, note, timestamp

**customers** (locale)
- id PK, full_name, email, phone, created_at

### 12.2 Supabase — Schema Cloud

**rides**
- id: UUID PK (DEVE coincidere con daily_rides.id in SQLite)
- activity_id: UUID
- date: Date
- time: Time
- status: String (A/B/C/D/X)
- is_overridden: Boolean
- created_at: Timestamp

**orders**
- id: UUID PK
- ride_id: UUID FK → rides ON DELETE CASCADE
- pax: Integer
- customer_name: String
- customer_email: String nullable
- customer_phone: String nullable
- price_total: Numeric
- price_paid: Numeric
- source: String (WEB/DESK/PARTNER)
- extras: JSONB
- notes: Text nullable
- status: String
- created_at: Timestamp

**transactions**
- id: UUID PK
- order_id: UUID FK → orders ON DELETE CASCADE
- amount: Numeric
- method: String (CASH/SUMUP/BONIFICO/PARTNERS)
- type: String (CAPARRA/SALDO)
- note: String nullable
- timestamp: Timestamp

**registrations** (Supabase)
- Partecipanti individuali con dati anagrafici, firma, consensi
- FK → orders

**customers** (Supabase)
- Anagrafica CRM cloud (UPSERT via CRM Silente)

**ride_allocations**
- id: UUID PK
- ride_id: UUID FK → rides
- resource_id: UUID (**CHIAVE LOGICA**, nessuna FK fisica verso staff/fleet)
- resource_type: String (crew_manifest)
- metadata: JSONB ({groups: [{order_id, customer_name, pax}]})
- created_at: Timestamp
- Indici su ride_id e resource_type
- RLS policy attiva

---

## 13. SICUREZZA E COMPLIANCE GDPR

| Aspetto | Implementazione |
|---------|----------------|
| Storage Documenti | NESSUNO. Immagini processate in RAM con `ID_IMAGE_RETENTION=NONE` |
| Firma Grafometrica | Canvas HTML5, vettori biometrici catturati, inclusi nel PDF |
| Audit Log | audit.json con hash chaining (blockchain-style, tamper-evident) |
| CORS | `allow_origins=["*"]` in dev (da restringere in prod) |
| Auth | Supabase Auth (JWT). Il backend verifica via chiavi SUPABASE_URL/KEY dal .env |
| Public API | /api/v1/public/* — NO AUTH (Kiosk client). Accesso limitato a fill-slot e info ordine |

> [!CAUTION]
> CORS è attualmente impostato su allow_origins=["*"]. In produzione dovrebbe essere ristretto al dominio gestionale.raftingrepublic.com.

---

## 14. ROUTING FRONTEND

| Route | Pagina | Note |
|-------|--------|------|
| / | redirect → /consenso | Landing Kiosk |
| /consenso | ConsentFormPage.vue (PublicLayout) | NO AUTH |
| /login | LoginPage.vue (standalone, no layout) | |
| /admin | MainLayout.vue (requiresAuth) | Sidebar + Header |
| /admin/operativo | PlanningPage.vue | HUB PRINCIPALE |
| /admin/segreteria | PlanningPage.vue | Alias backward-compat |
| /admin/timeline | TimelinePage.vue | Gantt |
| /admin/impostazioni | SettingsPage.vue | BPMN builder |
| /admin/risorse | ResourcesPage.vue | CRUD Staff/Fleet |
| /admin/board | DailyBoardPage.vue | Lavagna giornaliera |
| /admin/registrazioni | RegistrationsPage.vue | Archivio consensi |
| /admin/scanner/:id? | ScannerPage.vue | OCR |
| /admin/pianificazione | redirect → /admin/operativo | Legacy |

---

## 15. FILE ROOT DI GOVERNO

| File | Dim. | Ruolo |
|------|------|-------|
| PROJECT_RADAR.md | 8.7KB | Stato avanzamento, task pendenti, storico traguardi |
| LORE_VAULT.md | 16.7KB | Dogmi architetturali, regole sacre, vincoli di business |
| TECH_ARCHITECTURE.md | 14.1KB | Documentazione tecnica stack, API, engine, flussi dati |
| README.md | 4.8KB | Setup sviluppo locale (installazione backend/frontend) |
| DEPLOY.md | 6.2KB | Guida deploy su Ergonet Plesk |
| PHASE_7_BLUEPRINT.md | 7.4KB | Blueprint dettagliato Crew Builder |
| GIT_GUIDE.md | 2.2KB | Guida comandi Git |
| PHASE_6_D_DYNAMIC_YIELD.md | 1.7KB | Spec Fase 6.D |
| PHASE_6_E_MATH_ENGINE.md | 1.6KB | Spec Fase 6.E |

---

## 16. RIEPILOGO METRICHE CODEBASE

| Metrica | Valore |
|---------|--------|
| Pagine Vue | 11 (7 in /pages root + 4 in /pages/admin) |
| Componenti Vue | 14 (10 root + 4 scanner) |
| Store Pinia | 6 |
| Composables | 1 (useCheckin.js) |
| Services Frontend | 3 + 1 subdirectory |
| Router Backend | 12 |
| Modelli SQLAlchemy | 10 classi (3 MORTE) |
| Schemi Pydantic | 8 file |
| Servizi Backend | 9 |
| Dimensione file più grande FE | RideDialog.vue (48KB) |
| Dimensione file più grande BE | local_vision_service.py (36KB) — NON USATO |
| Dimensione DB SQLite | 294KB (rafting.db) |
| Dimensione resource-store.js | 35.5KB (store più pesante) |

---

## 17. BACKLOG STRATEGICO

| Priorità | Idea | Stato |
|----------|------|-------|
| PROSSIMA | **Fase 7.E** — Validazioni Crew Builder, collaudo e2e, pulizia orfani | Attivo |
| Backlog | Modulo Presenze Giornaliere Staff | Stand-by |
| Backlog | Flusso Prenotazioni CRM (Anagrafiche, Pagamenti completo) | Stand-by |
| Completato | ~~Timeline View~~ | Fase 6.J |
| Completato | ~~Amputazione ruderi geologici~~ | Fase 6.K |

---

## 18. NOTE OPERATIVE PER IL TECH LEAD

1. **Il file più critico da studiare per primo** è [resource-store.js](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/stores/resource-store.js) (35.5KB). Contiene l'intera logica di Merge Difensivo, Ghost Slots, Kill-Switch client, e la coreografia tra Supabase e FastAPI.

2. **RideDialog.vue** (48KB) è il secondo file da studiare. È la modale Omni-Board che fonde 3 tab: Ordini Esistenti, Nuova Prenotazione (POS), e Equipaggi (Crew Builder).

3. **calendar.py** backend (33KB) è la BFF principale. Contiene la Sync Sonda e orchestrate tutte le chiamate complesse.

4. **availability_engine.py** (22KB, 483 linee) è il cervello matematico. Non toccare senza capire il Two-Pass e il Time-Array Slicer.

5. **I turni si identificano per "Firma Operativa"** = `activity_name + ride_time normalizzato`. Questo è il meccanismo di merge tra i dati Supabase e i dati Engine.

6. **Per avviare il sistema in locale**: seguire il workflow `/start-dev` (backend su porta 8000, frontend con `npx quasar dev`).

7. **Le variabili Supabase** (`SUPABASE_URL`, `SUPABASE_KEY`) devono essere nel file [backend/.env](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/.env) e nel frontend ([web-app/.env](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/.env) o [supabase.js](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/supabase.js)).

---

*Report generato automaticamente dall'analisi statica del codebase. Snapshot al 27/02/2026 21:14 CET.*
