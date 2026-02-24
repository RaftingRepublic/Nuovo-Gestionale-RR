# 🧭 Rafting Republic Gestionale - Project Radar

## 🟢 STATO ATTUALE: FASE 4 COMPLETATA (Logistica e Calendario)

### ✅ Traguardi Raggiunti (Ultima Sessione)

- **UI Calendario Operativo:** Implementati semafori dinamici di riempimento (16px), "Ghost Slots" colorati, navigazione rapida Mese/Anno con menu a tendina e Footer "Potenza di Fuoco" (Badge colorati riassuntivi delle risorse attive).
- **Yield Engine V4 (Motore Logistico):** Completamente dinamico. Tempi di percorrenza (Tratti A, B, C) e capienze nette dei mezzi non sono più hardcodati, ma vengono letti in tempo reale dal database locale SQLite (`system_settings`).
- **Resilienza Database:** Rimossa FK `rides_activity_id_fkey` da Supabase per sbloccare i salvataggi. Join con `activities` spostato 100% in locale nel frontend, garantendo l'assenza di crash API. Vecchi dati di test svuotati.
- **Scudo Anti-Ubiquità:** Il `ResourcePanel.vue` calcola le sovrapposizioni temporali (`Start_A < End_B && End_A > Start_B`) di tutti i turni reali della giornata e disabilita (in grigio) le opzioni di guide e mezzi già in acqua in quello stesso orario.

### 🧹 Debito Tecnico Pendente (Da pulire in futuro)

- Rimuovere variabile non usata `internalViewMode` in `CalendarComponent.vue`.
- Ripulire i `console.log` di telemetria e sostituire i `print()` in `yield_engine.py` con il modulo `logging` standard.

### 🚧 PROSSIMI PASSI (Fase 5 - Da decidere al prossimo avvio)

1. **Opzione A:** Modulo Presenze Giornaliere (Assenze, Riposi, Malattie) per filtrare ulteriormente la "Potenza di Fuoco" reale.
2. **Opzione B:** Flusso di Prenotazione CRM (Gestione anagrafica, note intolleranze, caparre, saldi).
3. **Opzione C:** Dashboard Principale (Grafici, alert operativi, riepilogo giornaliero).
