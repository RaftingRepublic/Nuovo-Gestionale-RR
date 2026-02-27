LORE VAULT - RAFTING REPUBLIC

Documento di Riferimento Supremo. Architettura, Lore e Scelte di Business consolidate.

Aggiornato a: Chiusura Fase 6.G — Build Verificata

🔴 MAPPA DEGLI ORGANI VITALI (L'Architettura Definitiva)

1. L'OMNI-BOARD (PlanningPage.vue + RideDialog.vue): L'Alfa e l'Omega. Il Calendario è l'hub visivo. La modale del turno fonde Logistica (Ordini Esistenti/Crew Builder) e Segreteria (Nuova Prenotazione/POS). Zero context-switching.

2. IL BRACCIO COMMERCIALE (DeskBookingForm.vue): Il componente POS estratto e incastonato nella modale. Gestisce Ledger Misto, Spacca-Conto e inietta nel CRM Silente.

3. IL LABORATORIO (SettingsPage.vue): Costruttore visivo a mattoncini (BPMN) per definire la "ricetta logistica" (Hard/Soft Limits) in formato JSON nativo.

4. IL REGISTRO ANAGRAFICO (ResourcesPage.vue): Interfaccia CRUD vitale per popolare il database locale (Staff, Brevetti, Furgoni, Ferie). NON TOCCARE.

5. IL MOTORE PREDITTIVO (Backend): Time-Array Slicer a 1440 minuti in Python. Lavora su SQLite per la logica spaziale e usa la Sync Sonda per contare i pax reali da Supabase.

6. IL CIMITERO: Le pagine "DeskDashboardPage" standalone, "ReservationsPage", "Timeline" e "Lavagna" sono obsolete/sepolte.

VISIONE ARCHITETTURALE: L'OMNI-BOARD (Zero Context Switching)

Abbandonata la separazione tra viste Logistica e Segreteria. Il "Calendario Operativo" è l'unico hub centrale. Le funzioni di Segreteria (prenotazioni, pagamenti, CRM) e Logistica (Crew Builder) COLLASSANO all'interno delle modali del Calendario. Zero context-switching.

LA FUSIONE ASSOLUTA (RideDialog come Hub): La modale del turno (RideDialog.vue) è l'interfaccia suprema a schede (Tabs). TRAPIANTO COMPLETATO.

- Tab "ORDINI ESISTENTI" (default): visualizzazione passeggeri, assegnazione risorse logistica, Libro Mastro, Drop-outs.
- Tab "NUOVA PRENOTAZIONE": Il form POS completo della Segreteria (DeskBookingForm.vue), con Ledger Misto, Spacca-Conto, Extra e CRM Silente. Il form riceve in automatico activity_id, date, time e unitPrice dal turno cliccato. Zero context-switching dal Calendario.
- DeskBookingForm.vue: componente estratto chirurgicamente da DeskDashboardPage.vue. Riceve le props dal ride cliccato, chiama POST /orders/desk (con CRM Silente backend già innestato), emette @success per ricaricare la vista.

1\. DOGMI ARCHITETTURALI E LIMITI FISICI (PROTOCOLLO LVE)

Hard Limit CloudLinux: Il server di produzione (Ergonet) ha un limite di ferro di 1GB RAM. È severamente vietato caricare interi dataset in memoria, usare ORM pesanti in loop o istanziare processi asincroni nativi voraci. Si usa passenger_wsgi e logica backend stateless ad array indexati.

Architettura Ibrida (Split-Brain Controllato):

SQLite (Locale): Catalogo deterministico. Single Source of Truth per activities, settings, staff, fleet.

Supabase (Cloud PostgreSQL): Registro operativo per i dati caldi (rides, orders, ride_allocations).

🚨 **Architettura Ibrida Desk POS (Scelta Consolidata 27/02/2026):** Risolto lo Split-Brain. Gli ordini, le transazioni (Libro Mastro) e gli Slot Fantasma vengono scritti ESCLUSIVAMENTE su Supabase via API PostgREST (`httpx`). Il Catalogo (`activities`) viene letto DA SQLITE LOCALE. I Turni (`rides`) subiscono un DUAL-WRITE per garantire l'integrità referenziale (stesso UUID in locale e in cloud). SQLAlchemy è DEPRECATO per la cassa.

No SQL Join per Logistica: Le policy coreografiche (guide minime, navetta, mezzi) sono un oggetto JSON (workflow_schema.logistics) in SQLite. La mappa dell'equipaggio (Guida + Gommone UUID + Passeggeri) sarà un JSONB nel metadata di ride_allocations in Supabase (Crew Builder Blueprint).

2\. MOTORE PREDITTIVO V5 E REGOLE DI BUSINESS

Time-Array Slicer (1440 min): Nessun calcolo basato su Datetime. Il giorno è un array di 1440 slot (minuti). Il motore attraversa i blocchi e "colora" i minuti occupati, verificando trasversalmente che il "Fondo del Sacco" non vada mai sotto zero.

Scostamento BPMN a Due Passaggi: I blocchi logistici si ancorano in avanti (anchor=start) o a ritroso (anchor=end).

Teorema del Sacco \& Eccezione di Sarre:

Hard Limits (Rosso): Guide e Gommoni/Carrelli. Se mancano nel minuto di incrocio, la capacità è ZERO. Vendite bloccate.

Soft Limits (Giallo / Sarre): Furgoni su tratte brevi. L'assenza di sedili fisici genera uno Yield Warning (Giallo) ma NON blocca mai le vendite. Si risolve con spola/loop.

Safety Kayak: Regola logica non lineare. Il floor minimo delle guide è calcolato come max(min_guides_absolute, needed_boats).

River Ledger (ARR Cascade): Posti vuoti galleggianti in discesa da monte (es. AD) diventano arr_bonus_seats a valle (es. CL, FA) prima di consumare nuova flotta ferma alla base.

3\. DIFESA FRONTEND E SENSORI

Sync Sonda (Bypass Split-Brain): FastAPI estrae i booked_pax reali dal cloud via HTTPX e li inietta nel Motore Predittivo locale come external_pax_map (Dependency Injection), disinnescando il bug "Zero Assoluto".

Merge Difensivo (Pinia): resource-store.js funge da Hydration Node. Incrocia la Verità Fisica (Supabase) con l'Intelligenza Predittiva. Se ci sono 0 posti calcolati ma prenotazioni cloud forzate, scatta il SafeStatus ROSSO (Kill-switch anti-overbooking).

Ghost Slots Dinamici: Creazione di slot virtuali nel calendario basati sui default_times SQLite.

4\. FUNZIONI E LOGICHE MORTE (CIMITERO DEL CODICE)

☠️ Yield Engine V4 e costanti temporali globali: Inceneriti.

☠️ Capienza 16 pax hardcoded: Rimossa dal Calendario Operativo.

☠️ Prop 'Tratti Fiume' in Vue: Estirpata. La logica dipende solo dal footprint logistico astratto.

☠️ Le vecchie interfacce "Segreteria (POS)", "Timeline Operativa" e "Lavagna Operativa" sono fossili geologici. Dichiarate morte e rimosse dal frontend visivo (sidebar). Le loro rotte possono restare per backward-compatibility ma NON devono avere alcuna voce nel menù.

☠️ TabOrdiniEsistenti Mockup (RideDialog.vue): Incenerito l'HTML statico del Libro Mastro. I campi `paid_amount` e `total_pax` (dialetto ORM locale SQLAlchemy) sono morti e sepolti, sostituiti definitivamente da `price_paid` e `pax` (chiavi fisiche Supabase). La lista transazioni è ora iterata dinamicamente da `order.transactions[]`, non più una riga hardcoded "SUMUP". Il bottone PAGA è vivo con `v-model` + `submitPayment()`.

☠️ Dati Transazionali in SQLite: Dichiarati obsoleti per i dati operativi. La cassa e la segreteria (Ordini e Transazioni) DEVONO vivere solo nel cloud (Supabase). SQLite resta ad uso esclusivo del Motore Predittivo (Availability Engine, Yield Engine) e del Catalogo BPMN (activities, workflow_schema, staff, fleet). Il router `desk.py` che scrive ordini in SQLite è marcato per sventramento (CODICE ROSSO).

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
