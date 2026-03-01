SYSTEM SNAPSHOT — RAFTING REPUBLIC ERP
Generato: 01/03/2026 01:33 CET
Sessione: Fase 10.G (Activity-Aware Guide Filtering + Flat Driver Fallacy + Espansione Calendario)
Stato Globale: FASE 10 STABILE — Il Mangiasoldi (Cassa & CRM)

═══════════════════════════════════════════════════════════

1. ARCHITETTURA INFRASTRUTTURALE
   ═══════════════════════════════════════════════════════════

1.1 DEPLOY TARGET

- Host: Ergonet CloudLinux (Protocollo LVE)
- RAM Limit: 1GB (Hard Ceiling)
- Entry Point: passenger_wsgi.py + a2wsgi (NO uvicorn diretto in produzione)
- DB Cloud: Supabase PostgreSQL (datacenter Francoforte)
- DB Locale: SQLite (rafting.db)
- AI Services: Azure OCR via REST API (ZERO modelli locali — Dogma LVE)

  1.2 ARCHITETTURA IBRIDA (Split-Brain Controllato)

- SQLite (Locale): Catalogo deterministico — activities, settings, staff, fleet, daily_rides, registrations
- Supabase (Cloud): Dati caldi — rides, orders, transactions, customers, ride_allocations
- Dual-Write: I turni (rides) esistono in ENTRAMBI i database con stesso UUID
- Bridge: app/services/supabase_bridge.py (httpx.AsyncClient, 3 funzioni async difensive)
- Sync Sonda: calendar.py \_fetch_supabase_pax (httpx sincrono, endpoint def — unica eccezione Dogma 17)

═══════════════════════════════════════════════════════════ 2. STACK TECNOLOGICO
═══════════════════════════════════════════════════════════

2.1 BACKEND

- Runtime: Python 3.x + FastAPI + Uvicorn (dev) / Passenger (prod)
- ORM: SQLAlchemy (solo Catalogo locale — DEPRECATO per transazioni)
- HTTP Client: httpx (async per Supabase bridge, sincrono SOLO per Sync Sonda legacy)
- Modelli DB attivi: ActivityDB, DailyRideDB, StaffDB, FleetDB, ResourceExceptionDB, ActivitySubPeriodDB, SystemSettingDB, RegistrationDB
- Modelli MORTI: OrderDB (amputata Fase 9), CustomerDB, TransactionDB, CrewAssignmentDB (amputate Fase 8)
- Router attivi: calendar.py, resources.py, desk.py, crew.py, public.py, registration.py, vision.py
- Router MORTI: orders.py, reservations.py, availability.py (inceneriti Fase 8/10)
- Servizi: availability_engine.py, ride_helpers.py, supabase_bridge.py

  2.2 FRONTEND

- Framework: Vue 3 + Quasar Framework
- State: Pinia (resource-store.js, crew-store.js, settings-store.js)
- HTTP: Axios (API backend) + Supabase JS Client (cloud diretto per cassa)
- Build: Quasar CLI (npx quasar dev)

═══════════════════════════════════════════════════════════ 3. MAPPA ORGANI VITALI (Pagine + Componenti)
═══════════════════════════════════════════════════════════

3.1 FRONTEND PAGES

- PlanningPage.vue — Calendario Operativo (Omni-Board hub). Vista giornaliera + mensile. Card turno con semaforo motore, pax/capienza (Nimitz-aware)
- TimelinePage.vue — Vista Gantt con toggle DISC/ROLE. Multi-Lane Packing. Barra Saturazione 144 bucket. Colori Status-Aware (STATUS_COLOR_MAP: A→Verde, B→Giallo, C→Rosso, D→Blu)
- CassaPage.vue — Libro Mastro (3 cassetti CASH/POS/TRANSFER), Anagrafica clienti, Fascicolo storico, Leva dello Strozzino
- SettingsPage.vue — Costruttore Flussi BPMN (Drag & Drop mattoncini), Pannello Variabili, Footprint Logistico
- ResourcesPage.vue — CRUD Staff/Fleet (SALVACONDOTTO — NON TOCCARE)

  3.2 COMPONENTI CRITICI

