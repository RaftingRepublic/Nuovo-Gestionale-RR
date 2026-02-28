# SYSTEM SNAPSHOT REPORT — Sessione 28/02/2026 01:23

## Generato per: Tech Lead Rafting Republic
## Generato da: Operaio AI — Chiusura Fase 10.A-D
## Timestamp: 28 Febbraio 2026, ore 01:23 CET

---

## 1. STATO DEL CANTIERE

**Fase Attiva:** Fase 10 — Il Mangiasoldi (Cassa & CRM)
**Stato:** IN CORSO (Sottofasi 10.A → 10.D completate)
**Backend:** Uvicorn stabile dopo hotfix availability.py
**Frontend:** Quasar dev server attivo, CassaPage operativa

---

## 2. LAVORO COMPLETATO IN QUESTA SESSIONE

### 2.1 Inceneritore Debito Tecnico

| File Eliminato | Motivo | Effetto Collaterale | Fix |
|---|---|---|---|
| reservations.py | Router zombi, mai usato | Import orfano in main.py | Rimosso import + include_router |
| yield_engine.py | Servizio morto, mai referenziato | availability.py lo importava | Router availability decablato da main.py |
| availability.py | Guscio vuoto del defunto yield_engine | ImportError crashava Uvicorn | Import + include_router commentati |

### 2.2 CassaPage.vue — Cruscotto Finanziario

| Componente | Descrizione |
|---|---|
| I Tre Cassetti | 3 card fisse (CASH bg-teal-1, POS bg-blue-1, TRANSFER bg-orange-1). Computed totaliMetodo con chiavi fisse, sempre visibili anche a zero |
| Tabella Transazioni | q-table ordinata per data decrescente. Colonne: Data, Tipo, Metodo, Importo, Note |
| Tabella Anagrafica | q-table clienti (full_name, email, phone, created_at) con filtro locale reattivo (q-input search) |
| Fascicolo Cliente | Dialog laterale (position right, maximized, 600px). Query relazionale: orders + rides(ride_date, ride_time) + transactions(*) |
| Semaforo Debiti | q-badge per ordine: rosso "DEBITO: euro X" se price_total - price_paid > 0, verde "SALDATO" altrimenti |
| Leva dello Strozzino | Bottone "Incassa Saldo" accanto al badge DEBITO. Modale con importo precompilato + select metodo. Dual-Query: INSERT transactions + UPDATE orders.price_paid |
| Spia Check Engine | Error handling rumoroso: console.error + alert() su errori Supabase e eccezioni generiche |

### 2.3 Cablaggio Infrastrutturale

| File Modificato | Modifica |
|---|---|
| backend/main.py | Rimossi import reservations e availability. Commentati include_router corrispondenti |
| TECH_ARCHITECTURE.md | Rimosso riferimento fossile OrderDB in Sez. 6. Aggiunta nota Dogma 12 in Sez. 8 |
| web-app/src/router/routes.js | Aggiunta rotta path: 'cassa' dentro children di /admin |
| web-app/src/layouts/MainLayout.vue | Aggiunto q-item "Cassa & CRM" con icona point_of_sale nella sezione Amministrazione |
| PROJECT_RADAR.md | Fase 10 come cantiere aperto. BUG 1-4 spuntati. Sottofasi 10.A-D documentate |
| LORE_VAULT.md | Dogma 18 (La Graffettatrice) sancito. Sigillo Fase 10.A-D |

---

## 3. ARCHITETTURA DATABASE ATTUALE

### 3.1 SQLite Locale (rafting.db) — Catalogo Deterministico

