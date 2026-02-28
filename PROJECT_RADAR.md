# PROJECT RADAR

## STATO ATTUALE: FASE 10 STABILE — Il Mangiasoldi (Cassa & CRM)

---

**CANTIERE STABILE — Fase 10: Il Mangiasoldi (28/02/2026)**

### Fase 10.A — Fondazione Cassa & CRM + Inceneritore Debito Tecnico

- [x] **BUG-1 (TECH_ARCHITECTURE Fossile OrderDB — 28/02/2026):** Rimosso riferimento obsoleto "da OrderDB → DailyRideDB → ActivityDB". Aggiunta dichiarazione esplicita: OrderDB AMPUTATA, integrità referenziale cross-DB via UUID stringhe orfane (Dogma 12).
- [x] **BUG-2 (Router Reservations Zombi — 28/02/2026):** Eliminato fisicamente `reservations.py`. Rimosso import e `include_router` da `main.py`.
- [x] **BUG-3 (Yield Engine Zavorra — 28/02/2026):** Eliminato fisicamente `yield_engine.py` (servizio morto, mai referenziato).
- [x] **BUG-4 (Filo Scoperto availability.py — 28/02/2026):** Router `availability.py` (guscio vuoto del defunto `yield_engine.py`) decablato da `main.py`. ImportError che crashava Uvicorn.
- [x] **Fase 10.A (CassaPage Frontend — 28/02/2026):** Creata `CassaPage.vue` con client Supabase JS diretto (Dogma: i soldi si contano in Banca). Due tab: Libro Mastro (totali per metodo pagamento + q-table transazioni) e Anagrafica (q-table clienti con filtro locale reattivo). Rotta `/admin/cassa` cablata. Menu laterale aggiornato con icona `point_of_sale`.
- [x] **Fase 10.B (Cassetti e Fascicoli — 28/02/2026):** 3 card totali fissi (CASH/POS/TRANSFER con colori semantici). Drill-down clienti con dialog laterale: query relazionale Supabase `orders + rides + transactions`. Semaforo debiti per ordine (badge rosso DEBITO / verde SALDATO).
- [x] **Fase 10.C (Leva dello Strozzino — 28/02/2026):** Bottone "Incassa Saldo" nel fascicolo cliente. Modale incasso con importo precompilato e select metodo. Dual-Query Supabase: INSERT transaction + UPDATE order.price_paid. Refresh automatico fascicolo + Libro Mastro.
- [x] **Fase 10.D (Spia Check Engine — 28/02/2026):** Error handling rumoroso nel fascicolo cliente (console.error + alert). Ispezione desk.py: pipeline CRM già corretta (full_name/email/phone + Prefer return=representation + customer_id iniettato). Colonne Anagrafica verificate.

- [x] **Fase 10.fix — Operazione Acchiappafantasmi (28/02/2026):** Blindatura Frontend (DeskBookingForm.vue): rules Quasar obbligatorie su booker_name con trim + lazy-rules, validazione programmatica via ref, bottone CONFERMA disabilitato se nome vuoto o soli spazi. Blindatura Backend (desk.py): fallback difensivo "Cliente Walk-in" se booker_name vuoto, CRM UPSERT SEMPRE eseguito (rimosso bypass condizionale), parsing risposta Supabase robusto (list/dict), Kill-Switch Dogma 18 (HTTPException 400 se customer_id ancora None dopo il pipeline CRM). **BUG CRITICO 7.1 (Ordini orfani): RISOLTO E COLLAUDATO E2E.**
- [x] **Fase 10.fix — Cura Allucinazioni Frontend (28/02/2026):** CassaPage.vue: corretta select relazionale rides(date, time) invece di rides(ride_date, ride_time). Rimossa colonna created_at inesistente dalla q-table transazioni e dal template pagamenti nel fascicolo. Ordinamento fetchTransactions cambiato da .order('created_at') a .order('id'). Campo notes corretto in note. Eliminati 2 errori Supabase 42703.
- [x] **Fase 10.fix — Graffettatrice Vue (28/02/2026):** CassaPage.vue: importato uid() da Quasar e iniettato come Primary Key nel payload INSERT su tabella transactions. Fix violazione vincolo NOT NULL su colonna id. Corollario Dogma 18 sancito nel LORE_VAULT.

