LORE VAULT - RAFTING REPUBLIC

Documento di Riferimento Supremo. Architettura, Lore e Scelte di Business consolidate.

Aggiornato a: Chiusura Fase 9 — OrderDB Amputata, Cablaggio HTTPX Supabase (27/02/2026 23:55)

🔴 MAPPA DEGLI ORGANI VITALI (L'Architettura Definitiva)

1. L'OMNI-BOARD (PlanningPage.vue + RideDialog.vue): L'Alfa e l'Omega. Il Calendario è l'hub visivo. La modale del turno fonde Logistica (Ordini Esistenti/Crew Builder) e Segreteria (Nuova Prenotazione/POS). Zero context-switching.

2. IL BRACCIO COMMERCIALE (DeskBookingForm.vue): Il componente POS estratto e incastonato nella modale. Gestisce Ledger Misto, Spacca-Conto e inietta nel CRM Silente.

3. IL LABORATORIO (SettingsPage.vue): Costruttore visivo a mattoncini (BPMN) per definire la "ricetta logistica" (Hard/Soft Limits) in formato JSON nativo.

4. IL REGISTRO ANAGRAFICO (ResourcesPage.vue): Interfaccia CRUD vitale per popolare il database locale (Staff, Brevetti, Furgoni, Ferie). NON TOCCARE.

5. IL MOTORE PREDITTIVO (Backend): Time-Array Slicer a 1440 minuti in Python. Lavora su SQLite per la logica spaziale e usa la Sync Sonda per contare i pax reali da Supabase.

6. LA TIMELINE FLUSSI (TimelinePage.vue — 27/02/2026): Vista Gantt con toggle Discese/Ruoli. La Vista Ruoli applica un algoritmo di Multi-Lane Packing per visualizzare sovrapposizioni temporali. Barra di Saturazione a 144 bucket (5 min ciascuno, 08:00-20:00) con colori verde/giallo/rosso. Navigazione bidirezionale con PlanningPage tramite bottoni "Timeline Flussi" e "Torna al Giorno" (preserva data via store centralizzato).

7. IL CIMITERO: Le pagine "DeskDashboardPage" standalone, "ReservationsPage" e "Lavagna" sono obsolete/sepolte. La "Timeline" è stata RESUSCITATA il 27/02/2026 come Vista Ruoli integrata nel workflow operativo.

VISIONE ARCHITETTURALE: L'OMNI-BOARD (Zero Context Switching)

Abbandonata la separazione tra viste Logistica e Segreteria. Il "Calendario Operativo" è l'unico hub centrale. Le funzioni di Segreteria (prenotazioni, pagamenti, CRM) e Logistica (Crew Builder) COLLASSANO all'interno delle modali del Calendario. Zero context-switching.

LA FUSIONE ASSOLUTA (RideDialog come Hub): La modale del turno (RideDialog.vue) è l'interfaccia suprema a schede (Tabs). TRAPIANTO COMPLETATO.

- Tab "ORDINI ESISTENTI" (default): visualizzazione passeggeri, assegnazione risorse logistica, Libro Mastro, Drop-outs.
- Tab "NUOVA PRENOTAZIONE": Il form POS completo della Segreteria (DeskBookingForm.vue), con Ledger Misto, Spacca-Conto, Extra e CRM Silente. Il form riceve in automatico activity_id, date, time e unitPrice dal turno cliccato. Zero context-switching dal Calendario.
- DeskBookingForm.vue: componente estratto chirurgicamente da DeskDashboardPage.vue. Riceve le props dal ride cliccato, chiama POST /orders/desk (con CRM Silente backend già innestato), emette @success per ricaricare la vista.
- Semaforo Manuale (RideDialog Header): Bottoni VERDE/BLU/GIALLO/ROSSO/AUTO con Dual-Write Supabase+SQLite. Bottone "CHIUDI TURNO" visibile se booked_pax=0.

1\. DOGMI ARCHITETTURALI E LIMITI FISICI (PROTOCOLLO LVE)

Hard Limit CloudLinux: Il server di produzione (Ergonet) ha un limite di ferro di 1GB RAM. È severamente vietato caricare interi dataset in memoria, usare ORM pesanti in loop o istanziare processi asincroni nativi voraci. Si usa passenger_wsgi e logica backend stateless ad array indexati.

Architettura Ibrida (Split-Brain Controllato):

SQLite (Locale): Catalogo deterministico. Single Source of Truth per activities, settings, staff, fleet.

Supabase (Cloud PostgreSQL): Registro operativo per i dati caldi (rides, orders, ride_allocations).

🚨 **Architettura Ibrida Desk POS (Scelta Consolidata 27/02/2026):** Risolto lo Split-Brain. Gli ordini, le transazioni (Libro Mastro) e gli Slot Fantasma vengono scritti ESCLUSIVAMENTE su Supabase via API PostgREST (`httpx`). Il Catalogo (`activities`) viene letto DA SQLITE LOCALE. I Turni (`rides`) subiscono un DUAL-WRITE per garantire l'integrità referenzionale (stesso UUID in locale e in cloud). SQLAlchemy è DEPRECATO per la cassa.

No SQL Join per Logistica: Le policy coreografiche (guide minime, navetta, mezzi) sono un oggetto JSON (workflow_schema.logistics) in SQLite. La mappa dell'equipaggio (Guida + Gommone UUID + Passeggeri) sarà un JSONB nel metadata di ride_allocations in Supabase (Crew Builder Blueprint).

🔴 DOGMA DDL SUPABASE: Qualsiasi alterazione strutturale alle tabelle in Cloud richiede TASSATIVAMENTE l'esecuzione del comando SQL NOTIFY pgrst, 'reload schema'; come ultima riga dello script per svuotare la cache API. Il Tech Lead ha storicamente allucinato questo passaggio causando l'errore PGRST204 e accusando il PM. Mai dare per scontato che l'istruzione sia presente: verificare sempre fisicamente la riga nello script.

🔒 DOGMA DELL'OVERRIDE (27/02/2026): Se la colonna `is_overridden` è `True` nella tabella `daily_rides`, l'Availability Engine ha l'ordine tassativo di NON ricalcolare lo stato del turno, rispettando la scelta manuale della Segreteria. Il bypass avviene nel Pass 1 (`calculate_availability`): il motore restituisce direttamente lo status salvato nel DB (A→VERDE, B→GIALLO, C→ROSSO, D→BLU) e salta Pass 2. Il Kill-Switch client in `resource-store.js` rispetta il flag e non sovrascrive lo status forzato. Unica via per tornare al calcolo automatico: premere il bottone AUTO, che imposta `is_overridden=False`.

🔴 **DOGMA 12 — CHIAVI LOGICHE CROSS-DATABASE (Regola Anti-FK Split-Brain, 27/02/2026):**

Le chiavi esterne in Supabase che puntano a entità del Catalogo Locale (es. `resource_id` in `ride_allocations` verso `staff`/`fleet`) NON DEVONO avere vincoli fisici (`FOREIGN KEY` constraints). Devono essere **UUID liberi (Chiavi Logiche)**, validati solo a livello applicativo. Altrimenti il database cloud andrà in conflitto con SQLite, generando errori `409 Conflict` (`23503 foreign_key_violation`). Il vincolo `ride_allocations_resource_id_fkey` è stato amputato il 27/02/2026 dopo che il Crew Builder falliva silenziosamente al salvataggio. Regola aurea: se l'entità referenziata vive nell'altro database, il link è LOGICO, mai FISICO.

⚠️ **COROLLARIO — Sindrome dell'Arto Fantasma (27/02/2026):** Se una Foreign Key fisica viene amputata in cloud per rispettare lo Split-Brain, TUTTE le query frontend PostgREST (es. `supabase.from('...').select('..., entita_esterna(*)')`) devono essere epurate dalle JOIN esplicite verso l'entità scollegata. Altrimenti Supabase restituirà un errore bloccante `PGRST200` (Bad Request) mandando in crash l'interfaccia. Primo caso: `resources(*)` amputato da `resource-store.js` nelle funzioni `fetchDailySchedule` e `fetchMonthOverview` (27/02/2026).

2\. MOTORE PREDITTIVO V5 E REGOLE DI BUSINESS

Time-Array Slicer (1440 min): Nessun calcolo basato su Datetime. Il giorno è un array di 1440 slot (minuti). Il motore attraversa i blocchi e "colora" i minuti occupati, verificando trasversalmente che il "Fondo del Sacco" non vada mai sotto zero.

Scostamento BPMN a Due Passaggi: I blocchi logistici si ancorano in avanti (anchor=start) o a ritroso (anchor=end).

Teorema del Sacco \& Eccezione di Sarre:

Hard Limits (Rosso): Guide e Gommoni/Carrelli. Se mancano nel minuto di incrocio, la capacità è ZERO. Vendite bloccate.

Soft Limits (Giallo / Sarre): Furgoni su tratte brevi. L'assenza di sedili fisici genera uno Yield Warning (Giallo) ma NON blocca mai le vendite. Si risolve con spola/loop.

Safety Kayak: Regola logica non lineare. Il floor minimo delle guide è calcolato come max(min_guides_absolute, needed_boats).

🚫 Formula Furgoni Deterministica (27/02/2026): La capacità dei mezzi viene calcolata come `math.ceil(booked_pax / van_net_seats)`. È VIETATO l'uso di margini di sicurezza (`+1`) che alterano la percezione della disponibilità reale e generano falsi Yield Warning (Giallo Perenne). Il bug del "Passeggero Fantasma" è stato scoperto e corretto nella sessione del 27/02/2026.

River Ledger (ARR Cascade): Posti vuoti galleggianti in discesa da monte (es. AD) diventano arr_bonus_seats a valle (es. CL, FA) prima di consumare nuova flotta ferma alla base.

3\. DIFESA FRONTEND E SENSORI

Sync Sonda (Bypass Split-Brain): FastAPI estrae i booked_pax reali dal cloud via HTTPX e li inietta nel Motore Predittivo locale come external_pax_map (Dependency Injection), disinnescando il bug "Zero Assoluto".

Merge Difensivo (Pinia): resource-store.js funge da Hydration Node. Incrocia la Verità Fisica (Supabase) con l'Intelligenza Predittiva. Se ci sono 0 posti calcolati ma prenotazioni cloud forzate, scatta il SafeStatus ROSSO (Kill-switch anti-overbooking). Il kill-switch client è DISATTIVATO per i turni con `is_overridden=True`.

Ghost Slots Dinamici: Creazione di slot virtuali nel calendario basati sui default_times SQLite.

4\. FUNZIONI E LOGICHE MORTE (CIMITERO DEL CODICE)

☠️ Yield Engine V4 e costanti temporali globali: Inceneriti.

☠️ Capienza 16 pax hardcoded: Rimossa dal Calendario Operativo.

☠️ Prop 'Tratti Fiume' in Vue: Estirpata. La logica dipende solo dal footprint logistico astratto.

☠️ Le vecchie interfacce "Segreteria (POS)", "Timeline Operativa" e "Lavagna Operativa" sono fossili geologici. Dichiarate morte e rimosse dal frontend visivo (sidebar). Le loro rotte possono restare per backward-compatibility ma NON devono avere alcuna voce nel menù.

☠️ TabOrdiniEsistenti Mockup (RideDialog.vue): Incenerito l'HTML statico del Libro Mastro. I campi `paid_amount` e `total_pax` (dialetto ORM locale SQLAlchemy) sono morti e sepolti, sostituiti definitivamente da `price_paid` e `pax` (chiavi fisiche Supabase). La lista transazioni è ora iterata dinamicamente da `order.transactions[]`, non più una riga hardcoded "SUMUP". Il bottone PAGA è vivo con `v-model` + `submitPayment()`.

☠️ Dati Transazionali in SQLite: Dichiarati obsoleti per i dati operativi. La cassa e la segreteria (Ordini e Transazioni) DEVONO vivere solo nel cloud (Supabase). SQLite resta ad uso esclusivo del Motore Predittivo (Availability Engine, Yield Engine) e del Catalogo BPMN (activities, workflow_schema, staff, fleet). Il router legacy `orders.py` (endpoint `/api/v1/legacy-orders`) è stato **incenerito fisicamente** il 27/02/2026 (Fase 8 DT-5). Le classi `CustomerDB` e `TransactionDB` sono state amputate. La tabella `orders` SQLite è stata AMPUTATA e DROPpata nella Fase 9.A. La classe `OrderDB` è stata eliminata fisicamente. `RegistrationDB.order_id` è ora una stringa orfana (UUID Supabase).

☠️ Cimitero Backend (Fase 8, 27/02/2026): Router `orders.py` eliminato. Classi `CustomerDB`, `TransactionDB` distrutte dal modello. Schemi Pydantic `OrderCreate`, `OrderResponse` rimossi. Le funzioni helper `calculate_booked_pax` e `recalculate_ride_status` sono state estratte nel modulo `app/services/ride_helpers.py` (pattern di micro-servizio). Tabelle fisiche `transactions` e `customers` DROPpate da `rafting.db` via script monouso.

☠️ Sindrome UUID Visuale (Fase 8, 27/02/2026): Curata la visualizzazione di UUID raw nei mattoncini del calendario mensile. Template `assigned_staff`/`assigned_fleet` (vestigia FK SQLite) rimosso da PlanningPage. I commenti legacy su FK morte e TODO superati sono stati epurati dal frontend.

\[ARCHITETTURA UX E DEBITO GEOLOGICO]

Il Re Supremo è il Calendario: La direzione operativa ha decretato che l'unica interfaccia valida per unificare Segreteria e Logistica è il Calendario Operativo.

Il Cimitero dei Fossili: Le viste Segreteria (POS), Timeline Operativa e Lavagna Operativa sono ufficialmente dichiarate MORTE (strati geologici obsoleti e pericolosi).

Azione Architetturale: Il "CRM Silente" (salvataggio anagrafiche) e la gestione pagamenti devono essere sradicati dalla vecchia logica /desk e innestati chirurgicamente nella finestra Modale nativa del Calendario Operativo. Le voci dei ruderi andranno amputate dal menù laterale (MainLayout.vue o simili) per evitare lo Split-Brain dello staff.

\*\*\[EPITAFFIO ARCHITETTURALE - FASE 6.F] - ESTIRPAZIONE DEBITO GEOLOGICO (COMPARTIMENTO #1)\*\*

I file `ReservationsPage.vue`, `YieldSimulatorDialog.vue` e `BookingDialog.vue` sono stati dichiarati MORTI e rimossi fisicamente. La rotta `/prenotazioni` e la voce in sidebar sono state distrutte. L'interazione `onQuickBookFromMonth` nella `PlanningPage` naviga ora direttamente al giorno specifico, bypassando le vecchie modali dismesse. La `RideDialog` nativa si conferma come l'unica interfaccia operativa autorizzata per la gestione e la cassa.

\*\*\[SALVACONDOTTO - ResourcesPage.vue]\*\*

ResourcesPage.vue è un'interfaccia CRUD vitale per popolare il database locale SQLite (staff, mezzi) e NON deve essere toccata. Tentativo di amputazione abortito il 26/02/2026 (Falso Positivo UI). Il file resta nella sidebar sotto "Staff & Risorse".

\*\*\[CURA EMORRAGIA - Sync Sonda calendar.py]\*\*

L'errore Supabase "column orders.ride_date does not exist" è stato curato nella funzione `_fetch_supabase_pax` (riga 200 di calendar.py). La query REST ora usa un Inner Join PostgREST (`rides!inner(date)`) per filtrare gli ordini per data attraverso la relazione `orders → rides`, anziché cercare una colonna inesistente `ride_date` nella tabella `orders`.

**[SIGILLO FASE 6 — COMPLETATA (27/02/2026)]**

**FASE 6 COMPLETATA (Logistica Fluidodinamica e POS Ibrido)**

- Split-Brain POS polverizzato tramite architettura Ibrida (Dual-Write SQLite/Supabase) e Sync Sonda (httpx).
- Motore Predittivo stabilizzato con Teorema del Sacco (Hard/Soft limits) ed Eccezione di Sarre.
- Collisione di routing disinnescata (isolamento backend legacy).
- Variabili logistiche operative idratate nativamente su system_settings (SQLite).
- Spurgo Sentina completato: 9 file orfani inceneriti, fossile DeskDashboardPage.vue distrutto.
- Timeline Flussi (Gantt) operativa con Vista Ruoli, Multi-Lane Packing e Barra Saturazione.
- Drag & Drop blocchi BPMN innestato nel Costruttore di Flussi.

**[SIGILLO FASE 7.A — COMPLETATA (27/02/2026)]**

**FASE 7.A COMPLETATA (Scaffold Tubature Crew Builder)**

- Implementata API Backend (GET/PUT `/api/v1/crew/allocations`) per gestire la "Busta Stagna" (metadata JSONB) via httpx su Supabase.
- Interfaccia Scaffoldata: Creato `CrewBuilderPanel.vue` (layout a due colonne: Passeggeri vs Flotta) e innestato come tab "Equipaggi" nell'Omni-Board (`RideDialog.vue`).

**[SIGILLO FASE 7.B — COMPLETATA (27/02/2026)]**

**FASE 7.B COMPLETATA (Fondazione Busta Stagna)**

- DDL Supabase: Script idempotente per `ride_allocations` (colonna `metadata` JSONB, indici `ride_id` e `resource_type`, RLS policy, NOTIFY pgrst). Da eseguire manualmente nel SQL Editor.
- Nastro Trasportatore Pinia: Creato `crew-store.js` con state (`allocations`, `isLoading`), getter (`boatCount`, `assignedPax`, `unassignedPax`, `isEmpty`), e actions (`loadCrew(ride_id)` via GET, `saveCrew(ride_id, payload)` via PUT, `clearCrew()`). Comunicazione via Axios verso backend FastAPI.

**[SIGILLO FASE 7.C — COMPLETATA (27/02/2026)]**

**FASE 7.C COMPLETATA (Banchina d'Imbarco UI)**

- `CrewBuilderPanel.vue` ricostruito con righe dinamiche [Gommone q-select] + [Guida q-select] + [Pax q-input]. Zona Banchina con contatori pax paganti/imbarcati/in attesa e allarme over-assegnazione. Pulsante "SIGILLA EQUIPAGGI". Cablato al crew-store con onMounted + watch reattivo.

🔴 **DOGMA 10 — TETRIS UMANO (Manifesto d'Imbarco Nominale, 27/02/2026):**

Nel Crew Builder, i passeggeri non sono MAI numeri anonimi. La Busta Stagna (`ride_allocations.metadata`) per i gommoni DEVE contenere un array `groups: [{ order_id: UUID, customer_name: string, pax: int }]`. Non si imbarcano numeri assoluti, si imbarcano **frazioni di ordini**. Il totale passeggeri di un gommone è sempre la somma derivata dei `pax` nel suo array `groups`. Un maxi-ordine (es. 40 pax) può essere frammentato su più gommoni mantenendo il nome del referente per l'appello sul molo.

**[SIGILLO FASE 7.C.2 — COMPLETATA (27/02/2026)]**

**FASE 7.C.2 COMPLETATA (Tetris Umano — Busta Stagna Nominale)**

- Refactoring metadata gommone: rimosso `pax_count` anonimo, sostituito con `groups: [{ order_id, customer_name, pax }]`.
- Zona Banchina: ordini con conteggio pax residui in tempo reale (`getRemainingPax`). Badge verde/arancione per ordini completati/in attesa.
- Zona Fiume: ogni gommone mostra i gruppi imbarcati nominali con pax editabile. Select "Aggiungi Gruppo" filtra solo ordini con pax residui > 0.

🔴 **DOGMA 11 — SWAP & REPLACE (Regola dell'Aggiornamento Massivo, 27/02/2026):**

L'aggiornamento massivo di entità figlie e complesse (come gli equipaggi) si fa radendo al suolo i vecchi record (`DELETE` per `ride_id`) e bulk-inserendo i nuovi (`POST`). Zero orfani, zero lookup di differenza. Se devi aggiornare, distruggi e ricostruisci. Il vincolo FK `ON DELETE CASCADE` protegge l'integrità referenziale.

**[SIGILLO FASE 7.D — COMPLETATA (27/02/2026)]**

**FASE 7.D COMPLETATA (Allineamento Valvola Backend)**

- Fix 422: Schemi Pydantic allineati al Tetris Umano (`CrewGroup`, `CrewMetadata`, `CrewAllocationItem`). PUT accetta `List[CrewAllocationItem]` direttamente.
- Tecnica Swap & Replace implementata: DELETE vecchi crew_manifest per ride_id + bulk INSERT nuovi via httpx PostgREST.
- GET restituisce `{ ride_id, allocations: [...] }` (array piatto). Store frontend allineato: `saveCrew` invia array diretto, `loadCrew` legge da `data.allocations`.
- Rimosso dump errore raw dalla UI. Notifiche Quasar position=top per success/error.

🔴 **DOGMA 13 — KILL-SWITCH DEL VARO (Bilancia Banchina, 27/02/2026):**

L'interfaccia UI (CrewBuilderPanel.vue) DEVE inibire fisicamente il salvataggio API se: A) Un mezzo fisico supera la sua `capacity` (Sensore di Galleggiamento — incrocio `resource_id` con `fleetList`). B) I passeggeri imbarcati superano quelli paganti dell'ordine (Niente fantasmi gratis — Sovra-assegnazione). I salvataggi in difetto (imbarcati < paganti) sono invece AMMESSI per tollerare i no-show fisici al molo. Il bottone "SIGILLA EQUIPAGGI" cambia colore a grigio e mostra un tooltip rosso con il motivo del blocco. La computed property `isVaroBloccato` nel componente e il getter `hasAnyOverflow` nello store governano la logica.

**[SIGILLO FASE 7.E — COMPLETATA (27/02/2026)]**

**FASE 7.E COMPLETATA (Sensori di Galleggiamento e Bilancia Banchina)**

- Bilancia Banchina: q-banner reattivo a 3 stati nella Zona Banchina (🚨 Rosso fantasmi / ⚠️ Arancione molo / ✅ Verde bilancio perfetto).
- Sensore di Galleggiamento: card gommone con bordi, sfondo e badge dinamici. Incrocio `resource_id` con `fleetList` per `capacity` fisica. Stati: overflow (rosso), pieno (verde), liberi (blu), sconosciuto (default).
- Kill-Switch Varo: bottone SIGILLA EQUIPAGGI bloccato se overflow O sovra-assegnazione, con tooltip motivo blocco.
- Getter `hasAnyOverflow` aggiunto al `crew-store.js` come funzione factory cross-store.
- Pompa di Sentina: script `purge_bilge.py` eseguito e poi smantellato. 0 record orfani trovati.
- Collaudo E2E confermato dal PM.

**[SIGILLO FASE 7 — COMPLETATA (27/02/2026 21:46)]**

**FASE 7 COMPLETATA (Crew Builder — Lavagna d'Imbarco Digitale)**

Il Crew Builder è operativo e collaudato. Dalla Fase 7.A alla 7.E: scaffold backend/frontend, DDL Supabase, store Pinia, UI a righe dinamiche (Tetris Umano nominale), allineamento Pydantic, Swap & Replace, fix JWT/FK/PGRST200, sensori di galleggiamento, bilancia banchina, kill-switch varo e purge sentina. L'intera Fase 7 è stata completata nella sessione unica del 27/02/2026.

**[SIGILLO FASE 8 — COMPLETATA (27/02/2026 23:10)]**

**FASE 8 COMPLETATA (Smaltimento Debito Tecnico — Operazione Spurgo Sentina)**

Debito tecnico azzerato. 6 task completati (DT-1 → DT-6). Zero warning FastAPI, zero import orfani, zero classi morte, zero commenti obsoleti. Il backend riparte pulito con soli i modelli necessari a sostenere l'architettura ibrida SQLite/Supabase fino alla migrazione finale di `OrderDB` (Fase 9).

🔴 **DOGMA 14 — WALKIE-TALKIE HTTPX (Disconnessione Totale SQLite↔Transazioni, 27/02/2026):**

La classe `OrderDB` (SQLAlchemy) è stata AMPUTATA fisicamente. La tabella `orders` è stata DROPpata da SQLite. I dati transazionali (ordini, transazioni, registrazioni cloud, clienti) vivono ESCLUSIVAMENTE su Supabase. Il backend li accede via `httpx.AsyncClient` attraverso il modulo radio `app/services/supabase_bridge.py` (3 funzioni async difensive: `fetch_orders_by_ride`, `fetch_order_by_id`, `fetch_pax_by_rides`). Il campo `RegistrationDB.order_id` in SQLite è ora una stringa orfana (UUID Supabase) senza FK fisico. L'integrità referenziale è LOGICA, non FISICA. Se Supabase (Francoforte) ha un singhiozzo, le funzioni restituiscono `[]` o `None` senza crashare il server.

🔴 **DOGMA 15 — MASCHERAMENTO NIMITZ (Soglia Capacità Logistica, 27/02/2026):**

Le attività senza vincoli logistici (nessun `workflow_schema.logistics`) producono capacità astronomiche dal Motore Predittivo (es. 7992 pax). Nessun operatore deve mai vedere questi numeri. La soglia NIMITZ è fissata a 1000: se `total_capacity >= 1000`, il frontend NASCONDE il denominatore (`/ 7992`), i "posti residui" e la barra di progresso. Mostra SOLO i passeggeri confermati: "X pax confermati". Applicato in `PlanningPage.vue` (card turno + helper `isNimitz()`) e `RideDialog.vue` (header badge + banner Engine).

🔴 **DOGMA 16 — SINDROME UUID (Mismatch Tipo Chiave Cross-Database, 28/02/2026):**

In Python, un UUID object di SQLAlchemy (`uuid.UUID('...')`) NON matcha MAI una stringa Supabase (`"..."`) quando usato come chiave di dizionario. `dict.get(UUID('abc'), 0)` su un dict con chiavi `str` restituisce SEMPRE 0 silenziosamente. Regola aurea: usare TASSATIVAMENTE `str(ride.id)` prima di accedere a qualsiasi dizionario popolato da fetch esterni (Sonda Supabase, `external_pax_map`, `real_pax_map`). Strato difensivo nei router: se `remaining_seats == total_capacity` E `booked_pax > 0`, l'Engine ha ignorato i pax → forzare `remaining_seats = max(0, total_capacity - booked_pax)`. Strato difensivo nel frontend: calcolo deterministico `Math.max(0, cap - pax)` in-template, MAI fidarsi ciecamente del campo `remaining_seats` del backend.

🔴 **DOGMA 17 — DIVIETO ASSOLUTO httpx.Client SINCRONO (Thread FastAPI, 28/02/2026):**

È SEVERAMENTE VIETATO istanziare `httpx.Client()` (sincrono) nel thread principale di un endpoint FastAPI. FastAPI gira su un event loop async (uvicorn); una chiamata HTTP bloccante congestiona il worker e provoca timeout a cascata per tutti gli utenti. L'unica eccezione tollerata è la Sync Sonda legacy (`_fetch_supabase_pax` in `calendar.py`) che opera in un endpoint `def` sincrono (non `async def`). Per qualsiasi altro caso usare `httpx.AsyncClient` in endpoint `async def`, oppure delegare a `run_in_executor`. Mai — in nessun caso — mettere `httpx.Client` in un helper importato globalmente (come `ride_helpers.py`): verrebbe invocato ad ogni request.

**[SIGILLO FASE 9 — COMPLETATA E SIGILLATA (28/02/2026 00:15)]**

**FASE 9 COMPLETATA (Migrazione OrderDB a Supabase — Amputazione + Cablaggio HTTPX + Hotfix Matematici)**

- **9.A (Amputazione):** Classe `OrderDB` eliminata. FK `orders.id` recisa da `RegistrationDB`. Tabella `orders` DROPpata da `rafting.db`. Tutti i `joinedload` e import epurati. Export FIRAFT riscritta con JOIN diretto `daily_ride_id`.
- **9.B (Cablaggio):** Modulo radio `supabase_bridge.py` creato. Matrioska cablata a Supabase. Daily-schedule popolato via `fetch_pax_by_rides`. Public API Kiosk validata su Supabase Cloud. Schema Pydantic `orders: List[dict]`.
- **9.Fix (Pallottoliere + Nimitz + Sindrome UUID):** Soglia NIMITZ applicata al frontend. `ride_helpers.py` epurato da httpx sincrono (Dogma 17). Strato difensivo matematico nei router: `remaining_seats = max(0, total_cap - booked_pax)` quando Engine ignora i pax. Frontend blindato: `getRemainingSeats()` e banner Omni-Board ora deterministici (`cap - pax`), mai fidarsi del backend. Dogma 16 (Sindrome UUID) e Dogma 17 (Divieto httpx sincrono) sanciti.
- L'architettura ibrida è ora cristallizzata: SQLite = Catalogo + Motore, Supabase = Transazioni + CRM.

🔴 **DOGMA 18 — LA GRAFFETTATRICE (Anti-Ordini Orfani, 28/02/2026):**

Nessun ordine commerciale può essere inviato a Supabase senza prima aver creato il cliente, estrapolato il suo ID e iniettato il `customer_id` associato nel payload. Il POS locale non deve mai generare tuple orfane in cloud. La sequenza obbligatoria è: (1) UPSERT customers → (2) Estrai `customer_id` dalla risposta (header `Prefer: return=representation`) → (3) INSERT orders con `customer_id` valorizzato. Un ordine senza `customer_id` è un animale ferito che non potrà mai essere rintracciato dal CRM, dal Fascicolo Cliente o dalla Leva dello Strozzino nella CassaPage.

**[SIGILLO FASE 10.A-D — IN CORSO (28/02/2026 01:23)]**

**FASE 10 IN CORSO (Il Mangiasoldi — Cassa & CRM)**

- Inceneritore Debito Tecnico: `reservations.py`, `yield_engine.py` e `availability.py` (guscio) eliminati/decablati. TECH_ARCHITECTURE aggiornata.
- CassaPage.vue operativa: 3 cassetti finanziari (CASH/POS/TRANSFER), Anagrafica clienti con drill-down, Fascicolo storico ordini con semaforo debiti, Leva dello Strozzino (incasso diretto da fascicolo).
- Spia Check Engine installata: error handling rumoroso nel fascicolo cliente.
- Dogma 18 (La Graffettatrice) sancito. Pipeline CRM desk.py verificata e conforme.
