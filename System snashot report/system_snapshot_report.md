SYSTEM SNAPSHOT REPORT — Chiusura Cantiere Cassa

Data: 28/02/2026 02:10 CET
Fase: 10 (Il Mangiasoldi — Cassa & CRM) — STABILE
Sessione: Operazione Acchiappafantasmi + Cura Allucinazioni + Graffettatrice
Autore: Operaio AI (sotto direttiva Architetto)

---

SEZIONE 1 — STATO DEL SISTEMA

1.1 Architettura Ibrida (Invariata)

- SQLite Locale (rafting.db): Catalogo deterministico (activities, daily_rides, staff, fleet, system_settings, registrations)
- Supabase Cloud (PostgreSQL): Dati caldi transazionali (rides, orders, transactions, customers, registrations, ride_allocations)
- Dual-Write: I turni (rides/daily_rides) esistono in ENTRAMBI i DB con lo STESSO UUID
- Comunicazione Backend-Cloud: httpx (sincrono in endpoint def, asincrono in endpoint async def)
- Comunicazione Frontend-Cloud: Supabase JS Client diretto (CassaPage) + Axios verso FastAPI (resto dell'app)

1.2 Stack Tecnologico

Frontend: Vue 3 (Composition API) + Quasar v2.18.6 + Pinia + Vite
Backend: FastAPI + SQLAlchemy (solo catalogo) + httpx (Supabase)
DB Locale: SQLite (rafting.db)
DB Cloud: Supabase (PostgreSQL via PostgREST)
AI: Azure OCR (REST API cloud — zero RAM locale)
Deploy: Ergonet CloudLinux (1GB RAM limit) + Apache + Passenger

1.3 Moduli Operativi Attivi

| Modulo | File Principale | Stato |
|--------|----------------|-------|
| Calendario Operativo | PlanningPage.vue | STABILE |
| Omni-Board (Modale Turno) | RideDialog.vue | STABILE |
| POS Desk (Prenotazioni) | DeskBookingForm.vue | STABILE |
| Crew Builder (Equipaggi) | CrewBuilderPanel.vue | STABILE |
| Cassa & CRM | CassaPage.vue | STABILE |
| Timeline Flussi | TimelinePage.vue | STABILE |
| Costruttore Flussi BPMN | SettingsPage.vue | STABILE |
| Staff & Risorse | ResourcesPage.vue | STABILE |
| Kiosk Check-in | ConsentFormPage.vue | STABILE |
| Motore Predittivo | availability_engine.py | STABILE |

---

SEZIONE 2 — BUG RISOLTI IN QUESTA SESSIONE

2.1 BUG CRITICO 7.1 — Ordini Orfani senza customer_id (RISOLTO)

Sintomo: Il POS desk (desk.py) poteva generare ordini in Supabase senza customer_id, rendendo impossibile il tracciamento CRM.

Causa radice (Backend): Il blocco CRM (righe 113-134) era condizionale. L'UPSERT customers avveniva solo se il payload conteneva email O telefono (riga 115) E almeno un dato anagrafico (riga 124). Se il frontend inviava tutto vuoto, customer_id restava None e l'ordine veniva scritto orfano.

Causa radice (Frontend): Il campo booker_name aveva l'asterisco visivo ma nessuna validazione Quasar (rules). Il bottone CONFERMA aveva un :disable debole che non intercettava stringhe di soli spazi.

Fix applicati:

FRONTEND (DeskBookingForm.vue):
- Riga 11-18: Aggiunto ref="bookerNameRef", lazy-rules, :rules con trim + obbligatorieta
- Riga 173: Bottone CONFERMA con :disable rafforzato (intercetta trim vuoto)
- Riga 195: Ref bookerNameRef per validazione programmatica
- Riga 261-267: submitOrder con triplo guard (nullita + trim + hasError Quasar)

BACKEND (desk.py):
- Riga 113-115: Fallback difensivo — se booker_name vuoto, forza a "Cliente Walk-in"
- Riga 129-130: Bypass condizionale RIMOSSO — CRM crea SEMPRE un record cliente
- Riga 139-143: Parsing risposta robusto (gestisce sia list che dict da Prefer: return=representation)
- Riga 145-151: Kill-Switch Dogma 18 — HTTPException 400 se customer_id ancora None

2.2 Errore Supabase 42703 — Colonne Inesistenti in CassaPage (RISOLTO)

Sintomo: Due query Supabase in CassaPage.vue fallivano con errore 42703 (column does not exist).

Causa 1 (Fascicolo Cliente): La select relazionale usava rides(ride_date, ride_time) ma la tabella rides in Supabase ha colonne date e time.

Causa 2 (Libro Mastro): .order('created_at') sulla tabella transactions, ma la colonna created_at non esiste in quella tabella.

Fix applicati (CassaPage.vue):
- Riga 286: select corretto a rides(date, time)
- Riga 138: Template corretto a ordine.rides.date / ordine.rides.time
- Riga 163: Template pagamenti: tx.type al posto di formatDate(tx.created_at)
- Riga 222-227: txColumns: rimossa colonna created_at, corretto notes in note
- Riga 354: fetchTransactions: .order('id', { ascending: false })

2.3 Violazione NOT NULL su transactions.id (RISOLTO)

Sintomo: L'INSERT diretto dalla CassaPage (Leva dello Strozzino) verso la tabella transactions in Supabase falliva per violazione del vincolo NOT NULL sulla colonna id.

Causa: Il payload non includeva la Primary Key. Il backend Python genera le PK con uuid.uuid4(), ma il codice Vue.js nel fronte non generava alcun ID.

Fix applicati (CassaPage.vue):
- Riga 195: Importato { uid } from 'quasar'
- Riga 318: Aggiunto id: uid() nel payload INSERT transactions

---

SEZIONE 3 — STRUTTURA DATABASE (Stato Corrente)

3.1 SQLite Locale (rafting.db) — Catalogo

Tabella: activities
- id (TEXT PK), name, description, activity_type, price, duration, manager
- default_times (JSON), workflow_schema (JSON con logistics BPMN)
- is_active, created_at, updated_at

Tabella: daily_rides
- id (TEXT PK UUID), activity_id (FK activities), ride_date, ride_time
- status (A/B/C/D/X), is_overridden (BOOLEAN), booked_pax, note

Tabella: staff
- id (TEXT PK), name, role, license_type, has_first_aid, contract_type
- contract_start, contract_end, is_active

Tabella: fleet
- id (TEXT PK), name, fleet_type (RAFT/VAN/TRAILER), capacity
- has_tow_hitch, plate, is_active

Tabella: system_settings (EAV)
- key (TEXT PK), value (TEXT), description

Tabella: registrations (slot check-in locale)
- id (TEXT PK), order_id (TEXT — UUID orfano Supabase), daily_ride_id (FK)
- nome, cognome, email, telefono, status (EMPTY/COMPLETED)
- is_lead, locked, firaft_status

3.2 Supabase Cloud (PostgreSQL) — Transazioni

Tabella: rides
- id (UUID PK — STESSO UUID di daily_rides), activity_id (TEXT)
- date (DATE), time (TIME), status (TEXT)
- Nessun created_at

Tabella: orders
- id (UUID PK), ride_id (FK rides ON DELETE CASCADE)
- customer_id (FK customers), pax (INT), price_total, price_paid
- adjustments, extras (JSONB), source, notes, order_status
- booker_name, booker_phone, booker_email
- customer_name, customer_phone, customer_email
- created_at (TIMESTAMPTZ)

Tabella: transactions
- id (TEXT PK — NON auto-generato, obbligatorio nel payload)
- order_id (FK orders ON DELETE CASCADE)
- amount (NUMERIC), method (TEXT), type (TEXT), note (TEXT)
- Nessun created_at

Tabella: customers
- id (UUID PK), full_name (TEXT), email (TEXT), phone (TEXT)
- created_at (TIMESTAMPTZ)

Tabella: registrations (cloud)
- id (TEXT PK composito order_id-slot-N)
- order_id (FK orders), daily_ride_id (TEXT)
- nome, cognome, email, telefono, is_lead, status, locked, firaft_status

Tabella: ride_allocations
- id (UUID PK), ride_id (FK rides), resource_id (TEXT — chiave logica, NO FK fisica)
- resource_type (TEXT), metadata (JSONB con groups[] per Tetris Umano)

3.3 Chiavi Cross-Database (Dogma 12)

Le entita SQLite (staff, fleet) sono referenziate in Supabase tramite UUID stringa SENZA vincoli FK fisici. La validazione e LOGICA (livello applicativo). La FK ride_allocations_resource_id_fkey e stata amputata il 27/02/2026.

---

SEZIONE 4 — DOGMI VIGENTI (18 + Corollari)

| N. | Nome | Regola |
|----|------|--------|
| 1 | Hard Limit LVE | Max 1GB RAM. Lazy loading modelli AI. passenger_wsgi. |
| 2 | Architettura Ibrida | SQLite = catalogo, Supabase = transazioni. |
| 3 | DDL Supabase | NOTIFY pgrst obbligatorio dopo ogni ALTER TABLE. |
| 4 | Override | is_overridden=True blocca ricalcolo Engine. |
| 5-9 | (Business rules) | Time-Array Slicer, BPMN, Sarre, Safety Kayak, River Ledger. |
| 10 | Tetris Umano | Passeggeri nominali per ordine, mai anonimi. |
| 11 | Swap & Replace | DELETE + bulk INSERT per update massivi crew. |
| 12 | Chiavi Logiche | No FK fisiche cross-database + Corollario Arto Fantasma. |
| 13 | Kill-Switch Varo | Blocco UI se overflow o sovra-assegnazione. |
| 14 | Walkie-Talkie HTTPX | OrderDB amputata, supabase_bridge.py centralizzato. |
| 15 | Mascheramento Nimitz | Capacity >= 1000 nasconde denominatore UI. |
| 16 | Sindrome UUID | str(ride.id) prima di dict.get() cross-DB. |
| 17 | Divieto httpx sincrono | Mai httpx.Client in endpoint async def. |
| 18 | La Graffettatrice | customer_id OBBLIGATORIO + Corollario uid() Vue.js. |

---

SEZIONE 5 — FASI COMPLETATE (Cronologia)

| Fase | Nome | Data | Stato |
|------|------|------|-------|
| 5 | Motore BPMN e Yield Engine V5 | Pre-24/02 | SIGILLATA |
| 6 | Logistica Fluidodinamica e POS Ibrido | 24-27/02 | SIGILLATA |
| 7 | Crew Builder — Lavagna d'Imbarco | 27/02 | SIGILLATA |
| 8 | Smaltimento Debito Tecnico | 27/02 | SIGILLATA |
| 9 | Migrazione OrderDB a Supabase | 27-28/02 | SIGILLATA |
| 10 | Il Mangiasoldi — Cassa & CRM | 28/02 | STABILE |

---

SEZIONE 6 — FILE CHIAVE MODIFICATI IN QUESTA SESSIONE

| File | Tipo | Intervento |
|------|------|-----------|
| DeskBookingForm.vue | Frontend | Rules Quasar + validazione ref + guard submit |
| desk.py (backend) | Backend | Fallback Walk-in + CRM obbligatorio + Kill-Switch D18 |
| CassaPage.vue | Frontend | Fix colonne rides + rimosso created_at + uid() |
| LORE_VAULT.md | Doc | Corollario Dogma 18 (Graffettatrice del Cassiere) |
| PROJECT_RADAR.md | Doc | BUG 7.1 RISOLTO, 3 fix documentati, Fase 10 STABILE |

---

SEZIONE 7 — PROSSIMI PASSI (Backlog Fase 10+)

1. Reportistica avanzata (dashboard incassi giornalieri, filtri per data/attivita)
2. Storico ordini per cliente (timeline CRM nel fascicolo)
3. Dashboard incassi giornalieri aggregati (grafici per metodo pagamento)
4. Opzione B: Modulo Presenze Giornaliere Staff

---

SEZIONE 8 — COMANDI GIT (Per il PM)

git add -A
git commit -m "FASE 10.fix: Operazione Acchiappafantasmi - Blindatura anti-ordini orfani (Dogma 18) + Cura allucinazioni schema CassaPage (42703) + Graffettatrice uid() Vue.js. BUG CRITICO 7.1 RISOLTO. Fase 10 STABILE."
git push origin main

---

FINE REPORT — Sistema stabile. Pronto per la prossima sessione operativa.
