# PROJECT RADAR

## STATO ATTUALE: FASE 7 (Crew Builder — Lavagna d'Imbarco)

---

**CANTIERE ATTIVO — Fase 7.E: Collaudo end-to-end e Validazioni (Tetris Umano)**

**Obiettivi Prossima Sessione:**

- [ ] Warning UI se `SUM(groups.pax) != totale pax paganti` (mismatch imbarcati vs prenotati)
- [ ] Highlight barche piene / overflow sulla capienza del gommone fisico
- [ ] Collaudo end-to-end Tetris Umano: salva → ricarica → verifica persistenza Supabase
- [ ] Pulizia record orfani eventualmente creati durante il debugging Fase 7.D

---

## Debito Tecnico Pendente:

Residuali dalla Fase 6.K:

- Pulizia commenti JSDoc obsoleti.
- Consolidamento file requirements multipli (`requirements.txt`, `_fixed`, `_frozen`, `_lock`, `_production`).

---

## STORICO TRAGUARDI RAGGIUNTI:

### Fase 7 Completata — Crew Builder (27/02/2026)

- [x] **Fase 7.A (Scaffold Tubature — 27/02/2026):** Router `crew.py` (GET/PUT allocations), `CrewBuilderPanel.vue`, tab "Equipaggi" in RideDialog.
- [x] **Fase 7.B (Fondazione Busta Stagna — 27/02/2026):** Script DDL Supabase per `ride_allocations` (colonna `metadata` JSONB, indici, RLS). Store Pinia `crew-store.js` con actions `loadCrew`/`saveCrew` via Axios.
- [x] **Fase 7.C (Banchina d'Imbarco UI — 27/02/2026):** `CrewBuilderPanel.vue` ricostruito con righe dinamiche [Gommone q-select] + [Guida q-select] + [Pax q-input]. Zona Banchina con contatori pax paganti/imbarcati/in attesa e allarme over-assegnazione. Pulsante "SIGILLA EQUIPAGGI".
- [x] **Fase 7.C.2 (Tetris Umano — 27/02/2026):** Dogma 10 sancito. metadata dei gommoni ora contiene `groups: [{ order_id, customer_name, pax }]`. Zona Banchina mostra pax residui per ordine con badge verde/arancione. Zona Fiume con sezione "Gruppi Imbarcati" editabile e select "Aggiungi Gruppo" filtrato per pax residui > 0.
- [x] **Fase 7.D (Allineamento Valvola Backend — 27/02/2026):** Fix 422. Schemi Pydantic allineati al Tetris Umano (CrewGroup, CrewMetadata, CrewAllocationItem). PUT accetta `List[CrewAllocationItem]`. Tecnica Swap & Replace (DELETE+bulk INSERT via httpx). GET restituisce `{ allocations: [...] }`. Store frontend allineato: saveCrew invia array diretto, loadCrew legge da `data.allocations`. Rimosso dump errore raw dalla UI.
- [x] **Fase 7.D.fix (Autopsia Tripla — 27/02/2026):** Fix Auth JWT 401 (chiavi Supabase migrate da hardcode a `.env` con `load_dotenv()` e blindatura `.strip()`). Fix Pydantic mismatch `resource_type` ("RAFT" → "crew_manifest"). Amputazione Foreign Key Supabase `ride_allocations_resource_id_fkey` per risorse locali (Errore 409). Cura della Sindrome dell'Arto Fantasma nel frontend: epurate JOIN PostgREST `resources(*)` da `resource-store.js` (Errore PGRST200). Sanciti Dogma 12 e Corollario Arto Fantasma nel LORE_VAULT.

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

## BACKLOG (Idee in Stand-by):

- [x] ~~Opzione A: Timeline View~~ → COMPLETATA (Fase 6.J)
- [ ] Opzione B: Modulo Presenze Giornaliere Staff.
- [ ] Opzione C: Flusso Prenotazioni CRM (Anagrafiche, Pagamenti).
- [x] TATTICA IMMINENTE 1: Amputazione ruderi geologici completata.
- [x] TATTICA IMMINENTE 1.5: Abortita amputazione ResourcesPage (Falso Positivo UI).
