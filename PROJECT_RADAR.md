# PROJECT RADAR — Rafting Republic Gestionale

> Generato: 2026-02-23 · Destinatario: Architetto AI esterno  
> Scopo: Sincronizzazione stato reale del progetto

---

## 1. STACK TECNOLOGICO

| Layer             | Tecnologia           | Versione                             | Note                                                      |
| ----------------- | -------------------- | ------------------------------------ | --------------------------------------------------------- |
| **Framework**     | Vue 3                | `<script setup>` Composition API     | SFC everywhere                                            |
| **UI Kit**        | Quasar               | v2.18.6                              | `@quasar/app-vite` v2.4.0                                 |
| **Bundler**       | Vite                 | v7.3.1                               | via Quasar CLI                                            |
| **State**         | Pinia                | `defineStore`                        | 4 store: resource, reservation, registration, auth        |
| **DB/BaaS**       | Supabase             | JS Client v2                         | PostgreSQL hosted, anon key auth                          |
| **API Legacy**    | WordPress REST + JWT | via `wpApi` axios instance           | Solo per auth login (`/jwt-auth/v1/token`)                |
| **API Backend**   | FastAPI (Python)     | via `api` axios instance (`/api/v1`) | Parzialmente usato per `reservations`, `firaft`, `orders` |
| **Deploy Target** | CloudLinux + Ergonet | `passenger_wsgi.py`                  | RAM limit 1GB, no uvicorn diretto                         |
| **Architettura**  | JAMstack ibrido      | SPA (`spa` mode build)               | Static frontend + Supabase + FastAPI backend              |

### Canali di Comunicazione (axios boot)

```
api     → /api/v1           (FastAPI locale)
wpApi   → $VITE_WP_BASE_URL/wp-json (WordPress, solo auth)
supabase → SDK diretto       (import from src/supabase.js)
```

---

## 2. SCHEMA DB SUPABASE (Colonne Attivamente Interrogate)

Basato sulle query `.from().select()` presenti nel codice frontend:

### `activities`

| Colonna        | Usata in                                              | Note                                 |
| -------------- | ----------------------------------------------------- | ------------------------------------ |
| `id`           | fetchCatalogs                                         | UUID PK                              |
| `name`         | fetchCatalogs, fetchMonthOverview, fetchDailySchedule | Nome attività (es. "Rafting Family") |
| `color`        | fetchMonthOverview, fetchDailySchedule                | HEX color per UI (es. "#4CAF50")     |
| `*` (wildcard) | fetchDailySchedule                                    | Tutte le colonne via `activities(*)` |

> ⚠️ **NON ESISTONO** nel DB: `color_hex`, `code` — queste colonne sono state rimosse dalle query in Fase 3.19/3.20 dopo errori `42703`.

### `rides`

| Colonna         | Usata in                               | Note                                                     |
| --------------- | -------------------------------------- | -------------------------------------------------------- |
| `id`            | Everywhere                             | UUID PK                                                  |
| `date`          | fetchDailySchedule, fetchMonthOverview | `DATE` type (può arrivare con timestamp ISO `T00:00:00`) |
| `time`          | fetchDailySchedule, fetchMonthOverview | `TIME` type (es. "09:00:00")                             |
| `activity_id`   | fetchDailySchedule, saveOrder          | FK → activities                                          |
| `status`        | fetchDailySchedule                     | Stato ride                                               |
| `is_overridden` | fetchDailySchedule                     | Override semaforo manuale                                |
| `notes`         | fetchDailySchedule                     | Note testuali                                            |

### `orders`

| Colonna          | Usata in                               | Note                       |
| ---------------- | -------------------------------------- | -------------------------- |
| `id`             | PlanningPage (CRUD)                    | UUID PK                    |
| `ride_id`        | saveOrderToSupabase                    | FK → rides                 |
| `pax`            | fetchMonthOverview, fetchDailySchedule | Pax prenotati              |
| `actual_pax`     | fetchMonthOverview, fetchDailySchedule | Pax effettivi (se diversi) |
| `customer_name`  | saveBookingForm                        | Nome referente             |
| `customer_email` | saveBookingForm                        | Email                      |
| `customer_phone` | saveBookingForm                        | Telefono                   |
| `total_price`    | saveBookingForm                        | Prezzo totale              |
| `status`         | saveBookingForm                        | Stato ordine               |
| `notes`          | saveBookingForm                        | Note                       |