- RideDialog.vue — Modale suprema a 3 tab: Ordini Esistenti / Nuova Prenotazione / Equipaggi. Semaforo manuale Dual-Write. Nimitz-aware header. Kill-Switch turni vuoti
- CalendarComponent.vue — Cella mensile con mattoncini ride. Potenza di Fuoco footer (Date-Aware). NESSUN TRONCAMENTO: tutti i mattoncini visibili, grid-auto-rows: auto, box si espandono verticalmente
- CrewBuilderPanel.vue — Banchina d'Imbarco + Zona Fiume. Tetris Umano nominale. Sensore Galleggiamento. Kill-Switch Varo. Guide Activity-Aware (isGuideEligibleForActivity) + Idratazione Difensiva Pinia + Date-Awareness
- ResourcePanel.vue — Drawer laterale assegnazione risorse. Guide Activity-Aware con cascata 3 livelli (Codice DB → Macro-Classe → Nautico). Autisti filtrati per roles ['N','C','F'] (NO is_driver). Date-Aware + Nimitz-aware header
- DeskBookingForm.vue — POS integrato nella modale. Ledger Misto, Spacca-Conto, CRM Silente

  3.3 STORES PINIA

- resource-store.js — Hydration Node centrale. Esportazioni globali pre-store:
  - SKILL_MATRIX + expandRoles() (Matrice Ereditarietà Asimmetrica)
  - ACTIVITY_REQUIREMENTS (mappa codice attività → brevetti richiesti, sigle legacy + codici DB reali)
  - isGuideEligibleForActivity(guideRoles, activityObj) (cascata Scudo Nautico → Match Codice → Fallback Classe)
  - Getter: riverGuides (Skill Hierarchy), shuttleDrivers (roles ['N','C','F'] — NO is_driver), totalDailyPool
  - Actions: fetchStaff, fetchFleet, fetchDailySchedule, fetchCatalogs
- crew-store.js — Busta Stagna equipaggi. State: allocations. Actions: loadCrew, saveCrew (Swap & Replace). Getter: hasAnyOverflow (factory cross-store)
- settings-store.js — Pannello Variabili. Settings EAV SQLite

═══════════════════════════════════════════════════════════ 4. MOTORE PREDITTIVO (Availability Engine)
═══════════════════════════════════════════════════════════

4.1 ARCHITETTURA

- File: backend/app/services/availability_engine.py
- Paradigma: Time-Array Slicer a 1440 minuti (matrice discreta)
- Input: SQLite (catalogo + staff + fleet + eccezioni) + external_pax_map (Sync Sonda Supabase)
- Output per ride: total_capacity, arr_bonus_seats, booked_pax, remaining_seats, status (A/B/C/D)

  4.2 COSTANTI GLOBALI (Hotfix 10.F)

- SKILL_MATRIX: Matrice Ereditarietà Asimmetrica
  - RAF4 → {RAF4, RAF3}
  - RAF3 → {RAF3}
  - HYD → {HYD, SH, SK}
  - SH → {SH}
  - SK → {SK}
  - CB → {CB}
- NAUTICAL_ROLES: {'RAF4', 'RAF3', 'HYD', 'SH', 'SK', 'CB'}
- expand_roles(base_roles): Funzione pura di espansione gerarchica

  4.3 REGOLE DI BUSINESS

- Hard Limits (Rosso): Guide + Gommoni. Capacità ZERO se mancano
- Soft Limits (Giallo / Sarre): Furgoni su tratte brevi. MAI bloccare vendite
- Safety Kayak: floor = max(min_guides_absolute, needed_boats)
- Formula Furgoni: math.ceil(booked_pax / van_net_seats) — ZERO margini fantasma
- River Ledger (ARR Cascade): AD→CL (60min) → FA (30min)
- Override: is_overridden=True → Engine salta ricalcolo (Dogma Override)
- Nimitz: total_capacity >= 1000 → frontend nasconde denominatore (Dogma 15)

  4.4 METODO \_count_active_guides

