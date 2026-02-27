# PROJECT RADAR

## STATO ATTUALE: FASE 6 IN CORSO (Motore Logistico Predittivo e Crew Builder)

### 🔴 SITREP V5 - POST NOTTE 24/25 FEBBRAIO (LOGISTICA FLUIDODINAMICA)

**VITTORIE CONSEGUITE (Check-point Fase 6):**

- [x] **Fase 6.E.5 (River Ledger)**: Implementazione completa ARR Cascade (AD->CL->FA) e integrazione endpoint dettaglio discesa.
- [x] **Fase 6.A (Daily Board Onesta):** Estirpato l'hardcode "16 pax" dal Calendario Operativo (`PlanningPage.vue`). Il frontend ora legge i veri `booked_pax` (dalla tabella `orders` in Supabase) e degrada onestamente l'UI se la capacità commerciale massima è ignota.
- [x] **Fase 6.B (Crew Builder - Blueprint):** Teorizzata l'architettura relazionale orizzontale. La tabella `ride_allocations` in Supabase utilizzerà la colonna `metadata` (JSONB) per legare le tuple `[Guida + Gommone + Passeggeri]`. Vietati i select multipli generici. (Rif: `PHASE_6_B_CREW_BUILDER.md`).
- [x] **Fase 6.D (Il Sacco Risorse & Ricettario DB):** Sventrato il Costruttore di Flussi (`SettingsPage.vue`). Il "Footprint Logistico" (es. `min_guides`, `requires_van`, `requires_trailer`) viene ora configurato visivamente e salvato nativamente nel campo JSON `workflow_schema.logistics` della tabella `activities`, aggirando le migrazioni SQL. (Rif: `PHASE_6_D_DYNAMIC_YIELD.md`).
- [x] **Fase 6.E.1/2 (Sensori Pinia):** Lo store Vue (`resource-store.js`) è stato cablato con i getter vitali (`riverGuides`, `shuttleDrivers`, `towVans` tramite `has_tow_hitch`, `trailers`) per quantificare il pool logistico aziendale massimo disponibile al mattino ("Fondo del Sacco").

- [x] **Fase 6.E.3 (Motore di Svuotamento BPMN Backend):** Implementato il Time-Array Slicer a matrice discreta (1440 min) per incrociare i mattoncini temporali. Applicata Eccezione di Sarre (Soft Limits furgoni -> Semaforo Giallo). Implementato Two-Pass parsing per blocchi a ritroso (anchor=end).

- [x] **Fase 6.E.4 (Caduta dei Mock, Sensori Flotta e Ratio Logistici Reali):** Implementata l'estrazione EAV difensiva dal Pannello Variabili (calcolo posti netti dei van). Implementato sensore \_count_available_vans da FleetDB. Integrata la logica non-lineare della 'Regola del Safety Kayak' (Hard Floor Tributo) per il calcolo delle barche varabili e il blocco semaforo.

- [x] **Fase 6.E.6 (Patch Immortality & Kill-Switch):** Blindata l'affidabilità del sistema. Implementata logica Date-Aware per lo staff mensile e Hard-Floor matematico lato client per prevenire falsi positivi di disponibilità. Corretto il bug del conteggio flotta (bypass contract logic).
- [x] **Fase 6.E.7 (Risoluzione Split-Brain & Pax Map Injection):** Disinnescato il bug critico dell'Overbooking ("Zero Assoluto") causato dall'isolamento dell'ORM locale. Implementata la "Sync Sonda" nel router FastAPI (`calendar.py`) tramite `httpx` per estrarre i veri `booked_pax` da Supabase. I dati vengono ora iniettati dinamicamente come `external_pax_map` nell'Availability Engine (Dependency Injection), costringendo il Time-Array Slicer a calcolare il Fondo del Sacco sui reali paganti e a rispettare il Teorema del Sacco sui turni paralleli.
- [x] **Fase 6.E (Availability Engine / Dashboard):** SISTEMA COMPLETATO.
- [x] **[CODICE ROSSO] RISOLUZIONE SPLIT-BRAIN DESK POS:** Sventrato `desk.py`. Amputato SQLAlchemy per flussi commerciali e sostituito con iniezione HTTPX nativa verso Supabase.
- [x] **Iniezione Architettura Ibrida POS:** Implementato Dual-Write su `POST /desk` per i turni (`DailyRideDB` locale per UI, `rides` in cloud per FK). Catalogo letto da SQLite locale.
- [x] **Fondazione Relazionale Cloud:** Eseguito DDL in Supabase per fondare `transactions`, `registrations`, `customers` e allineare `orders` con chiavi esterne `ON DELETE CASCADE`.