### `resources`

| Colonna | Usata in      | Note                            |
| ------- | ------------- | ------------------------------- |
| `*`     | fetchCatalogs | Wildcard — staff, flotta, mezzi |

### `ride_allocations`

| Colonna       | Usata in                    | Note                                    |
| ------------- | --------------------------- | --------------------------------------- |
| `ride_id`     | saveRideAllocationsSupabase | FK → rides                              |
| `resource_id` | saveRideAllocationsSupabase | FK → resources                          |
| `*`           | fetchDailySchedule          | Via `ride_allocations(*, resources(*))` |

### `participants`

| Colonna                                                | Usata in                         | Note                     |
| ------------------------------------------------------ | -------------------------------- | ------------------------ |
| `id`                                                   | StepReview, DeskDashboard        | UUID PK                  |
| `order_id`                                             | saveOrderToSupabase, ConsentForm | FK → orders              |
| `ride_id`                                              | StepReview                       | FK → rides               |
| `nome`, `cognome`, `email`, `telefono`                 | StepReview, PlanningPage         | Anagrafica               |
| `data_nascita`, `sesso`, `is_minor`                    | StepReview                       | Dati personali           |
| `codice_fiscale`, `residenza`                          | StepReview                       | Dati fiscali             |
| `pdf_path`                                             | StepReview                       | Path PDF consenso        |
| `consenso_privacy`, `consenso_foto`, `consenso_medico` | StepReview                       | Flag legali              |
| `firaft_status`                                        | PlanningPage, StepReview         | Stato tesseramento       |
| `slot_index`                                           | saveOrderToSupabase              | Indice slot partecipante |
| `status`                                               | ConsentFormPage                  | Stato registrazione      |

---

## 3. MODULI COMPLETATI (100% Operativi)

### ✅ Calendario Mese — Lettura e Rendering

- **Store**: `resource-store.js` → `fetchMonthOverviewSupabase(year, month)`
- **Componente**: `CalendarComponent.vue`
- **Consumer**: `PlanningPage.vue` — sezione `v-if="viewMode === 'MONTH'"`
- **Stato**:
  - Query Supabase `rides + activities(name, color) + orders(pax, actual_pax)` ✅
  - Normalizzazione date ISO con `split('T')[0]` ✅
  - Merge 7 ghost slots + turni reali ✅
  - Filtri visivi (`tutto`, `discese`, `staff`) ✅
  - Fallback array con ghost su errore ✅

### ✅ Calendario Giorno — Lettura e Rendering

- **Store**: `resource-store.js` → `fetchDailyScheduleSupabase(dateStr)`
- **Consumer**: `PlanningPage.vue` — griglia card con semafori
- **Stato**: Query `rides + activities(*) + orders(*) + ride_allocations(*, resources(*))` ✅
  - Ghost slots generati per orari mancanti (7 baseSlots) ✅
  - Calcolo FIRAFT engine status (VERDE/GIALLO/ROSSO) ✅
  - Capacità: `cap_guides_pax`, `cap_rafts_pax` calcolati da risorse ✅

### ✅ Cataloghi (Attività + Risorse)

- **Store**: `resource-store.js` → `fetchCatalogs()`
- **Tabelle**: `activities(*)`, `resources(*)`
- **Stato**: Caricati all'init, usati ovunque per lookup attività e risorse

### ✅ Auth — Login WordPress JWT

- **Store**: `auth-store.js` → `login()`, `logout()`, `loadSession()`
- **Backend**: WordPress `/wp-json/jwt-auth/v1/token`
- **Stato**: Token in `localStorage`, interceptor 401/403 per auto-logout

### ✅ Kiosk / Consenso Informato — Flusso Completo

- **Route**: `/consenso` (PublicLayout, NO auth)
- **Pagina**: `ConsentFormPage.vue` (24KB, flusso completo)
- **Stepper interno**: `ScannerPage.vue` (6 step: Lingua → Documenti → Contatti → Privacy → Review → Summary)
- **Componenti**: `PersonForm.vue`, `SignaturePad.vue`, `StepDocuments.vue`, `StepReview.vue`
- **Store**: `registration-store.js` (OCR, form mapping, edit mode)
- **Stato**:
  - Upload documenti con compressione client-side ✅
  - OCR via `VisionService.js` ✅
  - Qualità immagine via `ImageQualityService.js` ✅
  - Salvataggio `participants` su Supabase ✅
  - Generazione PDF e upload ✅
  - Slot consumption con `order_id` da URL ✅

