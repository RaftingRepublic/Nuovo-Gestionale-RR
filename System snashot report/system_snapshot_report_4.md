# SYSTEM SNAPSHOT REPORT — CHIUSURA SESSIONE

Data: 28/02/2026 00:15 CET
Sessione: Fase 9 SIGILLATA (Amputazione OrderDB + Cablaggio HTTPX + Hotfix Matematici)
Autore: Agente IA Locale (Operaio)
Destinatario: Tech Lead (CTO)
Stato Generale: OPERATIVO — Backend FastAPI + Frontend Quasar avviati, zero crash

---

## 1. STATO SISTEMA CRISTALLIZZATO

L'architettura ibrida e' ora definitiva:

    SQLite (locale)  = Catalogo deterministico + Motore Predittivo
    Supabase (cloud) = Dati transazionali (ordini, pagamenti, clienti, allocazioni)
    Ponte            = supabase_bridge.py (httpx.AsyncClient) + Sync Sonda (_fetch_supabase_pax)

La classe OrderDB (SQLAlchemy) NON ESISTE PIU'. La tabella orders e' stata
DROPpata da rafting.db. Il campo RegistrationDB.order_id e' una stringa orfana
(UUID di Supabase, senza FK fisico). L'integrita' referenziale e' LOGICA.


## 2. INVENTARIO BACKEND (13 Router, 10 Servizi)

### 2.1 Modelli SQLAlchemy Attivi (app/models/)

    Modello              Tabella              Stato
    ActivityDB           activities           ATTIVO — Catalogo BPMN + workflow_schema JSON
    SubPeriodDB          activity_sub_periods ATTIVO — Override stagionali (yellow_threshold)
    DailyRideDB          daily_rides          ATTIVO — Turni materializzati + status + is_overridden
    StaffDB              staff                ATTIVO — Anagrafica guide/autisti/contratti
    FleetDB              fleet                ATTIVO — Mezzi RAFT/VAN/TRAILER + capacity + has_tow_hitch
    SystemSettingsDB     system_settings      ATTIVO — Variabili EAV (raft_capacity, van_seats)
    ResourceExceptionDB  resource_exceptions  ATTIVO — Ferie, manutenzioni, eccezioni
    RegistrationDB       registrations        ATTIVO — Slot check-in (order_id = UUID stringa orfana)

    ELIMINATI: OrderDB (Fase 9.A), CustomerDB (Fase 8), TransactionDB (Fase 8),
               CrewAssignmentDB (Fase 8), ride_staff_link (Fase 8), ride_fleet_link (Fase 8)

### 2.2 Router FastAPI

    File               Prefisso               Tipo          Note
    calendar.py        /api/v1/calendar       ATTIVO sync   Endpoint principali (list, detail, close, override)
    desk.py            /api/v1/orders         ATTIVO sync   POS Dual-Write (httpx -> Supabase + SQLAlchemy -> SQLite)
    public.py          /api/v1/public         ATTIVO async  Kiosk check-in (supabase_bridge)
    crew.py            /api/v1/crew           ATTIVO async  Crew Builder (ride_allocations JSONB)
    availability.py    /api/v1/availability   ATTIVO sync   Engine per singola attivita'
    registration.py    /api/v1/calendar       ATTIVO sync   CRUD registrazioni locali
    firaft.py          /api/v1/firaft         ATTIVO sync   Tesseramento bulk
    logistics.py       /api/v1/logistics      ATTIVO sync   Staff/Fleet read-only
    resources.py       /api/v1/resources      ATTIVO sync   Staff/Fleet CRUD completo
    vision.py          /api/v1/vision         ATTIVO sync   Azure OCR (zero RAM locale)
    waivers.py         /api/v1/waivers        ATTIVO sync   PDF manleve (reportlab)
    reservations.py    /api/v1/reservations   FOSSILE       Non critico, ancora montato

### 2.3 Servizi (app/services/)

    File                        Stato    Note
    availability_engine.py      ATTIVO   Motore Predittivo 2-Pass (Time-Array Slicer 1440 min)
    supabase_bridge.py          ATTIVO   Modulo radio HTTPX (3 funzioni async difensive)
    ride_helpers.py              ATTIVO   Fallback puro (return 0), NESSUNA chiamata di rete
    azure_document_service.py   ATTIVO   Azure OCR cloud provider
    waiver_service.py           ATTIVO   Generazione PDF (reportlab)
    waiver_mailer.py            ATTIVO   Invio email manleve
    image_utils.py              ATTIVO   Utility immagini
    document_specs.py           ATTIVO   Spec documenti identita'
    yield_engine.py             FOSSILE  Sostituito da availability_engine (Fase 5)