**CANTIERE ATTIVO (Obiettivo Prossima Sessione):**

- [x] Fix 422 Date Format (Backend Pydantic tollera e converte le date dal frontend).
- [x] Allineamento Split-Brain SQLite (Patch colonna customer_id applicata su orders locale).
- [x] TATTICA IMMINENTE 1: Amputati i ruderi geologici (Segreteria POS, Timeline, Lavagna) dal menù laterale frontend. Le rotte restano per backward-compatibility.
- [x] TATTICA IMMINENTE 2: Creato DeskBookingForm.vue (estratto da DeskDashboardPage). Innestato a Tabs nella RideDialog.vue (Omni-Board). CRM Silente attivo via POST /orders/desk. BUILD VERIFICATA ✅.
- [x] Emorragia Supabase "column orders.ride_date does not exist" curata con Inner Join PostgREST in calendar.py.
- [x] Fix Omni-Board 1: Passaggio corretto del Prezzo Unitario (unitPrice) per il calcolo del Totale nel Ledger. `localRide` convertito in `computed` reattivo con lookup `_getUnitPrice()` dal catalogo `store.activities`.
- [x] Fix Omni-Board 2: Reattività dell'evento emit('refresh') per mostrare immediatamente il nuovo ordine nel tab Ordini Esistenti. Distrutto il watcher snapshot, innestata Firma Operativa (activity+time) per transizione ghost→real.
- [x] Rianimazione Libro Mastro UI: Campi `paid_amount`→`price_paid`, `total_pax`→`pax` (chiavi fisiche Supabase). Lista transazioni iterata dinamicamente. Bottone PAGA cablato con `submitPayment()` → `POST /orders/{id}/transactions`.

**PROSSIMI PASSI (Priorità Critica):**

- [x] ~~**[CODICE ROSSO] RISOLUZIONE SPLIT-BRAIN DESK POS:**~~ ✅ COMPLETATO (27/02/2026). Sventrato `desk.py`, amputato SQLAlchemy, iniettato HTTPX nativo. Cerchio della Morte chiuso.
- [ ] Fix Allucinazione UI PlanningPage: Il denominatore delle card orario mostra la capacità TOTALE del motore (es. 48 pax) anziché quella RESIDUA. Valutare se il design voluto sia "booked / capacity" (attuale) o "booked / remaining".

---

## STORICO TRAGUARDI RAGGIUNTI (Fase 5 Completata):

1. Incenerito il vecchio Yield Engine V4 e le costanti temporali globali.
2. Implementato **Costruttore di Flussi a Mattoncini** in `SettingsPage.vue` (Libreria LocalStorage, Inserimento Pull a tendina, Giustificazione Flexbox Navetta).
3. Implementato **Yield Engine V5 e Scudo Anti-Ubiquità V5**: logica a scostamento cumulativo (ancoraggi `start`/`end`), normalizzazione tag, fallback monolitico per attività vergini.
4. Fix Reattività State Management: estirpato campo fossile "Tratti Fiume" e risolto il bug di desync (F5) sui Ghost Slots tramite l'helper `_isActivityClosedOnDate`.
5. Eseguita pulizia Supabase dai vecchi dati orfani (Split-Brain risolto).

## Debito Tecnico Pendente:

Nessuno critico. Solo pulizia di vecchi file di migrazione o commenti JSDoc obsoleti.

---

## BACKLOG (Idee in Stand-by post-Motore Predittivo):

Una volta blindato il Motore Logistico, si sceglierà la prossima direttrice:

- [ ] Opzione A: Timeline View (Visualizzazione grafica a Gantt nidificata Discese/Flussi/Blocchi) integrata come nuova rotta in Quasar.
- [ ] Opzione B: Modulo Presenze Giornaliere Staff.
- [ ] Opzione C: Flusso Prenotazioni CRM (Anagrafiche, Pagamenti).

- [x] TATTICA IMMINENTE 1 (Compartimento #1): Amputazione ruderi geologici completata. `ReservationsPage` (Prenotazioni), `BookingDialog` e `YieldSimulatorDialog` sono stati fisicamente eliminati e rimossi da router e layout.
- [x] TATTICA IMMINENTE 1.5 (Compartimento #2): Abortita amputazione (Falso Positivo UI). `ResourcesPage.vue` è un organo CRUD vitale. Emorragia Supabase su `calendar.py` curata tramite Inner Join PostgREST (`rides!inner(date)`).