### ✅ Gestione Staff & Flotta

- **Pagina**: `ResourcesPage.vue` (19KB, layout 3 colonne)
- **Store**: `resource-store.js` → CRUD su `resources` via Supabase
- **Stato**:
  - Staff Fisso/Extra con CRUD ✅
  - Fleet (Raft, Van, Trailer) con CRUD ✅
  - Calendario eccezioni (assenze/disponibilità) per risorsa ✅
  - Periodi contratto staff fisso ✅

### ✅ Configurazione Stagione

- **Componente**: `SeasonConfigDialog.vue` (20KB, dialog maximized)
- **Stato**:
  - CRUD attività (create, delete) ✅
  - Editing: nome, prezzo, durata, colore, tratti fiume ✅
  - Toggle ARR (incroci fiume) ✅
  - Orari partenza base (6 slot) ✅
  - Sotto-periodi/eccezioni con override prezzo/orari ✅

### ✅ Archivio Registrazioni

- **Pagina**: `admin/RegistrationsPage.vue` (13KB)
- **Stato**: Lista registrazioni da API FastAPI, con dettagli e audit log ✅

---

## 4. MODULI WIP (Lavori in Corso)

### 🔧 Nuova Prenotazione (POS Inline)

| Aspetto                  | File                                                        | Stato                                                                                                                                                                                                                                                                                                                                                                        |
| ------------------------ | ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **UI Modale**            | `PlanningPage.vue` righe 241-396                            | ✅ Completa — form con customer_name, pax, activity select, time, price, notes                                                                                                                                                                                                                                                                                               |
| **Bottone trigger**      | `PlanningPage.vue` riga 147                                 | ✅ `NUOVA PRENOTAZIONE` nel dialog del turno                                                                                                                                                                                                                                                                                                                                 |
| **Logica open**          | `PlanningPage.vue` → `openBookingForm()` righe 1253-1295    | ✅ Completa — ereditarietà contesto ride (data, ora, attività UUID)                                                                                                                                                                                                                                                                                                          |
| **Logica save (CREATE)** | `PlanningPage.vue` → `saveBookingForm()` righe 1334-1375    | ✅ Salva su Supabase via `store.saveOrderToSupabase()` con materializzazione participant slots. Ricarica sia daily che monthly                                                                                                                                                                                                                                               |
| **Logica save (EDIT)**   | `PlanningPage.vue` → `saveBookingForm()` righe 1300-1333    | ✅ Update ordine su Supabase `orders.update()` + sync locale                                                                                                                                                                                                                                                                                                                 |
| **Logica DELETE**        | `PlanningPage.vue` → `deleteBookingOrder()` righe 1377-1428 | ✅ Delete ordine + allocazioni + ride da Supabase                                                                                                                                                                                                                                                                                                                            |
| **Store backend**        | `resource-store.js` → `saveOrderToSupabase()` righe 403-472 | ✅ Upsert ride + insert order + insert participant slots vuoti                                                                                                                                                                                                                                                                                                               |
| **⚠️ ANOMALIA**          | `ReservationWizard.vue`                                     | 🔴 **ORFANO** — Questo componente ha UI completa (328 righe) ma usa `api.post('/reservations/')` verso FastAPI, NON Supabase. Chiama `api.get('/resources/daily-schedule')` per gli slot. **Non è integrato nel flusso POS attuale** (PlanningPage usa la propria modale inline). Rimane montato in `ReservationsPage.vue` ma il backend endpoint potrebbe non esistere più. |
| **⚠️ ANOMALIA**          | `reservation-store.js`                                      | 🔴 **ORFANO** — Store Pinia che fa CRUD via `api` (FastAPI). Non usa Supabase. Usato solo da `ReservationsPage.vue`. Disallineato dal flusso principale.                                                                                                                                                                                                                     |
| **⚠️ ANOMALIA**          | `ReservationsPage.vue`                                      | 🟡 **DA MIGRARE** — Pagina tabella prenotazioni (`/admin/prenotazioni`). Usa `api.get('/reservations/')` (FastAPI). Non usa Supabase. Il Wizard montato qui è quello vecchio.                                                                                                                                                                                                |

