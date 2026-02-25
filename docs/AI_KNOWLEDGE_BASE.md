# AI KNOWLEDGE BASE - RAFTING REPUBLIC

### ⚙️ AVAILABILITY ENGINE E RIVER LEDGER (YIELD MANAGEMENT STRATEGICO)

Il motore in `availability_engine.py` NON è un banale contatore di stock lineare. Usa un Time-Array Slicer a 1440 minuti (1 minuto = 1 slot) e logiche fluviali avanzate.
**Dogmi per l'IA (Non modificare MAI queste logiche senza ordine esplicito):**

1. **River Ledger (Matrice ARR):** Il fiume non è a compartimenti stagni. I gommoni fisici partiti a monte generano posti vuoti che "scendono a valle".
2. **Waterfall Offset (Routing):** La matrice temporale hardcodata è: **AD (Advanced) cede a CL (Classic) a +60 minuti. CL cede a FA (Family) a +30 minuti**.
3. **Consumo a Priorità Invertita:** L'algoritmo consuma SEMPRE prima i posti vuoti galleggianti in transito (`arr_bonus_seats`). Solo se i passeggeri superano questi posti bonus, calcola il prelievo di nuove barche fisiche dalla base (`needed_boats`).
4. **Capacità Asimmetrica:** La `total_capacity` calcolata e inviata al frontend DEVE e PUÒ superare la somma fisica dei gommoni in base. La formula è: `total_capacity = (barche_fisiche_disponibili * raft_capacity) + arr_bonus_seats`.
5. **Safety Kayak (Hard Floor):** Le guide minime per la sicurezza (`min_guides_absolute` definite nel JSON logistico) NON sono un moltiplicatore lineare sui gommoni fisici varati, ma un pavimento logico rigido stratificato nell'array dei 1440 minuti. Formula: `guides_needed = max(min_guides_absolute, needed_boats)`.
6. **EAV Logistica Furgoni:** Il calcolo dei posti netti per i furgoni avviene sottraendo autista e guida dal totale posti, pescando le chiavi dal DB dinamico `SystemSettingDB` (Pattern EAV).
7. **Semaforo Asimmetrico (Status):** ROSSO (posti residui <= `-overbooking_limit`), GIALLO (posti residui <= `yellow_threshold` OPPURE c'è uno `yield_warning` sui furgoni, ovvero mancano posti strada anche se ci sono posti fiume), VERDE (libero).
