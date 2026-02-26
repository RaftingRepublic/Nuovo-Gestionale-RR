LORE VAULT - RAFTING REPUBLIC

Documento di Riferimento Supremo. Architettura, Lore e Scelte di Business consolidate.

Aggiornato a: Chiusura Fase 6.E



1\. DOGMI ARCHITETTURALI E LIMITI FISICI (PROTOCOLLO LVE)

Hard Limit CloudLinux: Il server di produzione (Ergonet) ha un limite di ferro di 1GB RAM. È severamente vietato caricare interi dataset in memoria, usare ORM pesanti in loop o istanziare processi asincroni nativi voraci. Si usa passenger\_wsgi e logica backend stateless ad array indexati.



Architettura Ibrida (Split-Brain Controllato):



SQLite (Locale): Catalogo deterministico. Single Source of Truth per activities, settings, staff, fleet.



Supabase (Cloud PostgreSQL): Registro operativo per i dati caldi (rides, orders, ride\_allocations).



No SQL Join per Logistica: Le policy coreografiche (guide minime, navetta, mezzi) sono un oggetto JSON (workflow\_schema.logistics) in SQLite. La mappa dell'equipaggio (Guida + Gommone UUID + Passeggeri) sarà un JSONB nel metadata di ride\_allocations in Supabase (Crew Builder Blueprint).



2\. MOTORE PREDITTIVO V5 E REGOLE DI BUSINESS

Time-Array Slicer (1440 min): Nessun calcolo basato su Datetime. Il giorno è un array di 1440 slot (minuti). Il motore attraversa i blocchi e "colora" i minuti occupati, verificando trasversalmente che il "Fondo del Sacco" non vada mai sotto zero.



Scostamento BPMN a Due Passaggi: I blocchi logistici si ancorano in avanti (anchor=start) o a ritroso (anchor=end).



Teorema del Sacco \& Eccezione di Sarre:



Hard Limits (Rosso): Guide e Gommoni/Carrelli. Se mancano nel minuto di incrocio, la capacità è ZERO. Vendite bloccate.



Soft Limits (Giallo / Sarre): Furgoni su tratte brevi. L'assenza di sedili fisici genera uno Yield Warning (Giallo) ma NON blocca mai le vendite. Si risolve con spola/loop.



Safety Kayak: Regola logica non lineare. Il floor minimo delle guide è calcolato come max(min\_guides\_absolute, needed\_boats).



River Ledger (ARR Cascade): Posti vuoti galleggianti in discesa da monte (es. AD) diventano arr\_bonus\_seats a valle (es. CL, FA) prima di consumare nuova flotta ferma alla base.



3\. DIFESA FRONTEND E SENSORI

Sync Sonda (Bypass Split-Brain): FastAPI estrae i booked\_pax reali dal cloud via HTTPX e li inietta nel Motore Predittivo locale come external\_pax\_map (Dependency Injection), disinnescando il bug "Zero Assoluto".



Merge Difensivo (Pinia): resource-store.js funge da Hydration Node. Incrocia la Verità Fisica (Supabase) con l'Intelligenza Predittiva. Se ci sono 0 posti calcolati ma prenotazioni cloud forzate, scatta il SafeStatus ROSSO (Kill-switch anti-overbooking).



Ghost Slots Dinamici: Creazione di slot virtuali nel calendario basati sui default\_times SQLite.



4\. FUNZIONI E LOGICHE MORTE (CIMITERO DEL CODICE)

☠️ Yield Engine V4 e costanti temporali globali: Inceneriti.



☠️ Capienza 16 pax hardcoded: Rimossa dal Calendario Operativo.



☠️ Prop 'Tratti Fiume' in Vue: Estirpata. La logica dipende solo dal footprint logistico astratto.

\[ARCHITETTURA UX E DEBITO GEOLOGICO]

Il Re Supremo è il Calendario: La direzione operativa ha decretato che l'unica interfaccia valida per unificare Segreteria e Logistica è il Calendario Operativo.



Il Cimitero dei Fossili: Le viste Segreteria (POS), Timeline Operativa e Lavagna Operativa sono ufficialmente dichiarate MORTE (strati geologici obsoleti e pericolosi).



Azione Architetturale: Il "CRM Silente" (salvataggio anagrafiche) e la gestione pagamenti devono essere sradicati dalla vecchia logica /desk e innestati chirurgicamente nella finestra Modale nativa del Calendario Operativo. Le voci dei ruderi andranno amputate dal menù laterale (MainLayout.vue o simili) per evitare lo Split-Brain dello staff.

\*\*\[EPITAFFIO ARCHITETTURALE - FASE 6.F] - ESTIRPAZIONE DEBITO GEOLOGICO (COMPARTIMENTO #1)\*\*

I file `ReservationsPage.vue`, `YieldSimulatorDialog.vue` e `BookingDialog.vue` sono stati dichiarati MORTI e rimossi fisicamente. La rotta `/prenotazioni` e la voce in sidebar sono state distrutte. L'interazione `onQuickBookFromMonth` nella `PlanningPage` naviga ora direttamente al giorno specifico, bypassando le vecchie modali dismesse. La `RideDialog` nativa si conferma come l'unica interfaccia operativa autorizzata per la gestione e la cassa.

