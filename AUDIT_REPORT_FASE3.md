# 🔍 AUDIT REPORT — Fine Fase 3

> **Data:** 2026-02-23T20:55 · **Auditor:** Senior QA Engine · **Build:** ✅ Zero errori

---

## 🟢 SISTEMI OK — Validati e perfetti

### Backend

| Componente                                   | Stato | Note                                                                                                    |
| -------------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------- |
| `availability.py` (endpoint)                 | ✅    | Schema Pydantic corretto. Response model matches.                                                       |
| `AvailabilityRequest/Response` (schema)      | ✅    | Campi tipizzati, default `dict={}` per debug_info.                                                      |
| `_detect_bottleneck()`                       | ✅    | Tutti i rami edge-case coperti (0 guide, 0 gommoni, 0 furgoni, ecc.). Nessun `min()` su sequenza vuota. |
| `_fetch_busy_names()`                        | ✅    | Parsing JSON difensivo: controlla `isinstance(rides, list)`, guarda per chiave con `.get()`.            |
| `min(len(...), len(...), len(...))` (Fase B) | ✅    | Usa `len()` che ritorna sempre `int ≥ 0` → nessun `ValueError`.                                         |
| `sum(t.max_rafts or 0 ...)` (Fase B)         | ✅    | Protetto da `or 0` contro `None`.                                                                       |
| `gc.collect()` post-calcolo                  | ✅    | Conforme regola Ergonet.                                                                                |

### Frontend

| Componente                            | Stato | Note                                                                                                                                                                         |
| ------------------------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `YieldSimulatorDialog.vue`            | ✅    | Import/registrazione/integrazione corretti in PlanningPage. `v-model` con `computed get/set`, `watch(isOpen)` per reset stato, try/catch robusto con `errorMsg` in UI.       |
| `ResourcePanel.vue` — Template        | ✅    | Tutti i `<q-select>` hanno `emit-value` + `map-options`. `option-label="label"` e `option-value="value"` coerenti.                                                           |
| `ResourcePanel.vue` — Pre-populate    | ✅    | `extractNames()` gestisce sia stringhe che oggetti `{name}`. `.filter(Boolean)` rimuove stringhe vuote.                                                                      |
| `ResourcePanel.vue` — saveAllocations | ✅    | `try/catch` completo, `saving.value = false` nel `finally`. Notifica negativa con `err.message`.                                                                             |
| `ensureSupabaseIds()` — Guard null    | ✅    | `if (!item.name) return` alla riga 544 previene crash su `undefined.trim()`.                                                                                                 |
| `ensureSupabaseIds()` — Dedup         | ✅    | `toInsert.some(...)` previene inserimento doppio nello stesso payload.                                                                                                       |
| PlanningPage ↔ YieldSimulator         | ✅    | `yieldSimOpen` ref, `:initial-date` prop, import corretto.                                                                                                                   |
| Codice orfano (vecchi mock)           | ✅    | **Nessun residuo trovato.** `nameToId`, `enrichWithRoles`, `findSqliteMatch`, `fetchResources`, `boatOptionsDB/vanOptionsDB/trailerOptionsDB` → tutti rimossi correttamente. |

---

## 🛠️ FIX APPLICATE — Bug silenti corretti durante l'audit

### FIX 1 — ⚠️ CRITICO: Crash `is_free(None)` nel Yield Engine

- **File:** `yield_engine.py` → `is_free()`
- **Bug:** Se uno staff/fleet ha `name = None` in SQLite, `name.strip()` genera `AttributeError`. Il filtro `all_staff` non escludeva record con nome null.
- **Fix:**

  ```python
  # PRIMA (crashava su None)
  def is_free(name: str) -> bool:
      return name.strip().lower() not in busy_names

  # DOPO (null-safe)
  def is_free(name) -> bool:
      if not name:
          return False
      return str(name).strip().lower() not in busy_names
  ```

  Aggiunto anche `s.name and` / `f.name and` nei filtri di guide, autisti, gommoni, furgoni e carrelli.

### FIX 2 — ⚠️ MEDIO: Graceful Degradation Supabase

- **File:** `yield_engine.py` → `calculate_slot_availability()`
- **Bug:** Se Supabase è offline, `_fetch_busy_names` già gestiva l'errore, ma `calculate_slot_availability` poteva propagare l'eccezione verso l'alto senza controllo.
- **Fix:** Wrappato in `try/except`: se Supabase è irraggiungibile, il sistema assume `busy_names = set()` (tutte le risorse libere) e logga l'errore. Preferibile servire un risultato impreciso che un 500.

### FIX 3 — ⚠️ MEDIO: Timeout e Error Handling httpx

