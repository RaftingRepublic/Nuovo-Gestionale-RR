# PROJECT RADAR

## STATO ATTUALE: FASE 5 COMPLETATA (Pivot Architetturale V5 BPMN)

## Traguardi Raggiunti:

1. Incenerito il vecchio Yield Engine V4 e le costanti temporali globali.
2. Implementato **Costruttore di Flussi a Mattoncini** in `SettingsPage.vue` (Libreria LocalStorage, Inserimento Pull a tendina, Giustificazione Flexbox Navetta).
3. Implementato **Yield Engine V5 e Scudo Anti-Ubiquità V5**: logica a scostamento cumulativo (ancoraggi `start`/`end`), normalizzazione tag, fallback monolitico per attività vergini.
4. Fix Reattività State Management: estirpato campo fossile "Tratti Fiume" e risolto il bug di desync (F5) sui Ghost Slots tramite l'helper `_isActivityClosedOnDate`.
5. Eseguita pulizia Supabase dai vecchi dati orfani (Split-Brain risolto).

## Debito Tecnico Pendente:

Nessuno critico. Solo pulizia di vecchi file di migrazione o commenti JSDoc obsoleti.

## PROSSIMI PASSI (Fase 6):

- Opzione A: Timeline View (Visualizzazione grafica a Gantt nidificata Discese/Flussi/Blocchi) integrata come nuova rotta in Quasar.
- Opzione B: Modulo Presenze Giornaliere Staff.
- Opzione C: Flusso Prenotazioni CRM (Anagrafiche, Pagamenti).