### 🔧 Assegnazione Risorse (Logistica Turno)

| Aspetto             | File                                                                                 | Stato                                                                                                |
| ------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| **UI Pannello**     | `PlanningPage.vue` righe ~440-590                                                    | ✅ Dialog con 4 sezioni: Guide, Gommoni, Mezzi, Carrelli. Usa `q-select` multiple con chip           |
| **Bottone trigger** | `PlanningPage.vue` riga 100                                                          | ✅ `Assegna Risorse` nella card slot giornaliera                                                     |
| **Logica open**     | `PlanningPage.vue` → `openResourcePanel(slot)` righe 1552-1560                       | ✅ Pre-popola dalle assegnazioni correnti                                                            |
| **Logica save**     | `PlanningPage.vue` → `saveResourceAllocations()` righe 1562-1594                     | ✅ Salva su Supabase via `store.saveRideAllocationsSupabase(ride, resourceIds)`                      |
| **Store backend**   | `resource-store.js` → `saveRideAllocationsSupabase(ride, resourceIds)` righe 476-516 | ✅ Materializza ghost ride se necessario, delete+insert allocazioni                                  |
| **Visualizzazione** | `PlanningPage.vue` righe 96-99, 139-141                                              | ✅ Chip con nomi staff/fleet nella card e nel dialog header                                          |
| **Status**          |                                                                                      | 🟢 **FUNZIONANTE** — L'intero ciclo open → select → save → reload è completo e operativo su Supabase |

### 🔧 Segreteria / POS (DeskDashboardPage)

| Aspetto                      | File                                                                            | Stato                                                       |
| ---------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **Pagina**                   | `DeskDashboardPage.vue` (42KB, 1036 righe)                                      | 🟡 **PARZIALMENTE OPERATIVO**                               |
| **Route**                    | `/admin/segreteria` (carica `PlanningPage.vue` che innesta `DeskDashboardPage`) | ✅                                                          |
| **Radar Turni**              | Colonna SX: lista turni del giorno con avatar colorato                          | ✅ Funzionante                                              |
| **Tab "Nuova Prenotazione"** | Form inline per creare ordini dal POS                                           | 🟡 UI completa, logica save punta a store Supabase          |
| **Tab "Ordini Esistenti"**   | Lista ordini con gestione pagamenti multi-metodo                                | 🟡 UI completa, CRUD parzialmente operativo                 |
| **Pagamenti**                | Contanti, Carta, Bonifico, Satispay, Buono Regalo                               | 🟡 UI completa, update ordine su Supabase `orders.update()` |
| **Partecipanti**             | Espansione ordine con lista partecipanti FIRAFT                                 | ✅ Fetch `participants` da Supabase                         |
| **Mancante**                 | Stampa ricevuta, integrazione fiscale                                           | 🔴 Non implementato                                         |

### 🔧 FIRAFT Simulator

| Aspetto        | File                                       | Stato                                                        |
| -------------- | ------------------------------------------ | ------------------------------------------------------------ |
| **Servizio**   | `services/FiraftService.js` (712B)         | 🟡 Stub minimale                                             |
| **UI**         | `PlanningPage.vue` → dialog FIRAFT         | 🟡 Dialog con lista partecipanti e bottone tesseramento bulk |
| **Backend**    | Chiama `api.post('/firaft/register-bulk')` | 🟡 Dipende da endpoint FastAPI                               |
| **Export CSV** | `PlanningPage.vue` → `exportFiraft()`      | ✅ Bottone presente                                          |

### 🔧 Magic Link / Check-in Digitale

| Aspetto              | File                                        | Stato                                               |
| -------------------- | ------------------------------------------- | --------------------------------------------------- |
| **Generazione link** | `PlanningPage.vue` → `getMagicLink(order)`  | ✅ Genera URL `#/consenso?order_id=<UUID>`          |
| **Copia clipboard**  | `PlanningPage.vue` → `copyMagicLink(order)` | ✅                                                  |
| **QR Code**          | `PlanningPage.vue` → `openQrModal(order)`   | ✅ Via API esterna `api.qrserver.com`               |
| **WhatsApp share**   | `PlanningPage.vue` → `shareWhatsApp(order)` | ✅ Template messaggio con link                      |
| **Consumo slot**     | `ConsentFormPage.vue` + `StepReview.vue`    | ✅ Legge `order_id` da URL, aggiorna `participants` |