- **File:** `yield_engine.py` → `_fetch_busy_names()`
- **Bug:** Timeout di 10s poteva essere troppo aggressivo su rete lenta. Non distingueva tra `ConnectError` e `TimeoutException`.
- **Fix:** Timeout portato a 15s. Aggiunti handler specifici:
  ```python
  except httpx.ConnectError as e:
      print(f"[YieldEngine] Supabase non raggiungibile: {e}")
  except httpx.TimeoutException as e:
      print(f"[YieldEngine] Timeout connessione Supabase: {e}")
  ```

### FIX 4 — ⚠️ MEDIO: Endpoint senza Error Handler

- **File:** `availability.py` (endpoint)
- **Bug:** Un errore non gestito nel Yield Engine (es. SQLAlchemy) causava un 500 con traceback raw in produzione.
- **Fix:** Aggiunto `try/except` con `HTTPException(500)` e messaggio strutturato + log in console.

### FIX 5 — 🟡 BASSO: Import `Optional` inutilizzato

- **File:** `schemas/availability.py`
- **Bug:** `from typing import Optional` non usato da nessun campo.
- **Fix:** Rimosso.

### FIX 6 — 🟡 BASSO: Blocco duplicato `free_drivers_c`

- **File:** `yield_engine.py`
- **Bug:** Il blocco di calcolo `free_drivers_c` era duplicato (merge artifact). La seconda copia non aveva il guard `s.name and`, sovrascrivendo la prima corretta.
- **Fix:** Rimossa la copia duplicata.

---

## 🟡 WARNINGS / TECH DEBT — Raccomandazioni per Fase 4

### 1. 🔑 Credenziali Supabase Hardcoded

- **File:** `yield_engine.py` righe 26–32
- **Rischio:** La Supabase Anon Key è in chiaro nel codice sorgente Python.
- **Raccomandazione:** Spostare in variabili ambiente (`os.environ.get('SUPABASE_URL')`) o in un file `.env` caricato con `python-dotenv`.

### 2. 📊 `debug_info: dict = {}` non tipizzato

- **File:** `schemas/availability.py`
- **Rischio:** Il campo `debug_info` è un `dict` generico. Qualsiasi chiave/valore può essere iniettato.
- **Raccomandazione:** Creare un Pydantic model `DebugInfo` con campi tipizzati per type-safety e auto-documentazione API (OpenAPI schema).

### 3. 🔄 Multi-ruolo non esclusivo nel Yield Engine

- **Stato:** Il motore V1 conta la stessa persona sia tra le guide libere che tra gli autisti liberi se ha entrambi i ruoli. Il frontend (ResourcePanel) ha l'anti-ubiquità, ma il backend no.
- **Raccomandazione:** In V2, implementare l'esclusione mutua lato engine: se una persona è sia guida che autista, deve essere contata in un solo pool.

### 4. 🧹 `store.resources` Supabase ancora caricato

- **File:** `resource-store.js` → `fetchCatalogs()`
- **Stato:** `this.resources = res` carica ancora l'intera tabella `resources` di Supabase. Serve solo per `ensureSupabaseIds()` come fallback UUID lookup.
- **Raccomandazione:** Valutare se il fetch completo è necessario all'avvio o se farlo solo on-demand nel momento del salvataggio.

### 5. 🔒 Nessuna validazione formato date nell'endpoint

- **File:** `availability.py` + `schemas/availability.py`
- **Rischio:** `date: str` e `time: str` accettano qualsiasi stringa. Un valore malformato (es. `"ciao"`) produce una query Supabase che ritorna 0 risultati senza errore, ma confonde l'utente.
- **Raccomandazione:** Aggiungere `@validator('date')` e `@validator('time')` con regex per YYYY-MM-DD e HH:MM.

### 6. 📝 Lint Pyre Falsi Positivi

- **Nota:** L'IDE segnala errori su tutti gli import Python (`httpx`, `fastapi`, `sqlalchemy`, `pydantic`). Sono falsi positivi: l'IDE Pyre non è configurato per trovare il virtualenv del progetto. Il backend gira correttamente con uvicorn. Per risolvere, configurare `pyrightconfig.json` o `.pyre_configuration` con il path del venv.

---

## ✅ RISULTATI BUILD

| Target                                            | Risultato                              |
| ------------------------------------------------- | -------------------------------------- |
| `npx quasar build` (Frontend)                     | ✅ Zero errori, zero warning bloccanti |
| `python -m py_compile yield_engine.py`            | ✅ Compilazione OK                     |
| `python -m py_compile availability.py` (endpoint) | ✅ Compilazione OK                     |
| `python -m py_compile availability.py` (schema)   | ✅ Compilazione OK                     |
| Codice orfano nel frontend                        | ✅ Nessun residuo trovato              |
| Lint Pyre IDE                                     | ⚠️ Falsi positivi (venv non in path)   |