## 3. INVENTARIO FRONTEND

### 3.1 Pagine (src/pages/)

    Pagina               Rotta                 Stato
    PlanningPage.vue     /admin/operativo      ATTIVO — Hub operativo (Omni-Board)
    ResourcesPage.vue    /admin/resources      ATTIVO — CRUD Staff/Fleet (SALVACONDOTTO)
    LoginPage.vue        /login                ATTIVO — Autenticazione Supabase
    RegistrationPage.vue /admin/registrations  ATTIVO — Lista registrazioni check-in
    ScannerPage.vue      /admin/scanner        ATTIVO — Scanner AI documenti (Azure OCR)
    IndexPage.vue        /                     ATTIVO — Landing
    ErrorNotFound.vue    /*                    ATTIVO — 404

    PAGINE CON MASCHERAMENTO NIMITZ: PlanningPage.vue, RideDialog.vue

### 3.2 Componenti Critici

    Componente              Ruolo                             Blindature Attive
    RideDialog.vue          Omni-Board (hub modale a tab)     Nimitz + Posti Residui deterministici
    PlanningPage.vue        Calendario Operativo              Nimitz + getRemainingSeats() deterministico
    DeskBookingForm.vue     Form POS (tab Nuova Prenotazione) Nessuna modifica recente
    CrewBuilderPanel.vue    Crew Builder (tab Equipaggi)      Kill-Switch Varo + Sensori Galleggiamento
    CalendarComponent.vue   Calendario mensile mattoncini     Epurato UUID (Fase 8)

### 3.3 Store Pinia

    Store               Ruolo
    resource-store.js   State centralizzato (Hydration Node, Merge Difensivo, Kill-Switch Client)
    crew-store.js       Equipaggi (Busta Stagna JSONB, Swap and Replace)


## 4. MAPPA DATABASE

### 4.1 SQLite Locale (rafting.db) — 8 Tabelle Attive

    activities             Catalogo + workflow_schema JSON (BPMN, logistics)
    activity_sub_periods   Override stagionali per attivita'
    daily_rides            Turni materializzati (status A/B/C/D/X, is_overridden)
    staff                  Guide, autisti, brevetti, contratti mensili
    fleet                  RAFT (capacity), VAN (has_tow_hitch), TRAILER
    system_settings        EAV (raft_capacity, van_seats, overbooking_limit)
    resource_exceptions    Ferie, manutenzioni, disponibilita' extra (per data)
    registrations          Slot consenso check-in (order_id = UUID stringa Supabase)

### 4.2 SQLite — 6 Tabelle DROPpate

    orders                 DROPpata Fase 9.A (classe OrderDB eliminata fisicamente)
    transactions           DROPpata Fase 8 DT-5
    customers              DROPpata Fase 8 DT-5
    crew_assignments       DROPpata Fase 8 DT-3
    ride_staff_link        DROPpata Fase 8 DT-3
    ride_fleet_link        DROPpata Fase 8 DT-3

### 4.3 Supabase Cloud (PostgreSQL, Francoforte) — 6 Tabelle

    rides                  Turni operativi (UUID condiviso con daily_rides, FK per orders)
    orders                 Ordini clienti (pax, price_total, price_paid, ride_id FK)
    transactions           Libro Mastro pagamenti (amount, method, type, order_id FK)
    registrations          Partecipanti cloud (consensi, FIRAFT, dati anagrafici)
    customers              Anagrafica CRM cloud (nome, email, telefono)
    ride_allocations       Crew Builder (metadata JSONB, resource_type=crew_manifest)

### 4.4 Relazioni Cross-Database (Tutte LOGICHE, mai FK fisiche — Dogma 12)

    SQLite daily_rides.id       <==>  Supabase rides.id          DUAL-WRITE (stesso UUID)
    SQLite registrations.order_id --->  Supabase orders.id       UUID stringa orfana
    Supabase ride_allocations.resource_id ---> SQLite staff.id   Chiave logica (Dogma 12)
    Supabase ride_allocations.resource_id ---> SQLite fleet.id   Chiave logica (Dogma 12)


## 5. DOGMI ATTIVI (Riepilogo Completo)

    #    Nome                              Data         Status
    10   Tetris Umano                      27/02/2026   Sancito — LORE_VAULT
    11   Swap and Replace                  27/02/2026   Sancito — LORE_VAULT
    12   Chiavi Logiche Cross-DB           27/02/2026   Sancito — LORE_VAULT
    13   Kill-Switch del Varo              27/02/2026   Sancito — LORE_VAULT
    14   Walkie-Talkie HTTPX               27/02/2026   Sancito — LORE_VAULT
    15   Mascheramento Nimitz              27/02/2026   Sancito — LORE_VAULT
    16   Sindrome UUID                     28/02/2026   NUOVO — LORE_VAULT
    17   Divieto httpx.Client Sincrono     28/02/2026   NUOVO — LORE_VAULT
    --   Override (is_overridden)          27/02/2026   Sancito — LORE_VAULT
    --   DDL Supabase (NOTIFY pgrst)       27/02/2026   Sancito — LORE_VAULT
    --   Corollario Arto Fantasma          27/02/2026   Sancito — LORE_VAULT
    --   Formula Furgoni Deterministica    27/02/2026   Sancito — LORE_VAULT


## 6. BUG PENDENTI E DEBITO TECNICO RESIDUO

### 6.1 Bug Noti (Nessuno Bloccante)

    BUG-1: TECH_ARCHITECTURE.md non aggiornato a Fase 9.
           Riga "da OrderDB -> DailyRideDB -> ActivityDB" obsoleta.
           Sez. 8 "Flussi dati" ancora reference OrderDB.
           Priorita: MEDIA. Da aggiornare nella prossima sessione.

    BUG-2: reservations.py router fossile ancora montato in main.py.
           Non serve piu'. Potenziale confusione.
           Priorita: BASSA.

    BUG-3: yield_engine.py servizio fossile (sostituito da availability_engine).
           Nessuno lo importa. Peso morto nel codebase.
           Priorita: BASSA.

### 6.2 Debito Tecnico Residuo

    DT-R1: Soglia NIMITZ (1000) hardcoded nel frontend.
           Per renderla configurabile: estrarla in system_settings.
           Priorita: BASSA.

    DT-R2: Sync Sonda (_fetch_supabase_pax) usa httpx.Client sincrono
           in un endpoint "def" (non "async def"). Tollerato ma non ideale.
           Migrazione a async def + httpx.AsyncClient raccomandata.
           Priorita: MEDIA (se si migra list_daily_rides ad async).

    DT-R3: L'Engine potrebbe avere residui della Sindrome UUID in
           percorsi secondari. Lo strato difensivo nel router compensa.
           Fix definitivo: convertire Engine a usare str keys internamente.
           Priorita: BASSA.


## 7. SEQUENZA EVENTI SESSIONE (27-28/02/2026)

    ORA         AZIONE                                      STATO
    22:30       Fase 9.A: Amputazione OrderDB               COMPLETATA
    23:00       Fase 9.B: supabase_bridge.py creato          COMPLETATA
    23:30       Fase 9.B: Schema Pydantic + Matrioska        COMPLETATA
    23:45       Fase 9.Fix v1: httpx sincrono ride_helpers   ERRATA (Dogma 17)
    23:50       Fase 9.Fix v1: Nimitz frontend               COMPLETATA
    23:55       Documentazione v1: RADAR + VAULT + Snapshot  COMPLETATA
    00:03       Fase 9.Fix v2: Rimosso httpx sincrono        COMPLETATA
    00:03       Fase 9.Fix v2: Strato difensivo router       COMPLETATA
    00:03       Fase 9.Fix v2: Frontend blindato determin.   COMPLETATA
    00:15       Chiusura: Dogma 16+17, RADAR+VAULT, Snap v2  COMPLETATA


## 8. PROSSIMO OBIETTIVO STRATEGICO

    Fase 10: Il Mangiasoldi (Flusso Prenotazioni CRM e Cassa)
    Obiettivo: completare il ciclo commerciale end-to-end.
    - Anagrafiche clienti (CRUD Supabase customers)
    - Storico ordini per cliente
    - Reportistica pagamenti
    - Dashboard incassi giornalieri
    - Priorita': ASSOLUTA (in cima al backlog)


## 9. COMANDI GIT PER IL PM

    git add -A
    git commit -m "Fase 9 SIGILLATA + Hotfix UUID/Nimitz/Blindatura

    - 9.A: OrderDB amputata, FK recise, tabella DROPpata
    - 9.B: supabase_bridge.py (3 funzioni async HTTPX)
    - 9.Fix: Sindrome UUID risolta, httpx sincrono rimosso
    - Strato difensivo router: remaining_seats deterministico
    - Frontend blindato: getRemainingSeats() e banner cap-pax
    - Dogma 16 (UUID) + Dogma 17 (httpx ban) sanciti
    - NIMITZ threshold (>= 1000) applicato
    - Fase 10 'Il Mangiasoldi' impostata nel backlog"
    git push origin main


--- FINE REPORT ---
