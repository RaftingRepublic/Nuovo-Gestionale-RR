# FASE 7: CREW BUILDER — LAVAGNA D'IMBARCO DIGITALE

**Stato:** CANTIERE APERTO (27/02/2026)
**Prerequisiti completati:** Fase 6 sigillata. Split-Brain risolto. Motore Predittivo stabile.

---

## 1. VISIONE

La lavagna fisica del cliente è un database relazionale orizzontale: ogni riga indica chi guida quale gommone e quanti passeggeri ha a bordo. L'attuale tabella `ride_allocations` in Supabase è una "piscina piatta" che perde queste relazioni, salvando solo una lista slegata di UUID per turno.

Il Crew Builder trasforma la "piscina piatta" in una **Busta Stagna**: un documento JSONB autoconsistente che cattura l'intera composizione dell'equipaggio in un singolo colpo.

---

## 2. REGOLE D'INGAGGIO DEFINITIVE

### 2.1 Frontend

Il Crew Builder sarà un **nuovo tab "Equipaggi"** innestato dentro `RideDialog.vue` (l'Omni-Board). **Nessuna pagina separata.**

- Tab posizionato DOPO "Ordini Esistenti" e "Nuova Prenotazione"
- UI a **righe dinamiche**: ogni riga = una barca
- Ogni riga contiene: [Select Gommone] + [Select Guida] + [Lista Passeggeri con pax_count]
- Bottone "+ Aggiungi Barca" per aggiungere righe
- Bottone "Salva Equipaggio" che invia la Busta Stagna al backend
- I dati di selezione (gommoni, guide) provengono dallo store Pinia (`fleetList`, `staffList`)
- I passeggeri provengono dagli ordini Supabase del turno selezionato

### 2.2 Backend

Un singolo endpoint per salvare la "Busta Stagna" in un solo colpo:

- **Endpoint:** `PUT /api/v1/orders/{ride_id}/crew`
- **Logica:** UPSERT completo su Supabase (`ride_allocations` dove `ride_id` = target)
- **Operazione:** DELETE all existing allocations per il ride + INSERT batch delle nuove righe
- **Ogni riga `ride_allocations`** avrà:
  - `ride_id` (UUID turno)
  - `resource_id` (UUID risorsa — guida o mezzo)
  - `resource_type` ("guide" | "raft" | "van" | "trailer")
  - `metadata` (JSONB — la Busta Stagna con la composizione completa della barca)

### 2.3 Database

Useremo **ESCLUSIVAMENTE** la tabella `ride_allocations` in Supabase (colonna `metadata` JSONB).

**☠️ TABELLE SQLite DICHIARATE MORTE:**

- `crew_assignments` — MAI usata (0 righe)
- `ride_staff_link` — MAI usata (0 righe)
- `ride_fleet_link` — MAI usata (0 righe)

Queste tabelle M2M in SQLite sono fossili della Fase 6.B Blueprint e NON verranno mai populate. La composizione equipaggio vive SOLO nel cloud.

---

## 3. STRUTTURA JSONB — "BUSTA STAGNA"

Lo schema JSONB nel campo `metadata` di ciascuna riga `ride_allocations` con `resource_type = 'raft'`:

```json
{
  "crew_version": 1,
  "boats": [
    {
      "boat_id": "fleet-uuid-raft-001",
      "boat_name": "Raft Giallo",
      "guide_id": "staff-uuid-marco",
      "guide_name": "Marco Rossi",
      "passengers": [
        {
          "order_id": "supabase-order-uuid-aaa",
          "customer_name": "Famiglia Bianchi",
          "pax_count": 4
        },
        {
          "order_id": "supabase-order-uuid-bbb",
          "customer_name": "Coppia Verdi",
          "pax_count": 2
        }
      ],
      "total_pax": 6,
      "capacity": 8,
      "notes": ""
    },
    {
      "boat_id": "fleet-uuid-raft-002",
      "boat_name": "Raft Blu",
      "guide_id": "staff-uuid-luca",
      "guide_name": "Luca Neri",
      "passengers": [
        {
          "order_id": "supabase-order-uuid-ccc",
          "customer_name": "Gruppo Aziendale TechCorp",
          "pax_count": 7
        }
      ],
      "total_pax": 7,
      "capacity": 8,
      "notes": "Safety Kayak assegnato"
    }
  ],
  "unassigned_pax": [
    {
      "order_id": "supabase-order-uuid-ddd",
      "customer_name": "Walk-in Senza Nome",
      "pax_count": 2
    }
  ],
  "total_boats": 2,
  "total_assigned_pax": 13,
  "total_unassigned_pax": 2
}
```

### 3.1 Regole dello Schema

| Campo                            | Tipo          | Note                                                   |
| -------------------------------- | ------------- | ------------------------------------------------------ |
| `crew_version`                   | integer       | Versione schema (futuro-proof per migrazioni)          |
| `boats[]`                        | array         | Array di oggetti barca                                 |
| `boats[].boat_id`                | string (UUID) | FK → fleet.id (SQLite locale)                          |
| `boats[].guide_id`               | string (UUID) | FK → staff.id (SQLite locale)                          |
| `boats[].passengers[]`           | array         | Passeggeri assegnati alla barca                        |
| `boats[].passengers[].order_id`  | string (UUID) | FK → orders.id (Supabase cloud)                        |
| `boats[].passengers[].pax_count` | integer       | Pax di QUELL'ordine su QUESTA barca (split consentito) |
| `boats[].total_pax`              | integer       | Somma derivata `SUM(passengers[].pax_count)`           |
| `boats[].capacity`               | integer       | Capienza barca (da fleet.capacity)                     |
| `unassigned_pax[]`               | array         | Ordini non ancora assegnati a nessuna barca            |
| `total_boats`                    | integer       | Conteggio barche                                       |
| `total_assigned_pax`             | integer       | Pax assegnati totali                                   |
| `total_unassigned_pax`           | integer       | Pax in attesa di assegnazione                          |

### 3.2 Caso d'Uso: Split Ordine

Un ordine di 6 persone (Famiglia Bianchi) può essere **splittato** su due barche:

- Barca 1: `{ order_id: "aaa", pax_count: 4 }`
- Barca 2: `{ order_id: "aaa", pax_count: 2 }`

Il vincolo di integrità è: `SUM(pax_count per order_id) == order.total_pax`

---

## 4. FASI DI IMPLEMENTAZIONE

| Step | Descrizione                                                                     | Stima  |
| ---- | ------------------------------------------------------------------------------- | ------ |
| 7.A  | Verifica/creazione colonna `metadata` JSONB in `ride_allocations` Supabase      | 5 min  |
| 7.B  | Endpoint backend `PUT /orders/{ride_id}/crew` con httpx UPSERT                  | 30 min |
| 7.C  | Tab "Equipaggi" in RideDialog.vue — UI a righe dinamiche                        | 60 min |
| 7.D  | Integrazione lettura: caricamento Busta Stagna all'apertura RideDialog          | 20 min |
| 7.E  | Validazione: check pax_count vs order totals, highlight barche piene            | 20 min |
| 7.F  | Lavagna Operativa (DailyBoardPage.vue): visualizzazione allineata per convoglio | 40 min |

---

## 5. FILE COINVOLTI

| File                        | Modifica                                           |
| --------------------------- | -------------------------------------------------- |
| `RideDialog.vue`            | Nuovo tab "Equipaggi" con UI righe dinamiche       |
| `desk.py` o nuovo `crew.py` | Endpoint PUT crew UPSERT                           |
| `resource-store.js`         | Action `saveCrewAssignment` / `loadCrewAssignment` |
| `DailyBoardPage.vue`        | Parser visivo righe allineate per convoglio        |
| Supabase DDL                | Verifica colonna metadata JSONB                    |
