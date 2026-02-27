# SYSTEM SNAPSHOT REPORT — RAFTING REPUBLIC
Generato: 27/02/2026 (Aggiornato alla Fase 8 del progetto)
Report per: Onboarding Tech Lead
Autore: System Agent

## 1. IDENTITÀ DEL SISTEMA E VINCOLI INFRASTRUTTURA
L'infrastruttura di Rafting Republic è un gestionale ibrido, distribuito su cloud per la cassa e locale per la logistica.
L'hosting operativo (Ergonet CloudLinux) implementa restrizioni LVE rigorose:
*   Risorse limitate: Max 1GB di RAM. Questa limitazione rende severamente proibito il caricamento di modelli AI in memoria (es. YOLO, Paddle).
*   Deployment Backend: Passenger WSGI con a2wsgi. L'uso autonomo di uvicorn è vietato in produzione.
*   Architettura AI e GDPR: I modelli AI locali sono stati epurati. Il riconoscimento identità utilizza Azure OCR cloud-based. Non avviene nessuno storage permanente in chiaro (policy ID_IMAGE_RETENTION=NONE, file e immagini residenti solo in RAM e processati via base64 su PDF auto-generati o distrutti in audit.json).

## 2. STATO CORRENTE (CANTIERE: FASE 8 "DEBITO TECNICO")
Il sistema ha completato i lavori titanici della Fase 6 (Logistica Fluidodinamica e POS ibrido) e della Fase 7 (Crew Builder Lavagna D'Imbarco). Attualmente lo sforzo è concentrato sulla "Fase 8: Smaltimento Debito Tecnico".

### Completamenti Recenti (Chiusura Fasi):
*   Crew Builder Operativo: Banchina integrata su RideDialog.vue con interfacce a righe dinamiche. Gestiti sensori di bilancia passeggeri, kill-switch del varo e "Tetris Umano".
*   Fix Split-Brain: Cassa nativamente cablata via httpx a Supabase. Sventramento vecchio ORM da POS Desk.
*   Incenerimento Ruderi: Cancellati dt-1, dt-3, e dt-4: requirements unificati, amputate tabelle SQLAlchemy morte (CrewAssignmentDB, ride_staff_link, ride_fleet_link) ed estirpato script local_vision_service.py (36KB di lib AI). 

### Debito Tecnico e Bug Pendenti (DT ATTIVI):
*   DT-2 (Pendiente): Pulizia massiva dei commenti JSDoc obsoleti lungo il codebase frontend, causati dagli epocali sventramenti architettonici.
*   Cimitero Backend in Sospeso: Esistono ancora endpoints deprecati sotto /api/v1/legacy-orders. Le tabelle locali SQLite (orders, transactions, customers) sono un retaggio del vecchio ORM legacy. Attualmente non causano crash, ma espongono al rischio di disallineamento se interrogati inavvertitamente e necessitano eradicazione totale non appena il POS Ibrido viene consolidato storicamente.

## 3. L'ARCHITETTURA IBRIDA (SPLIT-BRAIN CONTROLLATO)
Per garantire precisione matematica alla logistica e scalabilità commerciale, l'architettura si biforca programmaticamente in un DUAL DATABASE MODEL.

### Il Catalogo Locale (SQLite)
Rappresenta la Single Source of Truth del motore predittivo. Tutte le risorse, attività, turni materializzati, mezzi fisici e staff vivono in locale nel file rafting.db. Nessuna entità Cloud può alterare questi dati senza passare mediante logiche di backend.

### Il Registro Operativo (Supabase PostgreSQL)
Gestisce esclusivamente i "Dati Caldi" operativi, ovvero i flussi di Cassa Commerciale (ordini, transazioni), il CRM aziendale e le allocazioni finali sul fiume (composizione logistica JSONB).

### Bridge Applicativo: "Sync Sonda" e "Dual Write"
*   Dual-Write per i Turni: Ogni turno creato possiede uno specifico UUID. Questo UUID viene scritto simultaneamente su SQLAlchemy (SQLite - table daily_rides) e su httpx/Supabase (PostgREST - table rides).
*   Sync Sonda per l'Engine: Poiché l'ORM SQLite è isolato, il file "calendar.py" utilizza httpx per scaricare un dizionario pax effettivi dal cloud, iniettandolo al "Availability Engine".

## 4. MAPPA E STRUTTURA DEL DATABASE

### 4.A - SQLITE LOCALE (rafting.db)
Le entità persistite da SQLAlchemy.
*   activities: Cuore delle regole BPMN (JSON workflow_schema) che governano il flusso gommoni/furgoni/tratte.
*   daily_rides: Turno fisico. Colonna vitale status (Semaforo) e is_overridden (Flag override manuale cassa).
*   staff: Anagrafica guide e autisti con gestione json di contratti e array ruoli.
*   fleet: Entità dei mezzi operativi equipaggiati di flag "capacity" o "has_tow_hitch" (ganci traino) essenziali per incroci dell'eccezione logistica di Sarre.
*   system_settings e activity_sub_periods: Configurazioni EAV e override stagionali.

### 4.B - SUPABASE CLOUD (PostgreSQL)
*   rides: Gemello di "daily_rides" usato come radice estera.
*   orders & transactions: Motore cassa che registra i booked_pax crudi e un libro mastro per pagamenti frazionati/multipli.
*   ride_allocations: Archiviazione del Crew Builder (Busta Stagna). Il campo "metadata" di tipo JSONB conserva in un colpo solo lo snodo intero Gommone + Guida + N Passeggeri (array groups frammentabile dell'Order).
*   registrations & customers: Modulo FiRaft per consensi auto-scompattati dal Kiosk via Magic Link.

## 5. DOGMI ARCHITETTURALI E PROTOCOLLI L'INGAGGIO (DA MEMORIZZARE)
Queste sei regole sono i sigilli sacri scritti nel "LORE_VAULT". Violarli provoca implosione strutturale e regressioni critiche.

1.  DOGMA DDL SUPABASE: Qualunque alterazione in Cloud necessita obbligatoriamente dell'istruzione "NOTIFY pgrst, 'reload schema';" alla fine del DDL per invalidare la cache PostgREST. L'omissione provoca Errore PGRST204.
2.  DOGMA 10 (TETRIS UMANO): Nel Crew builder i passeggeri non sono numeri interi liberi. La "Busta Stagna" li tratta come raggruppamenti iscritti: "groups: [{ order_id, pax }]". Questo abilita lo split dei clienti di un maxi-ordine su gommoni multipli senza perdere mai l'headcount.
3.  DOGMA 11 (SWAP & REPLACE CRUENTO): Modificare entità con parentele complesse via httpx cloud (es: allocazioni equipaggi) non prevede patching o diffing. Radere al suolo le row in base al target ID con una DELETE, e fare INSERT bulk dei payload nuovi da UI.
4.  DOGMA 12 (CHIAVE LOGICA) E COROLLARIO (ARTO FANTASMA): Divieto assoluto di istituire constraint FOREIGN KEY fisiche tra il Cloud Supabase e il Locale SQLite (es. resource_id per mezzo o staff). Il collegamento è puramente UUID. La presenza fisica di tali constraint genera blocchi HTTP 409. In caso di epurazione FK, sradicare le rel-JOIN PostgREST nel root JS del frontend per non far scattare il fatale errore HTTP PGRST200 da frontend.
5.  DOGMA DELL'OVERRIDE: Una segreteria umana onnipotente ha in override la macchina predittiva. Se in daily_rides è flaggato "is_overridden = True", l'Availability Engine deve restituire l'ultimo stato noto dal DB e bypassare internamente Pass 1 (allocazione BPMN virtuale) e Pass 2 (Semaforo per Capacity). Toggle ripristinabile solo con l'uso del tasto UI "AUTO".
6.  DOGMA 13 (KILL-SWITCH BANCHINA): L'integrazione frontend DEVE paralizzare il varo gommoni verso backend Cloud se lo specchio rileva in UI che Capacity (sensore gommone/galleggiante) va in overflow rosso, o che i pax imbarcati per un order superano matematicamente l'order originato (sensore sovra-assegnazioni fantasma). Imbarcati < Pagati è tollerato.

---
Il presente file rappresenta lo snapshot ultimo del sistema. Nessuna architettura addizionale dovrà violare le premesse qui imposte dal design tecnico di fase 8.