- Carica TUTTO staff attivo (StaffDB.is_active == True)
- Parse difensivo ruoli (JSON string, array, CSV)
- Espansione gerarchica: expanded = expand_roles(raw_roles)
- Intersezione: NAUTICAL_ROLES.intersection(expanded) — MAI usare is_guide (Dogma 19)
- Filtro contratti: FISSO → verifica contract_periods date range, EXTRA → verifica eccezioni positive
- Filtro eccezioni: \_has_exception per assenze

═══════════════════════════════════════════════════════════ 5. ACTIVITY-AWARE GUIDE FILTERING (Fase 10.G)
═══════════════════════════════════════════════════════════

5.1 ARCHITETTURA CASCATA DECISIONALE

La funzione isGuideEligibleForActivity(guideRoles, activityObj) in resource-store.js implementa una cascata a 3 livelli:

- LIVELLO 1 — Scudo Dogma 19 Assoluto: intersezione expandRoles(guideRoles) con NAUTICAL_ROLES. Se la risorsa non possiede ALCUN brevetto nautico → false (civile, scarto immediato)
- LIVELLO 2 — Match Codice DB: lookup activityObj.code.toUpperCase() in ACTIVITY_REQUIREMENTS. Match → filtra per brevetti specifici richiesti
- LIVELLO 3 — Fallback Macro-Classe: se il codice è sconosciuto, ricade su activityObj.activity_class. HYDRO/HYDROSPEED → richiede HYD/SH/SK/CB. RAFT/RAFTING → richiede RAF4/RAF3
- ULTIMA RATIO: attività sconosciuta ma guida nautica certificata (Scudo 1 superato) → ammessa

  5.2 MAPPA ACTIVITY_REQUIREMENTS

- Sigle Legacy: AD→[RAF4], CL→[RAF4], SL→[RAF4], FA→[RAF3], HYD→[HYD,SH,SK,CB]
- Codici Fisici DB: A1→[RAF4], C1→[RAF4], S1→[RAF4], F1→[RAF3], H1→[HYD,SH,SK,CB], PL→[HYD,SH,SK,CB]

  5.3 IDRATAZIONE DIFENSIVA PINIA

- Problema: props.ride.activity è SEMPRE undefined (il ride non possiede un sotto-oggetto activity)
- Soluzione: lookup difensivo nel catalogo Pinia prima di passare l'oggetto a isGuideEligibleForActivity
  - CrewBuilderPanel.vue (store: resourceStore): props.ride?.activity || resourceStore.activities?.find(a => a.id === props.ride?.activity_id)
  - ResourcePanel.vue (store: store): props.ride?.activity || store.activities?.find(a => a.id === props.ride?.activity_id)

═══════════════════════════════════════════════════════════ 6. DB SCHEMA (Stato Corrente)
═══════════════════════════════════════════════════════════

6.1 SQLITE (rafting.db) — Catalogo Locale

- activities: id, name, code, activity_class, color_hex, duration_hours, workflow_schema (JSON con blocks + logistics), default_times, price, season_start, season_end
- daily_rides: id (UUID), activity_id (FK), date, time, end_time, status, is_overridden, notes
- staff: id, name, roles (JSON array), contract_type (FISSO/EXTRA), contract_periods (JSON array), is_active, is_guide (MORTO — Dogma 19), is_driver (MORTO — Corollario Dogma 19 Terra)
- fleet: id, name, category (RAFT/VAN/TRAILER), capacity, has_tow_hitch, is_active
- resource_exceptions: id, resource_id, resource_type (STAFF/FLEET), is_available, dates (JSON array)
- system_settings: key, value (EAV per variabili dinamiche)
- registrations: id, order_id (UUID stringa orfana Supabase), daily_ride_id, nome, cognome, email, firaft_status
- activity_sub_periods: id, activity_id, start_date, end_date, custom_times

  6.2 SUPABASE (Cloud PostgreSQL) — Dati Operativi