---

**CANTIERE CHIUSO — Fase 9: Migrazione OrderDB a Supabase ✅ SIGILLATA (27/02/2026 23:55)**

**Tutti gli obiettivi completati.**

---

### Fase 8 Completata — Smaltimento Debito Tecnico (27/02/2026) ✅ SIGILLATA

- [x] **DT-1 (Consolidamento Requirements — 27/02/2026):** Inceneriti `requirements_fixed.txt`, `requirements_frozen.txt`, `requirements_lock.txt`. Sopravvivono solo `requirements.txt` (dev) e `requirements_production.txt` (deploy).
- [x] **DT-2 (Epurazione JSDoc Obsoleti — 27/02/2026):** Rimossi TODO obsoleti (`FASE 6.F`), commenti FK morte, template `assigned_staff/assigned_fleet` legacy da `PlanningPage.vue`. Puliti commenti duplicati e riferimenti a vecchie FK in `CalendarComponent.vue`.
- [x] **DT-3 (Amputazione ORM Tabelle Morte — 27/02/2026):** Distrutte `CrewAssignmentDB`, `ride_staff_link`, `ride_fleet_link` da `calendar.py`. Amputate tutte le relationship orfane da `DailyRideDB`, `StaffDB`, `FleetDB`. Epurati import da `main.py`, `__init__.py`, `init_db.py`. Import `Table` rimosso.
- [x] **DT-4 (Inceneritore AI Locale — 27/02/2026):** Distrutto `local_vision_service.py` (36KB, Paddle+YOLO+GLiNER). Sterilizzati import orfani in `vision.py` e `registration.py` con stub `AI_AVAILABLE=False`. Azure OCR è l'unico provider.
- [x] **DT-5 (Demolizione Cimitero Backend — 27/02/2026):** Router `/api/v1/legacy-orders` incenerito (file `orders.py` eliminato). Classi `CustomerDB` e `TransactionDB` amputate da `calendar.py`. Schemi `OrderCreate`/`OrderResponse` eliminati. Helper `calculate_booked_pax`/`recalculate_ride_status` estratti in `ride_helpers.py`. Tabelle SQLite `transactions` e `customers` DROPpate da `rafting.db`. `OrderDB` mantenuta per integrità relazionale (DailyRideDB, RegistrationDB, AvailabilityEngine).
- [x] **DT-6 (Silenziamento Regex Deprecate — 27/02/2026):** Sostituito `regex=` con `pattern=` in `resources.py` e `reservations.py`. Zero warning FastAPI residui.

### Fase 7 Completata — Crew Builder (27/02/2026) ✅ SIGILLATA

