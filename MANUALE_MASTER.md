TITOLO: Manuale Operativo e Logistico MASTER - Rafting Republic
SCOPO: Regole fisiche, spaziali e logiche di business per lo Yield Engine, Simulatore e Assegnazioni.

=== SEZIONE 0: VARIABILI DINAMICHE (PANNELLO VARIABILI) ===
REGOLA FONDAMENTALE SUPREMA: Nessun tempo in minuti (es. durata briefing, tempi di viaggio, discesa) o capienza mezzi (es. posti furgone) deve MAI essere hardcodato nel codice Python.
Lo Yield Engine DEVE SEMPRE interrogare il database SQLite (tabella settings/impostazioni generata dal Pannello Variabili dell'utente) per ottenere questi valori in tempo reale.
Chiavi da usare dal DB: `van_total_seats`, `van_driver_seats`, `van_guide_seats`, `briefing_duration_min`, `a_prep_ti_im_min`, `a_river_min`, `a_transfer_sb_to_imb_min`, `a_return_to_base_min`, `b_river_min`, ecc.

=== SEZIONE 1: MATRICE ATTIVITÀ E TRATTI FIUME ===

- AD (Rafting Advanced): Tratti navigati A + B + C
- CL (Rafting Classic): Tratti navigati B + C
- SL (Rafting Selection): Tratto navigato A
- FA (Rafting Family): Tratto navigato C
- HYD (Hydrospeed Base): Tratto navigato C

=== SEZIONE 2: REGOLE LOGICHE E OROLOGI (ACQUA vs TERRA) ===

1. TEMPI BASE AL CENTRO RAFTING (CR):
   Prima di partire, i clienti fanno Accoglienza, Briefing e Vestizione. La durata si ottiene leggendo la variabile `briefing_duration_min` (e affini) dal DB.
2. BUFFER ZERO (Acqua): Il tempo di recupero tra due turni per guide e gommoni è ZERO. Le risorse in acqua sono bloccate in modo continuo [Start -> End].
3. OROLOGIO TERRA E LA "NAVETTA ELASTICA":
   - SCENARIO TRATTO "A" (Ammiraglia): Se l'attività tocca il Tratto A (es. AD, SL), il furgone va allo sbarco e ASPETTA. Occupazione CONTINUA e RIGIDA.
   - SCENARIO TRATTI "B" e "C" (Navetta Elastica): Se l'attività tocca SOLO B e/o C (es. CL, FA), il furgone fa Drop-off all'imbarco, TORNA AL CENTRO BASE (tornando Libero per incroci), e poi fa Pick-up allo sbarco.
     ATTENZIONE: La durata del blocco di andata (Drop-off) e del blocco di ritorno (Pick-up) NON è fissa a 30 min, ma va calcolata sommando dinamicamente i tempi di percorrenza stradale (TI, TS) e sosta (IM, SB) letti dal DB per il tratto specifico.

=== SEZIONE 3: TEMPISTICHE STRADALI (ST) ===
I tempi di Trasporto Imbarco (TI), Trasporto Sbarco (TS) e le soste fisse (IM, SB) devono essere estrapolati in tempo reale dal database:

- TRATTO A (Bomb): Usa `a_prep_ti_im_min`, `a_transfer_sb_to_imb_min`, `a_return_to_base_min`.
- TRATTO B (Leve): Usa le rispettive variabili per il tratto B (es. `b_river_min`).
- TRATTO C (Chavo): Usa le rispettive variabili per il tratto C.

=== SEZIONE 4: REGOLE DI INCROCIO MULTIPLO (ARR) ===
REGOLA AUREA: Per usare lo stesso furgone su più discese, la discesa PIÙ LUNGA deve SEMPRE iniziare PRIMA della più corta.
Gli offset e i gap temporali tra le discese (es. AD -> CL) non sono hardcodati, ma verranno verificati matematicamente dall'algoritmo usando le finestre temporali generate dai tempi del DB.

=== SEZIONE 5: MATRICE COMPETENZE RIGIDE (GUIDE E MEZZI) ===

1. REGOLE GUIDE RAFTING:
   - Tratto A e Tratto B: Richiedono TASSATIVAMENTE brevetto 'RAF4'. (Una guida RAF3 NON può condurre qui).
   - Tratto C: Ammesso brevetto 'RAF3' (Il RAF4 è valido per downgrade).
   - Specialità Safety Kayak (SK): Eredita il livello Rafting.
2. REGOLE GUIDE HYDROSPEED:
   - Ammesse SOLO guide con brevetti: 'HYD', 'SH', 'SK', 'CB'. (Escluse RAF4, RAF3 puramente raft).
3. REGOLE AUTISTI E MEZZI:
   - Autisti: N (Navettista Base), C (Guida Carrello), F (Fa Foto). Combinabili. Per trainare, serve 'C'.
   - Carrelli (CR): Capienza MAX RIGOROSA 5 gommoni di qualsiasi tipo.
   - Gommoni: L (capienza 8 pax trasportati), M o S (capienza 6 pax).
     === SEZIONE 6: ECCEZIONI LOGISTICHE E IBRIDI (LA REGOLA DELLA LAVAGNA) ===
4. SNAVETTAMENTO (Cross-Role): Una risorsa 'Guida' (es. RAF4, RAF3) può essere assegnata a un blocco 'Terra' (Navetta Andata) se possiede la patente. Lo Scudo V5 la blocca a terra per quel frangente, liberandola poi per il blocco 'Acqua' successivo.
5. PRE-POSIZIONAMENTO (Drop-off Passivo): Un furgone lasciato allo sbarco (es. Sarre) segue un workflow dove il blocco Navetta è ancorato allo 'start' e copre l'intera durata della discesa in stato passivo/dormiente.
6. VINCOLO CARRELLO (+C): Un Carrello è un'entità passiva che richiede l'accoppiamento atomico con un Furgone trainante e un Autista con classe 'C'.
7. FOTOGRAFI (F): Risorsa logistica allocabile a un mattoncino parallelo. Consuma posto sul Van, ma non altera la capienza nautica del gommone.

### 🔴 AGGIORNAMENTO MANUALE V5: LIMITI ASIMMETRICI E LA REGOLA DI SARRE (MICRO-SNAVETTAMENTO)

5. 1. **Il Sacco Risorse (Store Vue):** Lo store Pinia (`resource-store.js`) ora possiede i sensori per il pool aziendale: `riverGuides` (intersezione deterministica `expandRoles(roles)` × `NAUTICAL_ROLES` — Dogma 19), `shuttleDrivers` (filtra per tag ruolo `['N', 'C', 'F']` — Corollario Dogma 19 Terra), `towVans` (has_tow_hitch) e `trailers`. Il getter `totalDailyPool` definisce la capienza massima all'alba. ⚠️ I booleani `is_guide` e `is_driver` nella tabella `staff` sono MORTI e IGNORATI ovunque nel frontend.
6. 2. **La Ricetta Logistica (JSON DB):** Le attività salvano il loro fabbisogno (es. guide minime, carrello, navetta) all'interno del DB SQL nella colonna `workflow_schema` (JSON), sotto il nodo `logistics`.
7. 3. **Hard Limits vs Soft Limits (L'Eccezione di Sarre):** Nel calcolo predittivo della disponibilità, le risorse non si comportano allo stesso modo.
8. - **Guide e Carrelli (Hard Limits):** Il loro assorbimento è rigido. Se mancano guide per garantire la sicurezza in acqua o carrelli per spostare i gommoni, la capacità del turno scende a ZERO (Semaforo Rosso - Vendite Bloccate).
9. - **Navette e Autisti su tratte brevi (Soft Limits / Loop):** Agli sbarchi vicini (es. Sarre), i furgoni operano in "loop" (doppio/triplo giro di spola). Il motore matematico NON deve mai bloccare le vendite (rosso) per mancanza di posti a sedere fisici sul furgone in quel minuto di intersezione. Deve invece applicare un "Yield Warning" (Semaforo Giallo), permettendo di incamerare la prenotazione e delegando alla Segreteria l'organizzazione della spola fisica.