| Tabella | Ruolo | Modello ORM |
|---|---|---|
| activities | Catalogo attivita + workflow_schema JSON BPMN | ActivityDB |
| daily_rides | Turni materializzati + status semaforo + is_overridden | DailyRideDB |
| staff | Anagrafica guide/autisti, contratti, brevetti | StaffDB |
| fleet | Mezzi: RAFT, VAN (has_tow_hitch), TRAILER | FleetDB |
| system_settings | Variabili globali EAV (raft_capacity, van_seats) | SystemSettingDB |
| activity_sub_periods | Override stagionali (yellow_threshold, etc.) | ActivitySubPeriodDB |
| resource_exceptions | Ferie, manutenzioni, disponibilita extra | ResourceExceptionDB |
| registrations | Slot consenso Check-in (Auto-Slotting Pac-Man) | RegistrationDB |

Tabelle AMPUTATE: orders (DROPpata Fase 9.A), transactions, customers (DROPpate Fase 8)

### 3.2 Supabase Cloud (PostgreSQL) — Dati Caldi Transazionali

| Tabella | Colonne Chiave | FK/Relazioni |
|---|---|---|
| rides | id (UUID), activity_id, date, time, status | Dual-Write con daily_rides (stesso UUID) |
| orders | id, ride_id, customer_id, pax, price_total, price_paid, booker_name/phone/email | ride_id -> rides.id, customer_id -> customers.id |
| transactions | id, order_id, amount, method, type, note | order_id -> orders.id ON DELETE CASCADE |
| registrations | id, order_id, daily_ride_id, nome, cognome, status, firaft_status | order_id -> orders.id |
| customers | id, full_name, email, phone, created_at | Anagrafica CRM cloud |
| ride_allocations | id, ride_id, resource_type, resource_id, metadata (JSONB) | ride_id -> rides.id. resource_id e chiave LOGICA (no FK fisica - Dogma 12) |
| resources | id, name, type | Bridge UUID per ride_allocations |

### 3.3 Regola Dual-Write (Perno Anti-Split-Brain)

I turni (rides/daily_rides) esistono in ENTRAMBI i DB con lo STESSO UUID.
Qualsiasi operazione che crea o modifica un turno DEVE scrivere su entrambi.

---

## 4. ROUTER BACKEND ATTIVI (main.py)

| # | Prefisso | Modulo | Stato |
|---|---|---|---|
| 1 | /api/v1/vision | vision.py | Attivo (Azure OCR) |
| 2 | /api/v1 | registration.py | Attivo |
| 3 | /api/v1/resources | resources.py | Attivo (try/except) |
| 4 | /api/v1/reservations | reservations.py | INCENERITO Fase 10 |
| 5 | /api/v1/calendar | calendar.py | Attivo (BFF + Engine) |
| 6 | /api/v1/legacy-orders | orders.py | INCENERITO Fase 8 |
| 7 | /api/v1/firaft | firaft.py | Attivo |
| 8 | /api/v1/logistics | logistics.py | Attivo |
| 9 | /api/v1/orders | desk.py | Attivo (POS Ibrido) |
| 10 | /api/v1/public | public.py | Attivo (Kiosk NO Auth) |
| 11 | /api/v1/availability | availability.py | DECABLATO Fase 10 (guscio vuoto) |
| 12 | /api/v1/crew | crew.py | Attivo (Crew Builder) |

---

## 5. PAGINE FRONTEND ATTIVE

| Rotta | Pagina | Funzione |
|---|---|---|
| /login | LoginPage.vue | Autenticazione |
| /consenso | ConsentFormPage.vue | Kiosk Check-in Pubblico |
| /admin/operativo | PlanningPage.vue | Calendario Operativo (Hub) |
| /admin/timeline | TimelinePage.vue | Gantt Flussi + Ruoli |
| /admin/board | DailyBoardPage.vue | Lavagna Operativa |
| /admin/registrazioni | RegistrationsPage.vue | Archivio Consensi |
| /admin/scanner | ScannerPage.vue | Nuova Registrazione |
| /admin/risorse | ResourcesPage.vue | CRUD Staff & Fleet |
| /admin/impostazioni | SettingsPage.vue | Costruttore Flussi BPMN |
| /admin/cassa | CassaPage.vue | **NUOVO** — Cassa & CRM |