- rides: id (UUID), activity_id, date, time, status, is_overridden
- orders: id (UUID), ride_id (FK), customer_id (FK), customer_name, booker_name, pax, total_pax, price_total, price_paid, status, discount_applied, is_exclusive_raft, notes, created_at
- transactions: id (UUID), order_id (FK), amount, method (CASH/SUMUP/BONIFICO/ALTRO), type, note, created_at (TIMESTAMPTZ DEFAULT now())
- customers: id (UUID), full_name, email, phone
- ride_allocations: id (UUID), ride_id (FK), resource_id (UUID LOGICA — no FK fisica, Dogma 12), resource_type (crew_manifest), metadata (JSONB: guide_id, groups[{order_id, customer_name, pax}])

═══════════════════════════════════════════════════════════ 7. DOGMI ARCHITETTURALI (Registro Completo)
═══════════════════════════════════════════════════════════

- Dogma DDL Supabase: NOTIFY pgrst obbligatorio dopo ogni ALTER TABLE
- Dogma Override: is_overridden=True → Engine salta ricalcolo
- Dogma 10 (Tetris Umano): Passeggeri = frazioni di ordini nominali, mai numeri anonimi
- Dogma 11 (Swap & Replace): Update massivo = DELETE + bulk INSERT
- Dogma 12 (Chiavi Logiche Cross-DB): No FK fisiche verso l'altro database
- Dogma 13 (Kill-Switch Varo): UI blocca salvataggio se overflow o fantasmi
- Dogma 14 (Walkie-Talkie HTTPX): OrderDB amputata, dati via httpx.AsyncClient
- Dogma 15 (Nimitz): total_capacity >= 1000 → nascondi denominatore
- Dogma 16 (Sindrome UUID): str(ride.id) OBBLIGATORIO prima di dict.get()
- Dogma 17 (No httpx sincrono): MAI httpx.Client() in endpoint async def
- Dogma 18 (Graffettatrice): UPSERT customer → customer_id → INSERT order
- Dogma 19 (Flat Role Fallacy): MAI usare is_guide. Solo NAUTICAL_ROLES.intersection(expand_roles(roles))
  - Corollario Skill Hierarchy: SKILL_MATRIX implementata. expand_roles() applicata su 4 file (backend + 3 frontend)
  - Corollario Activity-Aware: isGuideEligibleForActivity() con cascata 3 livelli (Codice DB → Macro-Classe → Nautico) + Idratazione Difensiva Pinia
  - Corollario Comparto Terra (01/03/2026): DIVIETO ASSOLUTO di usare is_driver nel frontend. Autisti SOLO da roles.some(r => ['N','C','F'].includes(r))

═══════════════════════════════════════════════════════════ 8. FASI COMPLETATE (Cronologia)
═══════════════════════════════════════════════════════════

- Fase 5: Motore BPMN + Yield Engine V5
- Fase 6: Logistica Fluidodinamica + POS Ibrido (24-27/02/2026)
- Fase 7: Crew Builder completo (27/02/2026)
- Fase 8: Smaltimento Debito Tecnico (27/02/2026)
- Fase 9: Migrazione OrderDB a Supabase (27-28/02/2026)
- Fase 10.A-D: Il Mangiasoldi — Cassa & CRM (28/02/2026)
- Fase 10.fix: Acchiappafantasmi, Allucinazioni, Graffettatrice, Cronografo (28/02/2026)
- Hotfix 10.E: Data-Awareness, Nimitz Modale, Timeline Cromatica, Troncamento Calendario (28/02/2026)
- Hotfix 10.F: Skill Hierarchy Matrix — SKILL_MATRIX + expand_roles() su 4 file (28/02/2026)
- Fase 10.G: Activity-Aware Guide Filtering + Flat Driver Fallacy + Espansione Calendario (01/03/2026)