- [x] **Fase 7.A (Scaffold Tubature — 27/02/2026):** Router `crew.py` (GET/PUT allocations), `CrewBuilderPanel.vue`, tab "Equipaggi" in RideDialog.
- [x] **Fase 7.B (Fondazione Busta Stagna — 27/02/2026):** Script DDL Supabase per `ride_allocations` (colonna `metadata` JSONB, indici, RLS). Store Pinia `crew-store.js` con actions `loadCrew`/`saveCrew` via Axios.
- [x] **Fase 7.C (Banchina d'Imbarco UI — 27/02/2026):** `CrewBuilderPanel.vue` ricostruito con righe dinamiche [Gommone q-select] + [Guida q-select] + [Pax q-input]. Zona Banchina con contatori pax paganti/imbarcati/in attesa e allarme over-assegnazione. Pulsante "SIGILLA EQUIPAGGI".
- [x] **Fase 7.C.2 (Tetris Umano — 27/02/2026):** Dogma 10 sancito. metadata dei gommoni ora contiene `groups: [{ order_id, customer_name, pax }]`. Zona Banchina mostra pax residui per ordine con badge verde/arancione. Zona Fiume con sezione "Gruppi Imbarcati" editabile e select "Aggiungi Gruppo" filtrato per pax residui > 0.
- [x] **Fase 7.D (Allineamento Valvola Backend — 27/02/2026):** Fix 422. Schemi Pydantic allineati al Tetris Umano (CrewGroup, CrewMetadata, CrewAllocationItem). PUT accetta `List[CrewAllocationItem]`. Tecnica Swap & Replace (DELETE+bulk INSERT via httpx). GET restituisce `{ allocations: [...] }`. Store frontend allineato: saveCrew invia array diretto, loadCrew legge da `data.allocations`. Rimosso dump errore raw dalla UI.
- [x] **Fase 7.D.fix (Autopsia Tripla — 27/02/2026):** Fix Auth JWT 401 (chiavi Supabase migrate da hardcode a `.env` con `load_dotenv()` e blindatura `.strip()`). Fix Pydantic mismatch `resource_type` ("RAFT" → "crew_manifest"). Amputazione Foreign Key Supabase `ride_allocations_resource_id_fkey` per risorse locali (Errore 409). Cura della Sindrome dell'Arto Fantasma nel frontend: epurate JOIN PostgREST `resources(*)` da `resource-store.js` (Errore PGRST200). Sanciti Dogma 12 e Corollario Arto Fantasma nel LORE_VAULT.
- [x] **Fase 7.E (Sensori di Galleggiamento e Bilancia Banchina — 27/02/2026):** Installati 3 sensori visivi nel CrewBuilderPanel. (1) Bilancia Banchina: q-banner reattivo a 3 stati (🚨 Rosso fantasmi / ⚠️ Arancione molo / ✅ Verde bilancio perfetto). (2) Sensore di Galleggiamento: card gommone con bordi e sfondo dinamici (rosso overflow, verde pieno, blu liberi) + badge carico/capienza. Incrocio resource_id con fleetList per capacity fisica. (3) Kill-Switch Varo: bottone SIGILLA EQUIPAGGI bloccato se overflow o sovra-assegnazione, con tooltip motivo blocco. Getter `hasAnyOverflow` aggiunto al crew-store.
- [x] **Fase 7.E.fix (Pompa di Sentina e Collaudo — 27/02/2026):** Script `purge_bilge.py` eseguito: 0 record fossili trovati (sentina pulita). Collaudo E2E confermato dal PM. Script di spurgo smantellato dopo esecuzione (niente esplosivi incustoditi nel cantiere). Dogma 13 sancito nel LORE_VAULT.

### Fase 9 Completata — Migrazione OrderDB a Supabase (28/02/2026) ✅ SIGILLATA

- [x] **Fase 9.A (Amputazione ORM OrderDB — 27/02/2026):** Classe `OrderDB` eliminata fisicamente da `calendar.py`. FK `orders.id` recisa da `RegistrationDB` (colonna `order_id` → stringa orfana UUID Supabase). Tabella `orders` DROPpata da `rafting.db` via `drop_orders_table.py`. Tutte le `joinedload(DailyRideDB.orders)` rimosse da `calendar.py`, `public.py`, `availability_engine.py`. Export FIRAFT riscritta con JOIN diretto `RegistrationDB.daily_ride_id → DailyRideDB`. Import `OrderDB` epurato da `main.py`, `__init__.py`.
- [x] **Fase 9.B (Cablaggio Walkie-Talkie HTTPX — 27/02/2026):** Creato `supabase_bridge.py` (modulo radio centralizzato: 3 funzioni async `fetch_orders_by_ride`, `fetch_order_by_id`, `fetch_pax_by_rides`). Matrioska cablata: `GET /daily-rides/{ride_id}` restituisce ordini Supabase via HTTPX. Daily-schedule: pax reali da `fetch_pax_by_rides`. Public API Kiosk: ordine validato su Supabase Cloud. Schema Pydantic: `orders: List[dict]` per JSON Supabase nativo.
- [x] **Fase 9.Fix (Pallottoliere Engine + Nimitz — 27/02/2026):** `ride_helpers.py` cablato a Supabase via httpx sincrono (non più `return 0`). `_calc_booked_pax` nell'Engine usa `external_pax_map` correttamente (iniettato dalla Sync Sonda). Frontend: soglia NIMITZ (capacity ≥ 1000) → nasconde denominatore, posti residui e progress bar per attività senza vincoli logistici. Mostra solo "X pax confermati".
- [x] **Fase 9.Fix (Hotfix Pallottoliere + Sindrome UUID — 28/02/2026):** `ride_helpers.py` epurato da httpx sincrono vietato (Dogma 17). Strato difensivo matematico nei router: `remaining_seats = max(0, total_cap - booked_pax)` se Engine ignora i pax. Frontend blindato: `getRemainingSeats()` e banner Omni-Board deterministici (`cap - pax`). Dogma 16 (Sindrome UUID) e Dogma 17 (Divieto httpx sincrono) sanciti nel LORE_VAULT.

### Fase 6 Completata — Logistica Fluidodinamica e POS Ibrido (24-27/02/2026)

🔴 SITREP V5 - POST NOTTE 24/25 FEBBRAIO (LOGISTICA FLUIDODINAMICA)

**VITTORIE CONSEGUITE (Check-point Fase 6):**

- [x] **Fase 6.E.5 (River Ledger)**: Implementazione completa ARR Cascade (AD->CL->FA) e integrazione endpoint dettaglio discesa.
- [x] **Fase 6.A (Daily Board Onesta):** Estirpato l'hardcode "16 pax" dal Calendario Operativo (`PlanningPage.vue`). Il frontend ora legge i veri `booked_pax` (dalla tabella `orders` in Supabase) e degrada onestamente l'UI se la capacità commerciale massima è ignota.
- [x] **Fase 6.B (Crew Builder - Blueprint):** Teorizzata l'architettura relazionale orizzontale. La tabella `ride_allocations` in Supabase utilizzerà la colonna `metadata` (JSONB) per legare le tuple `[Guida + Gommone + Passeggeri]`. Vietati i select multipli generici. (Rif: `PHASE_7_BLUEPRINT.md`).
- [x] **Fase 6.D (Il Sacco Risorse & Ricettario DB):** Sventrato il Costruttore di Flussi (`SettingsPage.vue`). Il "Footprint Logistico" (es. `min_guides`, `requires_van`, `requires_trailer`) viene ora configurato visivamente e salvato nativamente nel campo JSON `workflow_schema.logistics` della tabella `activities`, aggirando le migrazioni SQL.
- [x] **Fase 6.E.1/2 (Sensori Pinia):** Lo store Vue (`resource-store.js`) è stato cablato con i getter vitali (`riverGuides`, `shuttleDrivers`, `towVans` tramite `has_tow_hitch`, `trailers`) per quantificare il pool logistico aziendale massimo disponibile al mattino ("Fondo del Sacco").
- [x] **Fase 6.E.3 (Motore di Svuotamento BPMN Backend):** Implementato il Time-Array Slicer a matrice discreta (1440 min) per incrociare i mattoncini temporali. Applicata Eccezione di Sarre (Soft Limits furgoni -> Semaforo Giallo). Implementato Two-Pass parsing per blocchi a ritroso (anchor=end).
- [x] **Fase 6.E.4 (Caduta dei Mock, Sensori Flotta e Ratio Logistici Reali):** Implementata l'estrazione EAV difensiva dal Pannello Variabili (calcolo posti netti dei van). Implementato sensore \_count_available_vans da FleetDB. Integrata la logica non-lineare della 'Regola del Safety Kayak' (Hard Floor Tributo) per il calcolo delle barche varabili e il blocco semaforo.
- [x] **Fase 6.E.6 (Patch Immortality & Kill-Switch):** Blindata l'affidabilità del sistema. Implementata logica Date-Aware per lo staff mensile e Hard-Floor matematico lato client per prevenire falsi positivi di disponibilità. Corretto il bug del conteggio flotta (bypass contract logic).
- [x] **Fase 6.E.7 (Risoluzione Split-Brain & Pax Map Injection):** Disinnescato il bug critico dell'Overbooking ("Zero Assoluto") causato dall'isolamento dell'ORM locale. Implementata la "Sync Sonda" nel router FastAPI (`calendar.py`) tramite `httpx` per estrarre i veri `booked_pax` da Supabase.
- [x] **Fase 6.E (Availability Engine / Dashboard):** SISTEMA COMPLETATO.
- [x] **[CODICE ROSSO] RISOLUZIONE SPLIT-BRAIN DESK POS:** Sventrato `desk.py`. Amputato SQLAlchemy per flussi commerciali e sostituito con iniezione HTTPX nativa verso Supabase.
- [x] **Iniezione Architettura Ibrida POS:** Implementato Dual-Write su `POST /desk` per i turni (`DailyRideDB` locale per UI, `rides` in cloud per FK). Catalogo letto da SQLite locale.
- [x] **Fondazione Relazionale Cloud:** Eseguito DDL in Supabase per fondare `transactions`, `registrations`, `customers` e allineare `orders` con chiavi esterne `ON DELETE CASCADE`.
- [x] **Fase 6.F (Fix Engine Precision — 27/02/2026):** Eliminato il "Passeggero Fantasma" (`+ 1`) nella formula `target_vans_needed`. La formula è ora deterministica: `math.ceil(booked_pax / van_net_seats)`.
- [x] **Fase 6.G (Persistenza Override Manuale — 27/02/2026):** Colonna `is_overridden` in `daily_rides` blocca il ricalcolo del semaforo. Engine salta Pass 1 e Pass 2 per turni overridden.
- [x] **Fase 6.H (Kill-Switch Turni Vuoti — 27/02/2026):** Endpoint `POST /daily-rides/close` con `status='X'`. Filtro e rimozione reattiva.
- [x] **Fase 6.I (Dual-Write Semaforo — 27/02/2026):** Bottoni VERDE/BLU/GIALLO/ROSSO/AUTO nel RideDialog con Dual-Write Supabase+SQLite.
- [x] **Fase 6.J (Timeline Flussi — 27/02/2026):** Vista Discese + Vista Ruoli, Multi-Lane Packing, Barra Saturazione a 144 bucket.
- [x] **Fase 6.K (Spurgo Sentina — 27/02/2026):** Incenerito DeskDashboardPage.vue, 9 file debug, collisione router disinnescata, system_settings idratato.
- [x] **Fase 6.L (Drag & Drop Blocchi BPMN — 27/02/2026):** Riordinamento blocchi nei flussi via HTML5 Drag & Drop nativo nel Costruttore di Flussi.

**Fix e Manutenzioni Fase 6:**

- [x] Fix 422 Date Format (Pydantic).
- [x] Allineamento Split-Brain SQLite (customer_id).
- [x] Innesto DeskBookingForm.vue in RideDialog (Omni-Board).
- [x] Emorragia Supabase "ride_date" curata con Inner Join PostgREST.
- [x] Fix Omni-Board: Prezzo Unitario, Reattività emit refresh, Libro Mastro.
- [x] Collaudo POS (27/02/2026 09:56). Audit UUID: 5/5 MATCH.
- [x] Fix Allucinazione UI PlanningPage: riga "posti residui".

### Fase 5 Completata — Motore BPMN e Yield Engine V5:

1. Incenerito il vecchio Yield Engine V4 e le costanti temporali globali.
2. Implementato **Costruttore di Flussi a Mattoncini** in `SettingsPage.vue`.
3. Implementato **Yield Engine V5 e Scudo Anti-Ubiquità V5**.
4. Fix Reattività State Management (campo fossile "Tratti Fiume", Ghost Slots).
5. Pulizia Supabase dati orfani (Split-Brain risolto).

---

## BACKLOG STRATEGICO (Priorità):

1. **STABILE → Fase 10: Il Mangiasoldi (Cassa & CRM).** Fase 10.A-D completata + 3 fix (Acchiappafantasmi, Allucinazioni Schema, Graffettatrice). Prossimo: Reportistica avanzata, storico ordini per cliente, dashboard incassi giornalieri.
2. **Opzione B:** Modulo Presenze Giornaliere Staff.

**Completati:**

- [x] ~~Opzione A: Timeline View~~ → COMPLETATA (Fase 6.J)
- [x] ~~TATTICA IMMINENTE 1: Amputazione ruderi geologici~~ → COMPLETATA
- [x] ~~TATTICA IMMINENTE 1.5: Abortita amputazione ResourcesPage~~ → Falso Positivo UI
- [x] ~~Fase 8: Smaltimento Debito Tecnico~~ → COMPLETATA (27/02/2026)
- [x] ~~Fase 9: Migrazione OrderDB a Supabase~~ → COMPLETATA E SIGILLATA (28/02/2026)
