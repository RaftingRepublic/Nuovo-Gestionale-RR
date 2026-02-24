# FASE 6.D: Il Motore Predittivo (Il Sacco delle Risorse)

**Il Teorema del Fiume (Logica del PM):**
La disponibilità di un turno non è un numero statico o una capienza commerciale fissa. È un calcolo predittivo e dinamico basato sull'assorbimento del "Sacco" totale delle risorse aziendali (Guide, Furgoni, Carrelli).

**La Logica di Assorbimento (Liquid Yield Management):**

1. **Stato Zero:** Un giorno vuoto offre la capienza massima teorica su ogni turno, calcolata sul totale del Pool Aziendale.
2. **Minimum Viable Footprint:** Alla _prima_ prenotazione su un turno vuoto, il sistema "congela" un pacchetto minimo vitale di risorse virtuali (es. minimo 2 Guide fiume per sicurezza, 1 Autista, 1 Furgone, 1 Carrello) per l'intera durata temporale del blocco BPMN.
3. **Ricalcolo Intersezionale:** I turni adiacenti/sovrapposti temporalmente ricalcolano la propria disponibilità massima in tempo reale pescando dal "sacco" decurtato. Se mancano guide o carrelli nel lasso di tempo intersecante, la disponibilità crolla proporzionalmente.
4. **Semafori UI (Steering):** L'interfaccia (PlanningPage) mostrerà indicatori fluttuanti e accenderà "semafori" (Verde, Giallo, Rosso) basandosi sul riempimento del sacco. Questo permette alla segreteria di indirizzare i clienti nei "buchi" ottimali, saturando i convogli già in acqua prima di innescare nuove risorse a costo.

**Requisito Tecnico Futuro (Next Session):**
Sarà necessario configurare le "Ricette" per ogni attività nel DB (es. un record Rafting = richiede_carrello: true, guide_minime: 2) per istruire il motore matematico su quanto "svuotare il sacco" a ogni primo ordine inserito.
