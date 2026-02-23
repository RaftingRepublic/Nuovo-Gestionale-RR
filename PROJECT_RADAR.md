# 🧭 PROJECT RADAR — Rafting Republic Gestionale

> **Ultima rigenerazione:** 23 Febbraio 2026  
> **Branch:** `main`  
> **Status:** Post-smantellamento monolite — architettura a componenti isolati operativa

---

## 1. STACK TECNOLOGICO

| Layer                      | Tecnologia                                     | Note                                                                             |
| -------------------------- | ---------------------------------------------- | -------------------------------------------------------------------------------- |
| **Frontend**               | Vue 3 (Composition API) + Quasar 2.18 + Vite 7 | SPA servita come pagina statica                                                  |
| **State Management**       | Pinia                                          | Store `resource-store.js` (purificato), `auth-store.js`, `registration-store.js` |
| **BaaS (Source of Truth)** | **Supabase** (PostgreSQL hosted)               | Calendario, ordini, partecipanti, allocazioni risorse                            |
| **Backend Worker**         | FastAPI (Python 3.11)                          | Wrappato in WSGI via `passenger_wsgi.py` + `a2wsgi` per Ergonet CloudLinux       |
| **Hosting**                | Ergonet CloudLinux con LVE                     | RAM Limit 1GB — lazy loading obbligatorio per modelli AI                         |
| **Composables**            | `useCheckin.js`                                | Logica DRY per Magic Link, QR Code, WhatsApp                                     |

### Architettura Ibrida

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Vue 3 SPA     │────▶│   Supabase   │     │  FastAPI Worker   │
│  (Quasar 2.18)  │     │  PostgreSQL  │     │  (passenger_wsgi) │
│                 │────▶│              │     │                   │
│  Pinia Store    │     └──────────────┘     └──────────────────┘
│  useCheckin()   │              ▲                     ▲
└─────────────────┘              │                     │
         │                 BaaS diretto           API Axios
         │              (ordini, rides,        (staff, fleet,
         └──────────────  allocazioni,          settings, FIRAFT,
                          partecipanti)         OCR, transazioni)