---

## 5. SERVIZI LEGACY WORDPRESS (Non Migrati)

Directory `src/services/wp/` contiene 9 servizi che puntano al backend WordPress originale:

| File                     | Scopo                 | Stato                           |
| ------------------------ | --------------------- | ------------------------------- |
| `AuthService.js`         | Login JWT             | ✅ Attivo (usato da auth-store) |
| `CalendarService.js`     | Lettura calendario WP | 🔴 **Sostituito** da Supabase   |
| `OrderService.js`        | CRUD ordini WP        | 🔴 **Sostituito** da Supabase   |
| `RideService.js`         | CRUD rides WP         | 🔴 **Sostituito** da Supabase   |
| `AvailabilityService.js` | Disponibilità slot WP | 🔴 **Sostituito** da Supabase   |
| `ParticipantService.js`  | Partecipanti WP       | 🔴 **Sostituito** da Supabase   |
| `NoteService.js`         | Note WP               | 🔴 Non usato                    |
| `SearchService.js`       | Ricerca WP            | 🔴 Non usato                    |
| `SubseasonService.js`    | Sotto-stagioni WP     | 🔴 Non usato                    |

> **Raccomandazione**: I file WP `services/wp/` tranne `AuthService.js` possono essere considerati dead code. La migrazione a Supabase è avvenuta direttamente negli store Pinia.

---

## 6. ARCHITETTURA ROUTING

```
/                    → redirect → /consenso
/consenso            → ConsentFormPage.vue (PublicLayout, NO auth)
/login               → LoginPage.vue (standalone, NO layout)
/admin               → MainLayout.vue (sidebar + header)
  /admin/operativo   → PlanningPage.vue (Calendario Operativo)
  /admin/segreteria  → PlanningPage.vue (POS Mode, innesta DeskDashboardPage)
  /admin/scanner/:id → ScannerPage.vue (Stepper 6 step)
  /admin/registrazioni → RegistrationsPage.vue (Archivio admin)
  /admin/prenotazioni  → ReservationsPage.vue (⚠️ usa FastAPI, non Supabase)
  /admin/risorse     → ResourcesPage.vue (Staff + Fleet CRUD)
/:catchAll           → ErrorNotFound.vue
```

> **Nota**: `requiresAuth` è commentato (`// TODO: Riabilitare in produzione`). Attualmente tutte le rotte admin sono accessibili senza login.

---

## 7. MAPPA DIPENDENZE CRITICA

```
PlanningPage.vue (88KB, 1746 righe)
├── CalendarComponent.vue        → Vista mese
├── DeskDashboardPage.vue        → Innestato in mode Segreteria
├── resource-store.js            → Store principale (22KB, 543 righe)
│   ├── supabase client          → Query dirette
│   ├── api (axios)              → FastAPI backend
│   └── State: activities[], resources[], dailySchedule[], staffList[], fleetList[]
├── SeasonConfigDialog.vue       → Configurazione attività
└── supabase (diretto)           → CRUD ordini/partecipanti inline
```

---

## 8. KNOWN ISSUES & TECH DEBT

1. **`ReservationsPage.vue` + `ReservationWizard.vue` + `reservation-store.js`**: Tripletta orfana che usa FastAPI (`/api/v1/reservations/`). Non è integrata con il flusso Supabase. Da decidere: migrare a Supabase o deprecare.

2. **Auth disabilitata**: Il router guard `requiresAuth` è commentato. Tutte le rotte admin sono pubbliche.

3. **`staff_count: 5` hardcoded**: Nel monthly overview. Dovrebbe leggere le assegnazioni reali da `ride_allocations`.

4. **Semaforo Override**: Chiama `api.patch('/calendar/daily-rides/:id/override')` verso FastAPI. Endpoint potenzialmente non attivo.

5. **`PlanningPage.vue` è un monolite**: 1746 righe, 88KB. Candidato per estrazione componenti (BookingDialog, ResourcePanel, FiraftDialog, ParticipantForm).

6. **Servizi WP dead code**: 8 file in `services/wp/` non più utilizzati.
