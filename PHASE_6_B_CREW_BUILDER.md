# FASE 6.B: Da Piscina Piatta a Compositore di Equipaggi (Crew Builder)

**Il Problema:** La lavagna fisica del cliente è un database relazionale. L'allineamento orizzontale indica chi guida quale veicolo/gommone e quanti pax ha a bordo. L'attuale tabella ride_allocations in Supabase è una "piscina piatta" che perde queste relazioni, salvando solo una lista slegata di UUID per turno.

**Piano di Attacco (Next Session):**

1. **Database (Supabase):** Aggiungere una colonna metadata (tipo JSONB) alla tabella ride_allocations. Questa colonna ospiterà un link_id (per legare le risorse della stessa riga, es. la Guida al suo Gommone) e i pax (passeggeri).
2. **Store Vue (resource-store.js):** Modificare saveRideAllocations per impacchettare e inviare i metadata a Supabase.
3. **UI Assegnazione (ResourcePanel.vue):** Sventrare i q-select multipli. Sostituirli con un "Crew Builder" a righe dinamiche:
   - _Riga Acqua:_ [Select Gommone] + [Select Guida] + [Input PAX].
   - _Riga Terra:_ [Select Furgone] + [Select Autista] + [Checkbox Carrello].
4. **UI Lavagna (DailyBoardPage.vue):** Riscrivere il parser visivo. Leggere i metadata.link_id e stampare le risorse allineate orizzontalmente, raggruppate per convoglio, replicando le righe fisiche della lavagna.