```

---

## 2. SCHEMA DB SUPABASE

Tabelle attivamente interrogate dal frontend:

| Tabella            | Operazioni                     | Consumatori principali                                                                                                |
| ------------------ | ------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| `activities`       | SELECT                         | `resource-store.fetchCatalogs()`                                                                                      |
| `resources`        | SELECT                         | `resource-store.fetchCatalogs()`                                                                                      |
| `rides`            | SELECT, INSERT, UPDATE, DELETE | `resource-store.fetchDailySchedule()`, `fetchMonthOverview()`, `saveOrder()`, `RideDialog.vue`, `PlanningPage.vue`    |
| `orders`           | SELECT, INSERT, UPDATE, DELETE | `resource-store.saveOrder()`, `BookingDialog.vue`, `RideDialog.vue`, `DeskDashboardPage.vue`, `PlanningPage.vue`      |
| `ride_allocations` | SELECT, INSERT, DELETE         | `resource-store.saveRideAllocations()`, `ResourcePanel.vue`, `PlanningPage.vue`                                       |
| `participants`     | SELECT, INSERT, UPDATE         | `resource-store.saveOrder()` (slot pre-gen), `StepReview.vue` (Kiosk), `ConsentFormPage.vue`, `DeskDashboardPage.vue` |

---

## 3. MODULI COMPLETATI (100% BaaS)

### 3.1 Architettura a Componenti Isolati

Il monolite `PlanningPage.vue` è stato **smantellato** da ~1800 righe a ~350 righe.  
Ora è un **puro orchestratore** che coordina 5 componenti figli tramite `props` / `emit`:

| Componente          | File              | Righe | Responsabilità                                                                                                          |
| ------------------- | ----------------- | ----- | ----------------------------------------------------------------------------------------------------------------------- |
| `ResourcePanel.vue` | `src/components/` | 162   | Assegnazione guide, gommoni, furgoni, carrelli a un turno                                                               |
| `BookingDialog.vue` | `src/components/` | 296   | Creazione / modifica prenotazioni (Supabase diretto)                                                                    |
| `FiraftDialog.vue`  | `src/components/` | 162   | Simulatore tesseramento FIRAFT con selezione partecipanti                                                               |
| `RideDialog.vue`    | `src/components/` | 750   | Dettaglio turno: ordini a fisarmonica, cruscotto segreteria, drop-outs, pagamenti, semaforo manuale, lista partecipanti |
| `QrDialog.vue`      | `src/components/` | 27    | Modale QR Code riutilizzabile (v-model driven)                                                                          |

### 3.2 Composable DRY — Check-in Digitale

| File                            | Funzioni esportate                                                                               |
| ------------------------------- | ------------------------------------------------------------------------------------------------ |
| `src/composables/useCheckin.js` | `getMagicLink()`, `copyMagicLink()`, `openQrModal()`, `shareWhatsApp()`, `qrDialogOpen`, `qrUrl` |

**Consumatori:** `RideDialog.vue`, `DeskDashboardPage.vue`  
**Duplicazioni eliminate:** 3 implementazioni → 1 composable centralizzato

### 3.3 Store Purificato — Nomenclatura Standard

Le funzioni BaaS dello store sono state rinominate rimuovendo il suffisso `Supabase`:

| Funzione (standard)                      | Tabelle coinvolte                                                     |
| ---------------------------------------- | --------------------------------------------------------------------- |
| `fetchDailySchedule(dateStr)`            | `rides`, `activities`, `orders`, `ride_allocations`, `resources`      |
| `fetchMonthOverview(year, month)`        | `rides`, `activities`, `orders`                                       |
| `saveOrder({...})`                       | `rides` (upsert), `orders` (insert), `participants` (pre-gen slot)    |
| `saveRideAllocations(ride, resourceIds)` | `ride_allocations` (delete + insert), `rides` (ghost materialization) |
| `fetchParticipantsForOrder(orderId)`     | `participants`                                                        |

### 3.4 Mappa Eventi PlanningPage → Figli

```
PlanningPage.vue (Orchestratore — 350 righe)
│
├── CalendarComponent.vue
│     emit: @day-click, @ride-click, @update:month
│
├── RideDialog.vue (v-model="showRideDialog" :ride="rideDialogSlot")
│     emit: @edit-order ──────▶ padre ──▶ BookingDialog
│     emit: @delete-order ────▶ padre ──▶ Supabase DELETE
│     emit: @open-resources ──▶ padre ──▶ ResourcePanel
│     emit: @open-firaft ─────▶ padre ──▶ FiraftDialog
│     emit: @refresh ─────────▶ padre ──▶ reloadCalendarData()
│
├── BookingDialog.vue (v-model="bookingDialogOpen")
│     emit: @saved ───────────▶ padre ──▶ onBookingSaved()
│
├── ResourcePanel.vue (v-model="resourcePanelOpen")
│     emit: @saved ───────────▶ padre ──▶ onResourcePanelSaved()
│
├── FiraftDialog.vue (v-model="firaftModalOpen")
│     emit: @registered ──────▶ padre ──▶ onFiraftRegistered()
│
└── SeasonConfigDialog.vue (ref="seasonDialog")
```

---

## 4. MODULI WIP E DA IMPLEMENTARE

### 4.1 Priorità Assolute

| #      | Modulo                        | Status     | Dettaglio                                                                                                                                                                                                  |
| ------ | ----------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P1** | **Stampa Fiscale / Ricevute** | 🔴 DA FARE | Integrazione stampante termica per la DeskDashboard (POS). Richiede libreria driver-side o API cloud di stampa.                                                                                            |
| **P2** | **Motore FIRAFT Python**      | 🟡 WIP     | Endpoint `POST /api/v1/firaft/register-bulk` attivo nel backend FastAPI. Consumato da `RideDialog.vue` via Axios. Da migrare eventualmente a Supabase Edge Function o mantenere come microservizio Python. |

### 4.2 DeskDashboardPage.vue — Chiamate Axios Mantenute Intenzionalmente

La pagina POS (Segreteria) mantiene **6 chiamate Axios attive** verso il backend FastAPI. Queste sono **intenzionali** e non vanno rimosse fino alla migrazione completa del motore transazionale:

| Endpoint                    | Metodo | Funzione         | Motivazione                          |
| --------------------------- | ------ | ---------------- | ------------------------------------ |
| `/calendar/daily-rides`     | GET    | `loadDayRides()` | Radar turni con prezzo attività      |
| `/calendar/activities`      | GET    | `loadDayRides()` | Arricchimento `_unit_price`          |
| `/orders/by-ride/{id}`      | GET    | `loadOrders()`   | Lista ordini con transazioni         |
| `/orders/desk`              | POST   | `submitOrder()`  | Creazione ordine POS completa        |
| `/orders/{id}`              | PATCH  | `updateOrder()`  | Drop-outs (best-effort)              |
| `/orders/{id}/transactions` | POST   | `addPayment()`   | Registrazione pagamenti multi-metodo |

### 4.3 Altre Dipendenze Axios Residue (Non-Calendario)

| File                          | Import | Uso                                                                   |
| ----------------------------- | ------ | --------------------------------------------------------------------- |
| `resource-store.js`           | `api`  | Staff CRUD, Fleet CRUD, Settings, Activity Rules, Resource Exceptions |
| `RideDialog.vue`              | `api`  | `tesseraSelezionati()` → `POST /firaft/register-bulk`                 |
| `SeasonConfigDialog.vue`      | `api`  | CRUD attività e configurazione stagionale                             |
| `ScannerPage.vue`             | `api`  | OCR Azure e processing documenti                                      |
| `RegistrationPage.vue`        | `api`  | Registrazione legacy                                                  |
| `registration-store.js`       | `api`  | Store registrazioni legacy                                            |
| `StepReview.vue`              | `api`  | PDF generation backend                                                |
| `admin/RegistrationsPage.vue` | `api`  | Lista registrazioni admin                                             |

---

## 5. MAPPA DIPENDENZE CRITICA

### Frontend — Albero Componenti

```
src/
├── boot/
│   └── axios.js                    # Axios instance → FastAPI
├── composables/
│   └── useCheckin.js               # 🆕 DRY: Magic Link, QR, WhatsApp
├── components/
│   ├── BookingDialog.vue           # 🆕 Estratto: form prenotazione
│   ├── CalendarComponent.vue       # Vista mese interattiva
│   ├── CameraCapture.vue           # Cattura foto documento
│   ├── FiraftDialog.vue            # 🆕 Estratto: tesseramento FIRAFT
│   ├── ModuleCard.vue              # Card generica
│   ├── QrDialog.vue                # 🆕 Estratto: modale QR riutilizzabile
│   ├── ResourcePanel.vue           # 🆕 Estratto: assegnazione risorse
│   ├── RideDialog.vue              # 🆕 Estratto: dettaglio turno completo
│   ├── SeasonConfigDialog.vue      # Configurazione stagione
│   └── scanner/                    # Kiosk check-in (4 step)
│       └── steps/
│           └── StepReview.vue      # Submission Supabase
├── pages/
│   ├── PlanningPage.vue            # 🔧 Purificato: orchestratore puro (350 righe)
│   ├── DeskDashboardPage.vue       # POS Segreteria (Axios-based, intenzionale)
│   ├── ResourcesPage.vue           # Gestione staff/fleet
│   ├── ScannerPage.vue             # OCR documenti
│   ├── LoginPage.vue               # Auth Supabase
│   ├── RegistrationPage.vue        # Form registrazione legacy
│   ├── admin/
│   │   └── RegistrationsPage.vue   # Lista registrazioni
│   └── public/
│       └── ConsentFormPage.vue     # Consenso pubblico (Kiosk)
├── stores/
│   ├── resource-store.js           # 🔧 Purificato: nomenclatura standard BaaS
│   ├── auth-store.js               # Autenticazione
│   └── registration-store.js       # Registrazioni (Axios legacy)
└── services/
    └── VisionService.js            # OCR Azure
