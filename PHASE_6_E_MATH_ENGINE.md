# FASE 6.E: Il Motore Matematico (The Emptying Engine)

**Formula Base dell'Intersezione:**
Per ogni slot (Turno) T, la disponibilità logistica D(T) è calcolata come:
D(T) = TotalPool - Sum(Assorbimento(X))
_Dove X rappresenta l'insieme dei turni attivi il cui blocco temporale (BPMN) interseca l'orologio di T._

**La Legge del Pescaggio Asimmetrico:**
Non tutte le risorse bloccano le vendite allo stesso modo.

- **Hard Limits (Blocco Commerciale - Semaforo Rosso):**
  Se D(T).riverGuides < T.logistics.min_guides -> Sicurezza compromessa. Vendite bloccate.
  Se D(T).trailers < 1 (e l'attività lo richiede) -> Logistica bloccata. Vendite bloccate.
- **Soft Limits & L'Eccezione di Sarre (Navettamento Elastico / Spola):**
  Il numero di posti passeggero di un furgone (es. capacity: 9) NON è un limite rigido di vendita se la distanza (es. sbarco a Sarre) permette la spola. Il sistema non deve MAI bloccare a Zero la capacità commerciale per mancanza di sedili.
  Se i passeggeri prenotati superano i posti furgone disponibili in quel minuto di intersezione, l'interfaccia si colorerà di GIALLO (Yield Warning: "Spola Necessaria"), permettendo di incamerare la prenotazione.

**Implementazione Futura (Next Session):**
Verrà iniettata una funzione calculateDynamicYield(slot, allDailySlots) in resource-store.js o planning-store.js. La funzione itererà sui mattoncini temporali per trovare le vere intersezioni di orologio e applicherà i Soft/Hard limits per determinare il Semaforo (Verde, Giallo, Rosso) e i posti residui vendibili.
