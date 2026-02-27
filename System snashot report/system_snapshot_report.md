# SYSTEM SNAPSHOT REPORT — RAFTING REPUBLIC GESTIONALE

**Data generazione:** 27/02/2026 21:52 CET
**Fase corrente:** Fase 8 (Smaltimento Debito Tecnico)
**Ultima build verificata:** 27/02/2026 21:46
**Autore:** Antigravity System Agent

---

## INDICE

1. [Identità del Prodotto](#1-identità-del-prodotto)
2. [Stack Tecnologico Completo](#2-stack-tecnologico-completo)
3. [Architettura Ibrida — Dual Database](#3-architettura-ibrida--dual-database)
4. [Mappa Completa del Database](#4-mappa-completa-del-database)
5. [Backend — Routers, Modelli e Servizi](#5-backend--routers-modelli-e-servizi)
6. [Frontend — Pagine, Componenti e Stores](#6-frontend--pagine-componenti-e-stores)
7. [Flussi Dati Critici](#7-flussi-dati-critici)
8. [Dogmi Architetturali Vigenti](#8-dogmi-architetturali-vigenti)
9. [Bug Pendenti e Debito Tecnico](#9-bug-pendenti-e-debito-tecnico)
10. [Storico Fasi Completate](#10-storico-fasi-completate)
11. [Rischi e Avvertimenti per il Tech Lead](#11-rischi-e-avvertimenti-per-il-tech-lead)

---

## 1. IDENTITÀ DEL PRODOTTO

| Proprietà | Valore |
|---|---|
| **Nome** | Rafting Republic — Gestionale AI |
| **Versione** | 2.0 (Migration & Compliance Edition) |
| **Dominio** | gestionale.raftingrepublic.com |
| **Purpose** | Gestionale operativo per azienda di rafting: prenotazioni, logistica turni, assegnazione equipaggi, check-in digitale, semaforo disponibilità, CRM silente |
| **Utenti target** | Segreteria (desk POS), Logistica (crew builder), Clienti (kiosk check-in) |
| **Status** | In produzione attiva. Fase 8 aperta (debito tecnico residuale). |

---

## 2. STACK TECNOLOGICO COMPLETO

### Frontend

| Componente | Tecnologia | Versione / Note |
|---|---|---|
| Framework | Vue 3 | Composition API, `<script setup>` |
| UI Kit | Quasar Framework | v2.18.6 |
| State Management | Pinia | 6 stores attivi |
| Bundler | Vite | via @quasar/app-vite 2.4.0 |
| Cloud SDK | Supabase JS Client | Comunicazione diretta frontend→cloud |
| Firma Digitale | Canvas HTML5 nativo | Touch-optimized per mobile |
| QR Code | API esterna qrserver | Generazione Magic Link per Kiosk |

### Backend

| Componente | Tecnologia | Versione / Note |
|---|---|---|
| Framework | FastAPI | Python 3.10+ |
| ORM | SQLAlchemy | Solo per catalogo locale e Motore Predittivo |
| DB Locale | SQLite | File `rafting.db` |
| DB Cloud | Supabase | PostgreSQL via PostgREST |
| HTTP Client | httpx | Sync Sonda, Dual-Write, comunicazione Supabase |
| WSGI Bridge | a2wsgi | Deploy Passenger su Ergonet |
| AI Vision | Azure OCR | Cognitive Services — API REST cloud |
| PDF Generation | reportlab | Certificati, manleve, consensi |

### Deploy (Ergonet CloudLinux)

| Vincolo | Dettaglio |
|---|---|
| Hard Limit RAM | **1GB** (LVE). Vietati modelli AI locali |
| Reverse Proxy | Apache + Passenger (`passenger_wsgi.py`) |
| Frontend | SPA statica servita da Apache in `httpdocs/` |
| Backend | Python venv + gunicorn + UvicornWorker su `127.0.0.1:8000` |
| Nginx Proxy | `/api/*` → backend locale |
| Azure OCR | API REST cloud, zero consumo RAM locale |

---

## 3. ARCHITETTURA IBRIDA — DUAL DATABASE

> [!IMPORTANT]
> Il sistema opera con un'architettura **Split-Brain Controllato**: due database separati con un bridge applicativo. Comprenderla è prerequisito fondamentale.

### Regola Fondamentale

- Il **Catalogo** (entità deterministiche) vive su **SQLite locale**.
- I **Dati Transazionali** (dati caldi operativi) vivono **SOLO su Supabase** (PostgreSQL cloud).
- I **Turni** (`rides`/`daily_rides`) esistono in **ENTRAMBI** i DB con lo **STESSO UUID** → **Dual-Write**.

### Diagramma del Flusso Dati

| Operazione | SQLite | Supabase | Meccanismo |
|---|---|---|---|
| Catalogo attività, staff, fleet | ✅ WRITE/READ | ❌ | SQLAlchemy ORM |
| Crea turno | ✅ WRITE | ✅ WRITE | **Dual-Write** (stesso UUID) |
| Crea ordine POS | ❌ | ✅ WRITE | httpx → PostgREST |
| Registra pagamento | ❌ | ✅ WRITE | httpx → PostgREST |
| Salva equipaggio | ❌ | ✅ WRITE | httpx → PostgREST |
| Calcola disponibilità | ✅ READ (Engine) | ✅ READ (Sync Sonda pax) | Engine locale + httpx |
| Check-in consenso | ❌ | ✅ WRITE | httpx → PostgREST |
| CRM Silente (clienti) | ❌ | ✅ UPSERT | httpx → PostgREST |

### La Sync Sonda (Bypass Split-Brain)

Il router [calendar.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py) usa `httpx` per estrarre i `booked_pax` reali da Supabase e li inietta nel Motore Predittivo locale come `external_pax_map` (Dependency Injection). Questo disinnsca il bug "Zero Assoluto" (ORM locale isolato dal cloud).

---

## 4. MAPPA COMPLETA DEL DATABASE

### 4.A — SQLite Locale (`rafting.db`) — 10 Tabelle

| # | Tabella | Ruolo | Modello ORM | Stato |
|---|---|---|---|---|
| 1 | `activities` | Catalogo attività + `workflow_schema` (JSON BPMN) | [ActivityDB](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#23-54) | ✅ Attivo |
| 2 | `activity_sub_periods` | Override stagionali (prezzo, orari, soglie per sottoperiodi) | [ActivitySubPeriodDB](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#59-75) | ✅ Attivo |
| 3 | `daily_rides` | Turni materializzati + status semaforo + `is_overridden` | [DailyRideDB](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#94-115) | ✅ Attivo (Dual-Write con Supabase) |
| 4 | `orders` | Mirror locale ordini (DEPRECATO per flussi commerciali) | [OrderDB](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#133-174) | ⚠️ Legacy — scrive solo SQLAlchemy, la cassa usa Supabase |
| 5 | `transactions` | Locale (DEPRECATO) | [TransactionDB](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#178-191) | ⚠️ Legacy — cassa esclusivamente su Supabase |
| 6 | `customers` | CRM locale (DEPRECATO) | [CustomerDB](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#119-129) | ⚠️ Legacy — CRM Silente su Supabase |
| 7 | `staff` | Anagrafica guide/autisti, contratti, brevetti, ruoli | [StaffDB](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#195-207) | ✅ Attivo |
| 8 | `fleet` | Mezzi: RAFT (capacity), VAN (has_tow_hitch), TRAILER (max_rafts) | [FleetDB](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#208-222) | ✅ Attivo |
| 9 | `system_settings` | Variabili globali EAV (`raft_capacity`, `van_seats`, ecc.) | [SystemSettingDB](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#264-272) | ✅ Attivo |
| 10 | `resource_exceptions` | Ferie, manutenzioni, disponibilità extra (diario calendario) | [ResourceExceptionDB](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#239-260) | ✅ Attivo |
| 11 | `registrations` | Slot consenso Check-in (tabella RegistrationDB, modulo separato) | `RegistrationDB` | ✅ Attivo |

### Tabelle M2M Dichiarate MORTE (da rimuovere in Fase 8)

| Tabella | Stato | Note |
|---|---|---|
| `crew_assignments` | ☠️ MORTA, 0 righe | Sostituita da `ride_allocations` JSONB su Supabase |
| `ride_staff_link` | ☠️ MORTA, 0 righe | Fossile Fase 6.B, mai popolata |
| `ride_fleet_link` | ☠️ MORTA, 0 righe | Fossile Fase 6.B, mai popolata |

### Colonne Critiche `daily_rides`

| Colonna | Tipo | Significato |
|---|---|---|
| [id](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#94-115) | UUID (String 36) | PK condivisa tra SQLite e Supabase |
| `activity_id` | FK → `activities.id` | Tipo attività |
| `ride_date` | Date | Data turno |
| `ride_time` | Time | Ora turno |
| `status` | String(1) | A=Verde, B=Giallo, C=Rosso, D=Blu, X=Chiuso |
| `is_overridden` | Boolean | Se True → Engine NON ricalcola (Dogma Override) |
| `notes` | Text | Appunti operativi |

### Colonne Critiche `staff`

| Colonna | Tipo | Significato |
|---|---|---|
| [id](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#94-115) | UUID | PK |
| `name` | String | Nome risorsa |
| `contract_type` | String | "FISSO" o "EXTRA" |
| `is_guide` | Boolean | Abilitato come guida |
| `is_driver` | Boolean | Patente navetta |
| `roles` | JSON | Multi-ruolo: `["RAF4","SK","NC"]` |
| `contract_periods` | JSON | Periodi contratto: `[{"start":"2026-05-01","end":"2026-09-30"}]` |
| `is_active` | Boolean | Flag attivazione |

### Colonne Critiche `fleet`

| Colonna | Tipo | Significato |
|---|---|---|
| [id](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#94-115) | UUID | PK |
| `name` | String | Nome mezzo |
| `category` | String | "RAFT", "VAN", "TRAILER" |
| `capacity` | Integer | Posti pax (gommoni) o posti sedere escluso autista (furgoni) |
| `has_tow_hitch` | Boolean | Solo VAN: dotato di gancio traino |
| `max_rafts` | Integer | Solo TRAILER: quanti gommoni può trasportare |
| `is_active` | Boolean | Flag attivazione |

### Colonne Critiche `activities`

| Colonna | Tipo | Significato |
|---|---|---|
| `workflow_schema` | JSON | Schema flussi BPMN `{"flows":[...], "logistics":{...}}` |
| `default_times` | JSON | Orari base `["09:00","14:00"]` |
| `yellow_threshold` | Integer | Posti residui per semaforo giallo |
| `overbooking_limit` | Integer | Posti extra vendibili prima del rosso |
| `allow_intersections` | Boolean | Consenti incroci fiume (ARR Cascade) |
| `activity_class` | String | "RAFTING", "HYDRO", "KAYAK" |

### 4.B — Supabase Cloud (PostgreSQL) — 6 Tabelle

| # | Tabella | Ruolo | Comunicazione Backend |
|---|---|---|---|
| 1 | `rides` | Turni operativi (stessa UUID di `daily_rides`) | httpx PostgREST |
| 2 | `orders` | Ordini clienti (`pax`, `price_total`, `price_paid`, FK → `rides`) | httpx PostgREST |
| 3 | `transactions` | Libro Mastro pagamenti (`amount`, `method`, `type`, FK → `orders`) | httpx PostgREST |
| 4 | `registrations` | Partecipanti individuali (consensi, FIRAFT) | httpx PostgREST |
| 5 | `customers` | Anagrafica CRM cloud | httpx PostgREST (UPSERT) |
| 6 | `ride_allocations` | Assegnazione risorse (`metadata` JSONB — Busta Stagna Crew Builder) | httpx PostgREST |

### Colonne Critiche `ride_allocations`

| Colonna | Tipo | Significato |
|---|---|---|
| `ride_id` | UUID | FK → `rides.id` |
| `resource_id` | UUID | **Chiave Logica** (no FK fisica!) verso `staff`/`fleet` in SQLite |
| `resource_type` | String | `"crew_manifest"` (unico tipo attivo per Crew Builder) |
| `metadata` | JSONB | Busta Stagna: `{ guide_id, guide_name, groups: [{ order_id, customer_name, pax }] }` |

> [!WARNING]
> Il `resource_id` in `ride_allocations` NON ha vincoli FK fisici verso le tabelle SQLite. È una **Chiave Logica** validata solo applicativamente (Dogma 12). Il vincolo FK è stato amputato il 27/02/2026 dopo errori `409 Conflict`.

---

## 5. BACKEND — ROUTERS, MODELLI E SERVIZI

### 5.A — Routers Registrati ([main.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/main.py))

| # | Prefix | File Router | Tags | Note |
|---|---|---|---|---|
| 1 | `/api/v1/vision` | [vision.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/api/v1/endpoints/vision.py) (1.7KB) | AI Vision | Azure OCR analisi documenti |
| 2 | `/api/v1/registration` | [registration.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/registration.py) (10.8KB) | Registration | Gestione registrazioni e consensi |
| 3 | `/api/v1/resources` | [resources.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/resources.py) (2.6KB) | Resources | CRUD Staff & Fleet (SQLite) |
| 4 | `/api/v1/reservations` | [reservations.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/api/v1/endpoints/reservations.py) (1.3KB) | Reservations | Overrides e prenotazioni |
| 5 | `/api/v1/calendar` | [calendar.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py) (33KB) | Calendar | **BFF principale**: CRUD attività, daily-rides, Motore Engine, Sync Sonda |
| 6 | `/api/v1/legacy-orders` | [orders.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/orders.py) (12KB) | Orders (Legacy) | ⚠️ DEPRECATO — ORM locale, backward-compat |
| 7 | `/api/v1/firaft` | [firaft.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/api/v1/endpoints/firaft.py) (4.6KB) | FiRaft | Gestione tesseramento |
| 8 | `/api/v1/logistics` | [logistics.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/logistics.py) (9KB) | Logistics | Staff/Fleet attivo per Engine |
| 9 | `/api/v1/orders` | [desk.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/desk.py) (17KB) | Desk POS | **POS Operativo** — httpx → Supabase |
| 10 | `/api/v1/public` | [public.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/public.py) (5.2KB) | Public Check-in | NO AUTH — Kiosk Magic Link |
| 11 | `/api/v1/availability` | [availability.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/availability.py) (1.2KB) | Availability Engine | Calcolo singola attività |
| 12 | `/api/v1/crew` | [crew.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/api/v1/endpoints/crew.py) (7.8KB) | Crew Builder | GET/PUT allocazioni equipaggi |

### 5.B — Endpoints Chiave

**Calendar (BFF Principale):**
- `GET /api/v1/calendar/activities` → Lista attività attive (SQLite)
- `POST /api/v1/calendar/activities` → Crea attività
- `PUT /api/v1/calendar/activities/{id}` → Aggiorna attività
- `GET /api/v1/calendar/daily-rides?date=YYYY-MM-DD` → Turni + Engine (filtro status≠X)
- `POST /api/v1/calendar/daily-rides/close` → Kill-Switch turno vuoto (status=X)
- `PATCH /api/v1/calendar/daily-rides/{id}/status` → Semaforo manuale Dual-Write SQLite
- `GET /api/v1/calendar/daily-rides/export-firaft` → Export CSV FIRAFT

**Desk POS:**
- `POST /api/v1/orders/desk` → Crea ordine POS (httpx → Supabase + CRM Silente)
- `POST /api/v1/orders/{order_id}/transactions` → Registra pagamento (Supabase)

**Crew Builder:**
- `GET /api/v1/crew/allocations?ride_id=UUID` → Leggi equipaggi turno
- `PUT /api/v1/crew/allocations?ride_id=UUID` → Salva equipaggi (Swap & Replace)

**Public (NO AUTH):**
- `GET /api/v1/public/orders/{order_id}/info` → Info discesa per header consenso
- `POST /api/v1/public/orders/{order_id}/fill-slot` → Auto-Slotting Pac-Man

### 5.C — Servizi

| File | Dimensione | Ruolo |
|---|---|---|
| [availability_engine.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/availability_engine.py) | 22KB | **Motore Predittivo** — Time-Array Slicer 1440 min, 2 Pass |
| [yield_engine.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/yield_engine.py) | 22KB | Engine di calcolo yield (legacy V5, ancora in uso) |
| [azure_document_service.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/azure_document_service.py) | 15.6KB | OCR documenti via Azure Cognitive Services |
| [waiver_service.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/waiver_service.py) | 14KB | Generazione PDF manleva (reportlab) |
| [local_vision_service.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/local_vision_service.py) | **36KB** | ☠️ **DA ELIMINARE** — Paddle+YOLO+GLiNER, mai usato in prod |
| [image_utils.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/image_utils.py) | 12.6KB | Utilità processamento immagini |
| [document_specs.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/document_specs.py) | 4KB | Specs formati documenti identità |
| [waiver_mailer.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/waiver_mailer.py) | 1.8KB | Invio email manleva |

### 5.D — Schemas (Pydantic)

| File | Dimensione | Contenuto |
|---|---|---|
| [calendar.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py) | 5.2KB | ActivityCreate/Response, DailyRideCreate/Response, SubPeriodSchema |
| [desk.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/desk.py) | 3KB | DeskOrderCreate, SplitItem, ExtraItem (POS) |
| [orders.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/orders.py) | 4.4KB | TransactionCreate, OrderResponse |
| [logistics.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/logistics.py) | 4KB | StaffResponse, FleetResponse |
| [registration.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/registration.py) | 6.3KB | RegistrationCreate, SlotData, ConsentData |
| [resources.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/resources.py) | 5.6KB | StaffCreate/Update, FleetCreate/Update, ExceptionCreate |
| [availability.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/availability.py) | 495B | AvailabilityQuery |
| [public.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/public.py) | 572B | FillSlotRequest |

### 5.E — File Requirements (Proliferazione da consolidare)

| File | Destinazione |
|---|---|
| [requirements.txt](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/requirements.txt) | ⚠️ Sviluppo — da consolidare |
| [requirements_fixed.txt](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/requirements_fixed.txt) | ⚠️ Con dipendenze AI pesanti — da consolidare |
| [requirements_frozen.txt](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/requirements_frozen.txt) | ⚠️ Snapshot pip freeze — da eliminare |
| [requirements_lock.txt](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/requirements_lock.txt) | ⚠️ Lock file — da eliminare |
| [requirements_production.txt](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/requirements_production.txt) | ✅ **Produzione** — senza AI, quello che viene deployato |

---

## 6. FRONTEND — PAGINE, COMPONENTI E STORES

### 6.A — Rotte Attive

| Path | Pagina | Ruolo | Auth |
|---|---|---|---|
| `/` → `/consenso` | `ConsentFormPage.vue` | Kiosk Pubblico (Magic Link, 6 step) | ❌ NO |
| `/login` | [LoginPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/LoginPage.vue) | Autenticazione | ❌ NO |
| `/admin/operativo` | [PlanningPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/PlanningPage.vue) | **Calendario Operativo** — hub principale | ✅ SÌ |
| `/admin/segreteria` | [PlanningPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/PlanningPage.vue) | Stessa vista → Omni-Board collapse | ✅ SÌ |
| `/admin/timeline` | [TimelinePage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/admin/TimelinePage.vue) | Vista Gantt + Ruoli + Barra Saturazione | ✅ SÌ |
| `/admin/board` | [DailyBoardPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/admin/DailyBoardPage.vue) | Lavagna Operativa daily | ✅ SÌ |
| `/admin/impostazioni` | [SettingsPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/admin/SettingsPage.vue) | Costruttore Flussi BPMN a mattoncini | ✅ SÌ |
| `/admin/risorse` | [ResourcesPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/ResourcesPage.vue) | CRUD Staff & Fleet — **ORGANO VITALE** | ✅ SÌ |
| `/admin/registrazioni` | [RegistrationsPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/admin/RegistrationsPage.vue) | Archivio Consensi | ✅ SÌ |
| `/admin/scanner/:id?` | [ScannerPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/ScannerPage.vue) | Scanner documenti AI | ✅ SÌ |

### 6.B — Componenti

| Componente | Dimensione | Ruolo |
|---|---|---|
| [RideDialog.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/components/RideDialog.vue) | **48KB** | Modale Omni-Board suprema (Tabs: Ordini/POS/Crew) |
| [PlanningPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/PlanningPage.vue) | **35KB** | Griglia turni con semaforo, calendario mensile |
| [SettingsPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/admin/SettingsPage.vue) | **38KB** | Costruttore Flussi BPMN a mattoncini |
| [ResourcesPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/ResourcesPage.vue) | **30KB** | CRUD Staff & Fleet |
| [ScannerPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/ScannerPage.vue) | **28KB** | Scanner documenti AI (Azure OCR) |
| [TimelinePage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/admin/TimelinePage.vue) | **25KB** | Vista Gantt Multi-Lane |
| [CrewBuilderPanel.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/components/CrewBuilderPanel.vue) | **24KB** | Tab Equipaggi (Banchina + Fiume + Sensori) |
| [SeasonConfigDialog.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/components/SeasonConfigDialog.vue) | 21KB | Dialog configurazione stagione |
| [CalendarComponent.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/components/CalendarComponent.vue) | 18KB | Calendario mensile con colori semaforo |
| [ResourcePanel.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/components/ResourcePanel.vue) | 20KB | Pannello dettaglio singola risorsa |
| [DeskBookingForm.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/components/DeskBookingForm.vue) | 10.6KB | Form POS estratto (Ledger Misto, Spacca-Conto) |
| [DailyBoardPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/admin/DailyBoardPage.vue) | 10.6KB | Lavagna giornaliera |
| [RegistrationsPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/admin/RegistrationsPage.vue) | 13.7KB | Archivio consensi |
| [CameraCapture.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/components/CameraCapture.vue) | 11.6KB | Cattura foto documento |
| [FiraftDialog.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/components/FiraftDialog.vue) | 5.9KB | Dialog tesseramento FiRaft |
| [QrDialog.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/components/QrDialog.vue) | 0.9KB | QR Code Magic Link |
| [ModuleCard.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/components/ModuleCard.vue) | 1.4KB | Card modulo generica |

### 6.C — Pinia Stores

| Store | Dimensione | Ruolo |
|---|---|---|
| [resource-store.js](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/stores/resource-store.js) | **35.5KB** | **Store principale**: staffList, fleetList, dailySchedule, activities, Merge Difensivo, Ghost Slots, Override Guard, Kill-Switch Client |
| [crew-store.js](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/stores/crew-store.js) | 5.1KB | Allocazioni equipaggi, `loadCrew`, `saveCrew`, getter `hasAnyOverflow` |
| [registration-store.js](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/stores/registration-store.js) | 9.7KB | Gestione registrazioni e consensi |
| [settings-store.js](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/stores/settings-store.js) | 3.4KB | System settings EAV |
| [auth-store.js](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/stores/auth-store.js) | 1.6KB | Autenticazione utente |
| [index.js](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/stores/index.js) | 0.5KB | Bootstrap Pinia |

### 6.D — Composables

| Composable | Ruolo |
|---|---|
| `useCheckin.js` | `getMagicLink`, `copyMagicLink`, `openQrModal`, `shareWhatsApp` |

---

## 7. FLUSSI DATI CRITICI

### 7.1 — Prenotazione POS (Dual-Write)

DeskBookingForm → POST /orders/desk
→ httpx → Supabase: INSERT orders, transactions, rides (UUID condiviso)
→ SQLAlchemy → SQLite: INSERT/UPDATE daily_rides (stesso UUID)
→ CRM Silente: UPSERT customers (Supabase)

### 7.2 — Semaforo Manuale (Dual-Write)

RideDialog [ROSSO] → await Supabase rides.update(status='C', is_overridden=true)
→ await PATCH /daily-rides/{id}/status → SQLite (status='C', is_overridden=1)
→ Store Pinia: aggiornamento reattivo immediato

### 7.3 — Kill-Switch Turno Vuoto

PlanningPage [🗑️] → dialog conferma → POST /daily-rides/close
→ SQLite: status='X', is_overridden=1, note += "[CHIUSO MANUALMENTE]"
→ Store: dailySchedule.splice(idx, 1) — rimozione reattiva immediata

### 7.4 — Check-in Digitale (Magic Link)

Segreteria → useCheckin.getMagicLink(order) → WhatsApp / QR Code
Cliente → ConsentFormPage (6 step) → POST /public/fill-slot
→ RegistrationDB: status EMPTY → COMPLETED, dati anagrafici + firma
→ Generazione PDF manleva (reportlab)

### 7.5 — Crew Builder (Swap & Replace)

CrewBuilderPanel → saveCrew(ride_id, payload)
→ crew-store.js → PUT /api/v1/crew/allocations?ride_id=UUID
→ Backend: DELETE ride_allocations WHERE ride_id=target
→ Backend: bulk INSERT nuove allocazioni via httpx PostgREST
→ Sensori UI: Bilancia Banchina + Galleggiamento + Kill-Switch Varo

### 7.6 — Refresh Pagina Calendario

PlanningPage onMounted → fetchDailySchedule(date)
→ Supabase: rides + orders + allocations (verità fisica)
→ FastAPI: /daily-rides?date= → Sync Sonda + Engine.calculate_availability()
→ Merge Difensivo con Override Guard → UI aggiornata

### 7.7 — Motore Predittivo (2 Pass)

**Pass 1 — River Ledger:**
Per ogni turno ordinato per orario:
1. Se status='X' → skip (chiuso)
2. Se is_overridden=True → bypass completo, restituisci status DB
3. Calcola booked_pax (da external_pax_map Supabase)
4. Harvesting ARR (posti vuoti in cascata)
5. Calcola barche necessarie
6. Costruisci timeline BPMN (Two-Pass: anchor start + end)

**Pass 2 — Semaforo Asimmetrico:**
Per ogni turno:
1. Time-Array Slicer (3 array × 1440 interi)
2. total_capacity = (max_boats × raft_capacity) + arr_bonus_seats
3. Soglie: remaining ≤ -overbooking_limit → ROSSO / yield_warning o remaining ≤ yellow → GIALLO / else → VERDE

---

## 8. DOGMI ARCHITETTURALI VIGENTI

I "Dogmi" sono regole inviolabili sancite nel LORE_VAULT.md dopo incidenti e bug in produzione. Ignorarli causa regressioni garantite.

| # | Nome | Regola | Data |
|---|---|---|---|
| — | **Hard Limit LVE** | Max 1GB RAM su Ergonet. Vietato caricare modelli AI locali. Lazy Loading obbligatorio. | — |
| — | **DDL Supabase** | Ogni alterazione DDL DEVE terminare con `NOTIFY pgrst, 'reload schema'` per svuotare la cache PostgREST. | — |
| — | **Override** | Se `is_overridden=True` → Engine NON ricalcola. Bottone AUTO resetta il flag. | 27/02/2026 |
| 10 | **Tetris Umano** | I passeggeri non sono numeri anonimi. La Busta Stagna contiene `groups: [{ order_id, customer_name, pax }]`. Un ordine può essere frammentato su più gommoni. | 27/02/2026 |
| 11 | **Swap & Replace** | Aggiornamento massivo: DELETE tutti i vecchi record + bulk INSERT nuovi. Zero orfani. | 27/02/2026 |
| 12 | **Chiavi Logiche Cross-DB** | Le FK da Supabase verso entità SQLite devono essere **UUID liberi** (no FK fisica). Altrimenti 409 Conflict. | 27/02/2026 |
| 12c | **Sindrome Arto Fantasma** | Se una FK viene amputata, TUTTE le query PostgREST con JOIN verso l'entità scollegata devono essere epurate. Altrimenti PGRST200. | 27/02/2026 |
| 13 | **Kill-Switch del Varo** | L'UI DEVE inibire il salvataggio se: A) mezzo supera capacity, B) imbarcati > paganti. Salvataggi in difetto ammessi (no-show). | 27/02/2026 |

---

## 9. BUG PENDENTI E DEBITO TECNICO

### 9.A — Debito Tecnico ATTIVO (Fase 8 — Task Aperti)

| # | Descrizione | Priorità | File Coinvolti |
|---|---|---|---|
| DT-1 | **Proliferazione requirements**: 5 file requirements ([requirements.txt](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/requirements.txt), `_fixed`, `_frozen`, `_lock`, `_production`). Consolidare in 2: [requirements.txt](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/requirements.txt) (dev) + [requirements_production.txt](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/requirements_production.txt) (prod). | 🟡 Media | `backend/requirements*.txt` |
| DT-2 | **Pulizia commenti JSDoc obsoleti** nel frontend. Referenze a entità morte (YieldEngine V4, Segreteria POS standalone, DeskDashboardPage). | 🟢 Bassa | Codebase frontend |
| DT-3 | **Tabelle SQLite morte** da rimuovere dal modello ORM: `crew_assignments`, `ride_staff_link`, `ride_fleet_link`. 0 righe, mai usate. Rimuovere anche le relationship ORM correlate da [StaffDB](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#195-207), [FleetDB](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#208-222), [DailyRideDB](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py#94-115). | 🟡 Media | [backend/app/models/calendar.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py), [main.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/main.py) |
| DT-4 | **Rimozione [local_vision_service.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/local_vision_service.py)**: 36KB di codice morto (Paddle+YOLO+GLiNER). Sostituito al 100% da Azure OCR. Mai usato in produzione. | 🟡 Media | [backend/app/services/local_vision_service.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/local_vision_service.py) |

### 9.B — Anomalie Strutturali Rilevate (Non bugs, ma rischi)

| # | Descrizione | Rischio | Note |
|---|---|---|---|
| AN-1 | **Modello ORM OrderDB / TransactionDB / CustomerDB in SQLite**: Le tabelle esistono in SQLite ma i flussi operativi (POS, cassa) scrivono SOLO su Supabase via httpx. Le tabelle locali sono potenzialmente disallineate e vuote. Non sono state ancora rimosse per backward-compat con il router [orders.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/orders.py) legacy. | 🟠 Coerenza | Rimozione safe solo dopo verifica che nessun endpoint attivo le usi |
| AN-2 | **Router [orders.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/schemas/orders.py) legacy** montato su `/api/v1/legacy-orders`: contiene ancora la logica ORM locale. Da verificare se qualche frontend lo chiama ancora prima di rimuoverlo. | 🟠 Coerenza | Potenziale dead code |
| AN-3 | **Router [reservations.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/api/v1/endpoints/reservations.py)** (1.3KB): dimensione minima, probabilmente stub. Da verificare se è ancora usato o è un fossile. | 🟢 Bassa | Controllare eventuali chiamate frontend |
| AN-4 | **CORS `allow_origins=["*"]`**: Permissivo per sviluppo. In produzione su Ergonet → il proxy Nginx gestisce la sicurezza. Valutare restrizione per hardening. | 🟢 Bassa | Configurabile via .env |
| AN-5 | **[DEPLOY.md](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/DEPLOY.md) menziona gunicorn/systemd** ma le regole architettura impongono `passenger_wsgi.py` con `a2wsgi`. Il DEPLOY.md potrebbe essere disallineato dalla realtà produttiva. | 🟡 Media | Verificare procedura reale di deploy |
| AN-6 | **[README.md](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/README.md) cita Paddle+YOLO+GLiNER come stack AI**. In realtà il sistema usa Azure OCR in produzione. README obsoleto. | 🟡 Media | Aggiornare |

### 9.C — Bug Risolti Recentemente (Riferimento per regressioni)

| Bug | Soluzione | Data | Dogma |
|---|---|---|---|
| 401 JWT Auth Crew Builder | Chiavi Supabase migrate da hardcode a `.env` con `load_dotenv()` + `.strip()` | 27/02 | — |
| 422 Pydantic mismatch `resource_type` | "RAFT" → "crew_manifest" | 27/02 | — |
| 409 FK violation `ride_allocations_resource_id_fkey` | Amputazione FK fisica Supabase | 27/02 | Dogma 12 |
| PGRST200 Ghost Limb | Rimozione JOIN PostgREST `resources(*)` dal frontend | 27/02 | Dogma 12c |
| Passeggero Fantasma (+1) nella formula furgoni | `math.ceil(booked_pax / van_net_seats)` senza margine | 27/02 | Formula Deterministica |
| Zero Assoluto (ORM locale isolato) | Sync Sonda httpx per `external_pax_map` | 25/02 | — |
| Split-Brain Desk POS | Sventramento SQLAlchemy, sostituzione con httpx nativo | 26/02 | — |

---

## 10. STORICO FASI COMPLETATE

| Fase | Nome | Data | Sintesi |
|---|---|---|---|
| **5** | Motore BPMN e Yield Engine V5 | Pre-24/02 | Incenerito V4, Costruttore Flussi a mattoncini, Yield Engine V5, Scudo Anti-Ubiquità |
| **6** | Logistica Fluidodinamica e POS Ibrido | 24-27/02/2026 | 12+ sottofasi. Time-Array Slicer, ARR Cascade, Split-Brain risolto, Dual-Write, Omni-Board, Timeline Gantt, Drag&Drop BPMN, Spurgo Sentina |
| **6.A** | Daily Board Onesta | 24/02 | Estirpato hardcode "16 pax", lettura veri booked_pax |
| **6.B** | Crew Builder Blueprint | 24/02 | Architettura ride_allocations teorizzata |
| **6.D** | Sacco Risorse | 25/02 | Footprint logistico in workflow_schema.logistics |
| **6.E.1-7** | Availability Engine | 25-26/02 | Sensori Pinia, Time-Array Slicer, Eccezione di Sarre, Safety Kayak, River Ledger, Sync Sonda |
| **6.F** | Fix Engine Precision | 27/02 | Eliminato Passeggero Fantasma (+1) |
| **6.G** | Persistenza Override | 27/02 | Colonna is_overridden, bypass Engine |
| **6.H** | Kill-Switch Turni Vuoti | 27/02 | Endpoint POST /daily-rides/close |
| **6.I** | Dual-Write Semaforo | 27/02 | Bottoni manuali con Dual-Write |
| **6.J** | Timeline Flussi | 27/02 | Vista Gantt + Multi-Lane Packing + Barra Saturazione |
| **6.K** | Spurgo Sentina | 27/02 | 9 file inceneriti, DeskDashboardPage distrutta |
| **6.L** | Drag & Drop BPMN | 27/02 | Riordinamento blocchi HTML5 Drag&Drop |
| **7** | Crew Builder | 27/02/2026 | 5 sottofasi. Scaffold → DDL → UI → Backend → Sensori → Collaudo E2E |
| **7.A** | Scaffold Tubature | 27/02 | Router crew.py, CrewBuilderPanel.vue, tab Equipaggi |
| **7.B** | Fondazione Busta Stagna | 27/02 | DDL ride_allocations JSONB, crew-store.js |
| **7.C** | Banchina d'Imbarco UI | 27/02 | UI righe dinamiche, contatori pax, SIGILLA EQUIPAGGI |
| **7.C.2** | Tetris Umano | 27/02 | Assegnazione nominale per gruppi/ordini |
| **7.D** | Allineamento Valvola Backend | 27/02 | Pydantic allineamento, Swap & Replace |
| **7.D.fix** | Autopsia Tripla | 27/02 | Fix JWT, FK, PGRST200 |
| **7.E** | Sensori e Bilancia | 27/02 | 3 sensori visivi, Kill-Switch Varo |
| **7.E.fix** | Pompa Sentina | 27/02 | Script purge, collaudo E2E OK |

---

## 11. RISCHI E AVVERTIMENTI PER IL TECH LEAD

> [!CAUTION]
> **Regola #1: MAI creare FK fisici da Supabase verso entità SQLite.** Il sistema è Split-Brain by design. Le relazioni cross-database sono LOGICHE (UUID condivisi, validati solo applicativamente). Violazione → errore 409 bloccante.

> [!WARNING]
> **Regola #2: Ogni DDL su Supabase DEVE terminare con `NOTIFY pgrst, 'reload schema'`.** Dimenticarlo causa PGRST204 (schema cache stale). Storicamente questo passaggio è stato omesso causando debug inutile.

> [!IMPORTANT]
> **Regola #3: Il file [local_vision_service.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/local_vision_service.py) (36KB) è una bomba a orologeria per la RAM.** Carica Paddle+YOLO+GLiNER in memoria. Non viene mai invocato in produzione (Azure OCR lo ha sostituito) ma un `import` accidentale può far esplodere il limite di 1GB.

> [!NOTE]
> **Regola #4: I dati commerciali (ordini, transazioni, CRM) vivono SOLO su Supabase.** Le tabelle corrispondenti in SQLite (`orders`, `transactions`, `customers`) esistono per backward-compat ORM ma NON sono la source of truth. Non leggere mai da lì per logiche di business.

> [!TIP]
> **Regola #5: Il [resource-store.js](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/stores/resource-store.js) (35KB) è il cuore del frontend.** Contiene il Merge Difensivo, i Ghost Slots, l'Override Guard e il Kill-Switch Client. Ogni modifica qui ha effetto a cascata sull'intera UI operativa.

### File da NON Toccare senza comprensione completa

| File | Motivo |
|---|---|
| [availability_engine.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/services/availability_engine.py) | Motore matematico critico, formula deterministica |
| [resource-store.js](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/stores/resource-store.js) | Hub reattivo con 7+ logiche interconnesse |
| [calendar.py](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/backend/app/models/calendar.py) (endpoint) | 33KB di BFF con Sync Sonda e Dual-Write |
| [RideDialog.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/components/RideDialog.vue) | 48KB — Omni-Board con 3 tabs e semaforo |
| [ResourcesPage.vue](file:///c:/Users/RAFTING/Desktop/Gestionale%20RR/Nuovo-Gestionale-RR/web-app/src/pages/ResourcesPage.vue) | CRUD vitale — tentativo di amputazione abortito 26/02 |

### Backlog Strategico (Post Fase 8)

| Priorità | Iniziativa | Stato |
|---|---|---|
| 1 | **Fase 8 Attiva**: Consolidamento requirements, pulizia JSDoc, rimozione tabelle/file morti | 🔵 In corso |
| 2 | Modulo Presenze Giornaliere Staff | 📋 Backlog |
| 3 | Flusso Prenotazioni CRM (Anagrafiche, Pagamenti) | 📋 Backlog |

---

**Fine Report. Documento generato automaticamente dall'analisi dei file sorgente.**
**Il Tech Lead è invitato a leggere LORE_VAULT.md per il contesto storico e TECH_ARCHITECTURE.md per il dettaglio degli endpoint.**