```

### Backend Python — Struttura

```
backend/
├── passenger_wsgi.py               # ✅ WSGI wrapper (a2wsgi) per Ergonet
├── main.py                         # FastAPI app con CORS
├── init_db.py                      # Seeding DB SQLite + attività
├── requirements.txt                # Dipendenze Python
├── app/
│   ├── routers/                    # Endpoint API
│   ├── services/                   # Business logic
│   ├── models/                     # SQLAlchemy models
│   └── schemas/                    # Pydantic schemas
└── tools/                          # Script utilità
```

---

## 6. KNOWN ISSUES & TECH DEBT

### 6.1 Issue RISOLTI (Storico — Chiusi)

| #   | Issue                                                                           | Status     | Commit                                   |
| --- | ------------------------------------------------------------------------------- | ---------- | ---------------------------------------- |
| 1   | God Object `PlanningPage.vue` (1800+ righe)                                     | ✅ RISOLTO | Smantellato in 5 componenti + composable |
| 2   | Duplicazione logica Check-in (Magic Link/QR/WA) in 3 file                       | ✅ RISOLTO | Centralizzato in `useCheckin.js`         |
| 3   | Nomenclatura store con suffissi `Supabase` / `ToSupabase`                       | ✅ RISOLTO | Rinominate in nomenclatura standard      |
| 4   | Import `api` (Axios) in PlanningPage.vue                                        | ✅ RISOLTO | Eliminato completamente                  |
| 5   | Dialog inline nel monolite (Ride, FIRAFT, Booking, Resources, QR, Partecipanti) | ✅ RISOLTO | Estratti in SFC dedicati                 |
| 6   | Ghost Slots non generati dopo refactoring                                       | ✅ RISOLTO | Logica ghost ripristinata in store       |

### 6.2 Tech Debt Accettato Temporaneamente

| #        | Debt                                                                                                                                                                                                                                                          | Severità | Piano                                                          |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | -------------------------------------------------------------- |
| **TD-1** | **Ridondanza form prenotazione:** `BookingDialog.vue` e il tab "Nuova Prenotazione" di `DeskDashboardPage.vue` hanno logica sovrapposta (~60%) ma backend diverso (Supabase vs Axios/FastAPI). Non unificabili senza migrare il motore transazionale del POS. | 🟡 Media | Unificare quando il POS migra a Supabase                       |
| **TD-2** | **Chiamate Axios legacy nel POS:** 6 endpoint FastAPI attivi in `DeskDashboardPage.vue` per il ciclo ordine-pagamento. Necessari finché il backend transazionale non è replicato in Supabase.                                                                 | 🟡 Media | Migrare progressivamente a Supabase RPC/Edge Functions         |
| **TD-3** | **`RideDialog.vue` mantiene `import { api }`** per la singola chiamata `tesseraSelezionati()` → `POST /firaft/register-bulk`.                                                                                                                                 | 🟢 Bassa | Migrare quando il motore FIRAFT diventa Supabase Edge Function |
| **TD-4** | **`registration-store.js` integralmente Axios:** Store dedicato alle registrazioni legacy, non ancora migrato a Supabase.                                                                                                                                     | 🟢 Bassa | Migrazione pianificata post-stabilizzazione                    |

### 6.3 Vincoli Infrastrutturali (Invarianti)

- **RAM ≤ 1GB** (Ergonet CloudLinux LVE) → Modelli AI con lazy loading obbligatorio
- **No `uvicorn` diretto** → Solo `passenger_wsgi.py` + `a2wsgi`
- **No storage immagini documenti** in chiaro (GDPR) → Solo `audit.json` append-only
- **`gc.collect()`** dopo ogni inferenza pesante

---

> **Prossime priorità operative:**
>
> 1. 🔴 Stampa Fiscale / Ricevute POS
> 2. 🟡 Migrazione motore transazionale DeskDashboard da Axios a Supabase
> 3. 🟢 Unificazione form prenotazione (BookingDialog ↔ DeskDashboard)