---

## 6. DOGMI ATTIVI (LORE_VAULT)

| # | Nome | Sintesi |
|---|---|---|
| 10 | Tetris Umano | Passeggeri come frazioni di ordini nominali, mai numeri anonimi |
| 11 | Swap & Replace | Aggiornamento massivo = DELETE + bulk INSERT |
| 12 | Chiavi Logiche Cross-DB | No FK fisiche tra SQLite e Supabase. UUID liberi |
| 13 | Kill-Switch Varo | UI inibisce salvataggio se overflow o sovra-assegnazione |
| 14 | Walkie-Talkie HTTPX | OrderDB amputata. Transazioni solo via httpx/supabase_bridge |
| 15 | Mascheramento Nimitz | Capacita >= 1000 nasconde denominatore nel frontend |
| 16 | Sindrome UUID | str(ride.id) obbligatorio prima di accedere a dict esterni |
| 17 | Divieto httpx sincrono | Mai httpx.Client() nel thread async FastAPI |
| 18 | La Graffettatrice | customer_id obbligatorio prima di INSERT ordine su Supabase |

---

## 7. BUG PENDENTI E NEXT STEPS

### 7.1 BUG CRITICO (Segnalato dal Tech Lead)

**desk.py (POS) genera ordini orfani omettendo il customer_id nel payload verso Supabase e perde email/telefono del cliente.**

NOTA OPERAIO post-ispezione: Il codice di desk.py (righe 114-167) risulta GIA correttamente cablato:
- Riga 124-133: CRM Silente con UPSERT cliente (full_name, email, phone) e header Prefer return=representation
- Riga 133: customer_id estratto dalla risposta Supabase
- Riga 167: customer_id iniettato nel payload ordine

Il bug potrebbe manifestarsi in casi edge:
- Il form POS non invia booker_name/email/phone (tutti vuoti)
- La condizione riga 124 salta se nessun dato referente presente
- Il customer non viene creato e customer_id resta None

AZIONE CONSIGLIATA: Test E2E con ordine completo (nome + email + telefono) per verificare se il customer_id compare effettivamente nell'ordine su Supabase. Se il bug persiste, il problema e nel frontend (DeskBookingForm non passa i dati) o nelle RLS Supabase.

### 7.2 Next Steps Fase 10

1. Collaudo E2E CassaPage: creare ordine POS, verificare che appaia in Libro Mastro e nel Fascicolo Cliente
2. Test incasso: usare la Leva dello Strozzino su un ordine con debito, verificare update price_paid
3. Reportistica avanzata: dashboard incassi giornalieri, filtri per data
4. Storico ordini per cliente: cronologia completa con export

---

## 8. COMANDI GIT PER IL PM

Eseguire nell'ordine, dalla root del progetto:

git add -A

git commit -m "Fase 10.A-D: Il Mangiasoldi - CassaPage + Inceneritore Debito Tecnico + Dogma 18

- INCENERITORE: reservations.py, yield_engine.py eliminati fisicamente. availability.py decablato.
- CASSA: CassaPage.vue con Supabase JS diretto (3 cassetti CASH/POS/TRANSFER, Anagrafica con drill-down).
- FASCICOLO: Dialog laterale con query relazionale orders+rides+transactions. Semaforo debiti.
- STROZZINO: Bottone Incassa Saldo con Dual-Query (INSERT tx + UPDATE order.price_paid).
- CHECK ENGINE: Error handling rumoroso nel fascicolo cliente.
- ROUTING: Rotta /admin/cassa + voce menu laterale point_of_sale.
- DOCS: TECH_ARCHITECTURE (OrderDB amputata Sez.8), LORE_VAULT (Dogma 18), PROJECT_RADAR (Fase 10 in corso)."

git push