═══════════════════════════════════════════════════════════ 9. FILE MODIFICATI IN QUESTA SESSIONE (01/03/2026 00:18-01:33)
═══════════════════════════════════════════════════════════

9.1 FASE 10.G — Activity-Aware Guide Filtering

- resource-store.js: +ACTIVITY_REQUIREMENTS (sigle legacy + codici DB reali), +isGuideEligibleForActivity(guideRoles, activityObj) con cascata 3 livelli, firma cambiata da stringa a oggetto attività
- CrewBuilderPanel.vue: import isGuideEligibleForActivity (rimosso expandRoles), idratazione difensiva Pinia (resourceStore.activities.find), guideOptions usa isGuideEligibleForActivity
- ResourcePanel.vue: import isGuideEligibleForActivity (rimosso expandRoles), idratazione difensiva Pinia (store.activities.find), filteredGuideOptions usa isGuideEligibleForActivity. RIMOSSI: currentActivityClass, validGuideRoles, HYDRO_GUIDE_ROLES, RAFT_GUIDE_ROLES

  9.2 ESPANSIONE VERTICALE CALENDARIO

- CalendarComponent.vue: Rimosso MAX_VISIBLE_RIDES=5, rimosso .slice(0, MAX_VISIBLE_RIDES) dal v-for, rimosso badge overflow "+ N altri", rimossa classe .overflow-badge. Grid CSS: grid-template-rows cambiato da "auto 1fr..." a "auto" + grid-auto-rows: auto. slots-container: overflow-y cambiato da auto a visible

  9.3 HOTFIX FLAT DRIVER FALLACY

- resource-store.js: shuttleDrivers → da s.is_driver a s.is_active !== false && Array.isArray(s.roles) && s.roles.some(r => ['N','C','F'].includes(r)). totalDailyPool.drivers → stessa logica role-based
- ResourcePanel.vue: DRIVER_ROLES aggiornato da ['N','C'] a ['N','C','F']. filteredDriverOptions: rimosso s.is_driver, ora usa Array.isArray(s.roles) && s.roles.some(r => DRIVER_ROLES.includes(r))

  9.4 DOCUMENTAZIONE

- LORE_VAULT.md: Aggiunta Fase 10.G (meccanica 3 livelli + idratazione Pinia). Corollario Dogma 19 Comparto Terra. Timestamp aggiornato
- PROJECT_RADAR.md: Fase 10.G aggiunta come completata (5 sotto-task). Opzione C spostata da backlog a completati. Flat Driver Fallacy nei completati. Backlog ridotto a 2 opzioni

═══════════════════════════════════════════════════════════ 10. DEBITO TECNICO RESIDUO
═══════════════════════════════════════════════════════════

- is_guide: colonna ancora presente in StaffDB ma IGNORATA ovunque (Dogma 19). Candidata per DROP futuro
- is_driver: colonna ancora presente in StaffDB ma IGNORATA nel frontend (Corollario Dogma 19 Terra). Candidata per DROP futuro
- Sync Sonda legacy: httpx sincrono in calendar.py (unica eccezione Dogma 17). Migrazione a async pianificabile
- Barra Saturazione Timeline: usa staffList.filter(is_active) generico, non espansione ruoli nautica
- Backend availability_engine.py: la funzione \_count_active_guides usa ancora il filtro generico NAUTICAL_ROLES, non il filtro Activity-Aware. L'Opzione C è stata implementata SOLO lato frontend. Il backend non distingue ancora tra guide RAF e guide HYD nel calcolo predittivo della capienza per turno

═══════════════════════════════════════════════════════════ 11. PROSSIMI OBIETTIVI (Backlog Strategico)
═══════════════════════════════════════════════════════════

1. Fase 10 continuazione: Reportistica avanzata, storico ordini per cliente, dashboard incassi giornalieri
2. Opzione B: Modulo Presenze Giornaliere Staff
3. Backend Activity-Aware Engine: estendere il filtro per attività anche a \_count_active_guides nel Motore Predittivo

-- FINE SNAPSHOT --
