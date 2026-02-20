# 🏗️ RAFTING REPUBLIC — Legacy System Data Architecture Audit

**Data Audit:** 20 Febbraio 2026  
**Sorgente:** `full_project_dump (8).txt` — Snapshot 11 Febbraio 2026  
**Stack Legacy:** Python 3.10 (FastAPI 0.x) + Vue 3 (Quasar) + Pydantic v2 + ReportLab  
**Persistenza:** File-Based JSON (nessun Database relazionale)

---

## 📌 INDICE

1. [Overview dell'Architettura](#1-overview-dellarchitettura)
2. [Core Data Models](#2-core-data-models)
   - 2.1 Registration Domain
   - 2.2 Waiver Domain (Legacy)
   - 2.3 Resources Domain (Staff / Fleet / Calendar)
3. [Relazioni tra Entità](#3-relazioni-tra-entita)
4. [Lifecycle & State Machines](#4-lifecycle--state-machines)
5. [Storage Layer (File-Based)](#5-storage-layer-file-based)
6. [API Surface](#6-api-surface)
7. [AI/Vision Pipeline (Schema di Input/Output)](#7-aivision-pipeline)
8. [Suggerimenti per Migrazione a Pydantic/FastAPI/Vue3 Ottimizzato](#8-suggerimenti-migrazione)

---

## 1. Overview dell'Architettura

```
┌─────────────────────────────────────────────────────────┐
│                     VUE 3 + QUASAR                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Kiosk   │  │  Dashboard/  │  │    Planning /     │  │
│  │ Consenso │  │  Registraz.  │  │    Resources      │  │
│  └────┬─────┘  └──────┬───────┘  └────────┬──────────┘  │
│       │               │                   │             │
└───────┼───────────────┼───────────────────┼─────────────┘
        │  HTTP/REST    │                   │
        ▼               ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│                FASTAPI BACKEND (Python)                  │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ /vision  │  │ /registration│  │   /resources      │  │
│  │ (AI OCR) │  │ (CRUD+PDF)   │  │ (Staff/Fleet/Cal) │  │
│  └────┬─────┘  └──────┬───────┘  └────────┬──────────┘  │
│       │               │                   │             │
│  ┌────▼─────┐  ┌──────▼───────┐  ┌────────▼──────────┐  │
│  │ Paddle+  │  │ Registration │  │  Priority Engine  │  │
│  │ YOLO+    │  │   Service    │  │  (JSON File-Based)│  │
│  │ GLiNER   │  │ (PDF+Email)  │  │                   │  │
│  └──────────┘  └──────┬───────┘  └────────┬──────────┘  │
│                       │                   │             │
│                ┌──────▼───────────────────▼──────────┐  │
│                │     FILE SYSTEM (storage/)           │  │
│                │  registrations/<uuid>/               │  │
│                │  resources/{staff,fleet,...}.json     │  │
│                │  daily_freezes/                      │  │
│                └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Punti Chiave:**

- **Nessun Database**: Tutto è persistito su JSON files.
- **AI Pipeline** (Paddle OCR + YOLOv11 + GLiNER) caricata in RAM con pattern Lazy Singleton.
- **GDPR by Design**: immagini elaborate in RAM, mai salvate a disco in produzione (`ID_IMAGE_RETENTION=NONE`).
- **Audit Trail**: append-only `audit.json` con hash-chaining stile Blockchain.

---

## 2. Core Data Models

### 2.1 🧑 Registration Domain

#### `PersonData` (Schema Pydantic - `schemas/registration.py`)

Il modello centrale per qualsiasi persona (partecipante, tutore, minore).

| Campo                  | Tipo                                  | Obbligatorio | Note                                                                      |
| ---------------------- | ------------------------------------- | :----------: | ------------------------------------------------------------------------- |
| `nome`                 | `str`                                 |      ✅      | min_length=1                                                              |
| `cognome`              | `str`                                 |      ✅      | min_length=1                                                              |
| `data_nascita`         | `str`                                 |      ✅      | Formato `DD/MM/YYYY`                                                      |
| `stato_nascita`        | `str?`                                |      ❌      | Es. "ITALIA", "GERMANIA"                                                  |
| `comune_nascita`       | `str?`                                |      ❌      | Es. "Roma"                                                                |
| `stato_residenza`      | `str?`                                |      ❌      | Es. "ITALIA", "ALTRO"                                                     |
| `comune_residenza`     | `str?`                                |      ❌      | Es. "Vigevano"                                                            |
| `indirizzo_residenza`  | `str?`                                |      ❌      | Via completa                                                              |
| `cittadinanza_scelta`  | `Literal["ITALIANA","NON_ITALIANA"]?` |      ❌      | Scelta del flusso UI                                                      |
| `tipo_documento`       | `DocType`                             |      ✅      | Enum: CIE, CI_CARTACEA, PATENTE_IT, PASSAPORTO, PERMESSO_SOGGIORNO, ALTRO |
| `numero_documento`     | `str`                                 |      ✅      | min_length=2                                                              |
| `scadenza_documento`   | `str`                                 |      ✅      | Formato `DD/MM/YYYY`                                                      |
| `source`               | `str?`                                |      ❌      | "OCR_HYBRID", "MANUAL"                                                    |
| `signature_base64`     | `str?`                                |      ❌      | PNG base64 della firma (alias: `signature`)                               |
| `signature_biometrics` | `str?`                                |      ❌      | JSON stringificato dei punti FEA (alias: `signatureBiometrics`)           |
| `legal_consents`       | `LegalConsents?`                      |      ❌      | Consensi annidati (alias: `legal`)                                        |
| `codice_fiscale`       | `str?`                                |      ❌      | ⚠️ **NON nel Pydantic**, salvato come extra field tramite `extra="allow"` |

> ⚠️ **CRITICO**: `codice_fiscale` non è un campo esplicito nel modello `PersonData`. Viene accettato perché `model_config = ConfigDict(extra="allow")`. Questo è un **anti-pattern** da correggere nella migrazione.

#### `LegalConsents` (Schema Pydantic)

| Campo              | Tipo   | Default | Alias Frontend      |
| ------------------ | ------ | ------- | ------------------- |
| `privacy`          | `bool` | `False` | —                   |
| `informed_consent` | `bool` | `False` | `informedConsent`   |
| `responsibility`   | `bool` | `False` | —                   |
| `tesseramento`     | `bool` | `False` | —                   |
| `photo`            | `bool` | `False` | `photoConsent`      |
| `newsletter`       | `bool` | `False` | `newsletterConsent` |

#### `ContactData`

| Campo      | Tipo       | Validazione                   |
| ---------- | ---------- | ----------------------------- |
| `email`    | `EmailStr` | Validazione Pydantic built-in |
| `telefono` | `str`      | min_length=5                  |

#### `RegistrationPayload` (Envelope completo)

| Campo                | Tipo             | Note                                        |
| -------------------- | ---------------- | ------------------------------------------- |
| `language`           | `str`            | Default: "it"                               |
| `booking_id`         | `str?`           | Non implementato                            |
| `tutor_participates` | `bool?`          | Alias: `tutorParticipates`                  |
| `has_minors`         | `bool?`          | Alias: `hasMinors`                          |
| `is_minor`           | `bool`           | Calcolato server-side                       |
| `participant`        | `PersonData`     | ✅ Sempre presente                          |
| `guardian`           | `PersonData?`    | Se minorenne                                |
| `contact`            | `ContactData`    | Email + Telefono                            |
| `legal`              | `LegalConsents?` | Consensi root level (legacy)                |
| `signature_base64`   | `str`            | Firma principale (alias: `signatureBase64`) |

> **Validazione server-side** (model_validator):
>
> - Se `is_minor` e `guardian` è None → ❌ ValueError
> - Se `privacy` non accettata → ❌ ValueError
> - Se `informed_consent` non accettata → ❌ ValueError
> - Format date verificato (`DD/MM/YYYY`)
> - Firma minimo 20 char base64

#### `RegistrationSubmitResponse`

| Campo             | Tipo         |
| ----------------- | ------------ |
| `registration_id` | `str` (UUID) |
| `timestamp_iso`   | `str`        |
| `pdf_filename`    | `str`        |
| `emailed_to`      | `str?`       |

---

### 2.2 📄 Waiver Domain (Legacy — pre-migrazione)

Questo modulo è stato **superato** dal flusso Registration ma è ancora presente nel codice.

#### `PersonaItalia` (Pydantic — `waiver_service.py`)

| Campo                | Tipo             | Note                       |
| -------------------- | ---------------- | -------------------------- |
| `cittadinanza`       | `Literal["ITA"]` | Fisso                      |
| `nome`, `cognome`    | `str`            |                            |
| `comune_nascita`     | `str`            |                            |
| `data_nascita`       | `str`            | DD/MM/YYYY                 |
| `comune_residenza`   | `str`            |                            |
| `codice_fiscale`     | `str`            | ✅ Presente esplicitamente |
| `tipo_documento`     | `str`            |                            |
| `numero_documento`   | `str`            |                            |
| `scadenza_documento` | `str`            |                            |
| `email`, `telefono`  | `str`            |                            |

#### `PersonaEstera`

Come `PersonaItalia` ma con `stato_nascita` e `stato_residenza` al posto dei rispettivi campi comunali. NO `codice_fiscale`.

> **Differenza Architetturale**: Nel Waiver domain la distinzione ITA/estero è **strutturale** (due classi separate). Nel Registration domain è **semantica** (un'unica `PersonData` con campi opzionali + flag `cittadinanza_scelta`).

---

### 2.3 ⚙️ Resources Domain (Staff / Fleet / Calendar)

#### `StaffMember`

| Campo               | Tipo                                                   | Default  |
| ------------------- | ------------------------------------------------------ | -------- |
| `id`                | `str` (UUID)                                           | Auto-gen |
| `name`              | `str`                                                  | —        |
| `is_guide`          | `bool`                                                 | `False`  |
| `is_driver`         | `bool`                                                 | `False`  |
| `is_photographer`   | `bool`                                                 | `False`  |
| `guide_level`       | `Literal["3_LIV","4_LIV","TRIP_LEADER"]?`              | `None`   |
| `guide_skills`      | `List[Literal["RAFTING","HYDROSPEED","SAFETY_KAYAK"]]` | `[]`     |
| `is_active`         | `bool`                                                 | `True`   |
| `default_max_trips` | `int`                                                  | `2`      |

#### `FleetResource`

| Campo           | Tipo                              | Default  |
| --------------- | --------------------------------- | -------- |
| `id`            | `str` (UUID)                      | Auto-gen |
| `type`          | `Literal["RAFT","VAN","TRAILER"]` | —        |
| `name`          | `str`                             | —        |
| `capacity`      | `int`                             | `0`      |
| `priority`      | `int`                             | `1`      |
| `has_tow_hitch` | `bool`                            | `False`  |
| `is_active`     | `bool`                            | `True`   |

#### `ActivityRule`

| Campo           | Tipo           | Note                                                      |
| --------------- | -------------- | --------------------------------------------------------- |
| `id`            | `str` (UUID)   |                                                           |
| `activity_type` | `ActivityType` | FAMILY, CLASSICA, ADVANCED, SELECTION, HYDRO_L1, HYDRO_L2 |
| `name`          | `str`          |                                                           |
| `valid_from`    | `str`          | YYYY-MM-DD                                                |
| `valid_to`      | `str`          | YYYY-MM-DD                                                |
| `days_of_week`  | `List[int]`    | 0=Lunedì … 6=Domenica                                     |
| `start_times`   | `List[str]`    | Es. ["10:00", "14:00"]                                    |
| `is_active`     | `bool`         |                                                           |

#### `AvailabilityRule`

| Campo           | Tipo                                 | Note                                    |
| --------------- | ------------------------------------ | --------------------------------------- |
| `id`            | `str` (UUID)                         |                                         |
| `staff_id`      | `str`                                | FK logica → StaffMember / FleetResource |
| `day_of_week`   | `int?`                               | 0-6 per ricorrenti                      |
| `specific_date` | `str?`                               | YYYY-MM-DD per eccezioni                |
| `start_hour`    | `int`                                |                                         |
| `end_hour`      | `int`                                |                                         |
| `type`          | `Literal["AVAILABLE","UNAVAILABLE"]` |                                         |
| `notes`         | `str?`                               | Motivo ferie/manutenzione               |

#### `DailySlotView` (Read-only, calcolato)

| Campo                 | Tipo           | Note                                      |
| --------------------- | -------------- | ----------------------------------------- |
| `time`                | `str`          | "10:00"                                   |
| `activity_type`       | `ActivityType` |                                           |
| `is_active`           | `bool`         |                                           |
| `avail_guides`        | `int`          | Conteggio guide disponibili               |
| `avail_drivers`       | `int`          |                                           |
| `avail_photographers` | `int`          |                                           |
| `avail_vans`          | `int`          |                                           |
| `avail_rafts`         | `int`          |                                           |
| `avail_trailers`      | `int`          |                                           |
| `cap_guides_pax`      | `int`          | Capacità clienti (guide × raft_capacity)  |
| `cap_vans_pax`        | `int`          | Capacità clienti (somma capacity furgoni) |
| `cap_rafts_pax`       | `int`          | Capacità clienti (somma capacity raft)    |
| `booked_pax`          | `int`          | ⚠️ Sempre 0 — **non implementato**        |

#### `PriorityResponse` (Semaforo A/B/C/D)

| Campo                | Tipo                       | Note                                          |
| -------------------- | -------------------------- | --------------------------------------------- |
| `status`             | `Literal["A","B","C","D"]` | A=Verde, B=Giallo, C=Rosso, D=Blu(Elasticità) |
| `color_hex`          | `str`                      |                                               |
| `description`        | `str`                      | "Aperto", "Limite", "Chiuso", "Elasticità"    |
| `total_capacity`     | `int`                      |                                               |
| `remaining_capacity` | `int`                      |                                               |
| `elastic_buffer`     | `int`                      |                                               |
| `active_guides`      | `int`                      |                                               |

---

## 3. Relazioni tra Entità

```
RegistrationPayload (1)
  ├── participant: PersonData (1)     ← OBBLIGATORIO
  ├── guardian: PersonData (0..1)     ← Solo se minorenne
  ├── contact: ContactData (1)        ← Email + Tel
  ├── legal: LegalConsents (0..1)     ← Consensi root (legacy)
  └── signature_base64: str (1)       ← Firma PNG

PersonData (ogni persona include):
  ├── legal_consents: LegalConsents (0..1)  ← Consensi per-persona
  ├── signature_base64: str (0..1)           ← Firma per guardian
  └── signature_biometrics: str (0..1)       ← Dati FEA vettoriali

StaffMember (N)
  └── AvailabilityRule (N)    ← FK logica: staff_id → StaffMember.id

FleetResource (N)
  └── AvailabilityRule (N)    ← FK logica: staff_id → FleetResource.id
                                ⚠️ Stessa tabella per Staff e Fleet!

ActivityRule (N)
  └── DailySlotView (calcolato) ← Non persistito, join runtime
```

> ⚠️ `AvailabilityRule.staff_id` è usato come FK sia per Staff che per Fleet. Non c'è un campo `resource_type` per distinguere. Funziona perché gli UUID sono univoci, ma è semanticamente confuso.

---

## 4. Lifecycle & State Machines

### 4.1 Registration Lifecycle

```
          ┌─── SCAN ───┐
          │  /vision    │
          │  /analyze   │
          │             │
          ▼             │
    [Frontend collects] ──── OCR Data (extracted)
          │
          ▼
    [Frontend submit] ──── POST /registration/submit
          │
          ▼
    ┌─────────────────────┐
    │  registration_id    │
    │  timestamp_iso      │
    │  computed_age       │
    │  is_minor           │   ──── CREATE (audit log)
    │  locked: true       │
    └─────────┬───────────┘
              │
              ├── PDF generato (signed.pdf)
              ├── Firma salvata (signature.png)
              ├── Biometrici salvati (biometrics.json)
              ├── Payload completo (payload.json)
              ├── Email inviata (se SMTP configurato)
              │
              ▼
    ┌─────────────────────┐
    │  LOCKED = true      │  ← Default post-creazione
    │                     │
    │  POST /{id}/lock    │  ← locked: false (sblocca per modifica)
    │  POST /{id}/lock    │  ← locked: true  (ri-blocca)
    └─────────────────────┘
              │
              ▼
    [Se modificato con update_id]:
    ┌─────────────────────┐
    │  ARCHIVE versione   │  ← history/v_{timestamp}/
    │  precedente         │     payload.json, signed.pdf, signature.png
    │                     │
    │  OVERWRITE corrente │  ← Nuova versione sovrascrive file root
    │  UPDATE (audit log) │
    └─────────────────────┘
```

### 4.2 Priority Semaphore (A/B/C/D)

```
Input: date_iso, hour, current_pax, request_pax

    total_guides = count(available guides @ hour)
    total_capacity = total_guides × RAFT_CAPACITY (default: 8)
    remaining = total_capacity - current_pax

    IF remaining < request_pax OR total_guides == 0:
        → C (ROSSO) "Chiuso"

    active_rafts = ceil(current_pax / RAFT_CAP)
    elastic = (active_rafts × RAFT_CAP) - current_pax

    IF elastic >= request_pax AND current_pax > 0:
        → D (BLU) "Elasticità" — I clienti stanno nei raft già attivi

    IF (total_guides - active_rafts - 1) < SAFETY_BUFFER:
        → B (GIALLO) "Limite" — Si attiverebbero troppe guide

    ELSE:
        → A (VERDE) "Aperto" — OK
```

---

## 5. Storage Layer (File-Based)

### Directory Structure

```
backend/storage/
├── registrations/
│   └── <uuid>/
│       ├── payload.json        ← Dati completi registrazione
│       ├── signed.pdf          ← PDF firmato
│       ├── signature.png       ← Firma grafica
│       ├── biometrics.json     ← Punti FEA vettoriali
│       ├── audit.json          ← Log con hash-chaining
│       └── history/
│           └── v_<timestamp>/  ← Snapshot precedente (se UPDATE)
│               ├── payload.json
│               ├── signed.pdf
│               ├── signature.png
│               └── biometrics.json
│
├── resources/
│   ├── staff.json              ← Array di StaffMember
│   ├── fleet.json              ← Array di FleetResource
│   ├── activity_rules.json     ← Array di ActivityRule
│   ├── availability_rules.json ← Array di AvailabilityRule
│   ├── config.json             ← { raft_capacity: 8, safety_buffer: 1 }
│   └── slots.json              ← (non usato attivamente)
│
├── daily_freezes/
│   └── freeze_report_<date>.json  ← Snapshot giornaliero con hash file
│
├── dataset_raw/                ← Immagini debug (solo se ID_IMAGE_RETENTION=DEBUG)
└── debug_captures/             ← Screenshot YOLO per debugging
```

### Audit Log Format (Hash-Chaining)

```json
[
  {
    "timestamp": 1770647937.399,
    "iso_date": "2026-02-09T15:38:57+0100",
    "action": "CREATE",
    "details": "Nuova registrazione",
    "previous_hash": "0000000000000000000000000000000000000000000000000000000000000000",
    "hash": "33528bd7ddc630acb889f04e2588b9c4175f37125d9678039ef9ced568f75644"
  },
  {
    "action": "EMAIL_SENT",
    "details": "To: theo.bellotti@live.it",
    "previous_hash": "33528bd7...",
    "hash": "d4c09ad3..."
  }
]
```

> **Azioni tracciabili:** `CREATE`, `UPDATE`, `EMAIL_SENT`, `EMAIL_ERROR`, `LOCK_CHANGE`, `BIO_ERROR`

---

## 6. API Surface

### 6.1 Registration Endpoints (`/api/v1/registration/`)

| Metodo | Path            | Descrizione                | Request                               | Response                          |
| ------ | --------------- | -------------------------- | ------------------------------------- | --------------------------------- |
| `POST` | `/scan`         | OCR document analysis      | `multipart (front, back?, doc_type)`  | `DocumentScanResponse`            |
| `POST` | `/submit`       | Create/Update registration | `RegistrationPayload` + `?update_id=` | `RegistrationSubmitResponse`      |
| `GET`  | `/details/{id}` | Read full payload          | —                                     | `dict` (payload.json + audit_log) |
| `GET`  | `/list`         | List registrations         | `?limit=&offset=&q=`                  | `{ items: [...] }`                |
| `POST` | `/{id}/lock`    | Toggle lock                | `{ locked: bool }`                    | `{ registration_id, locked }`     |
| `GET`  | `/{id}/pdf`     | Download PDF               | —                                     | `FileResponse`                    |

### 6.2 Vision Endpoints (`/api/v1/vision/`)

| Metodo | Path       | Descrizione                                      |
| ------ | ---------- | ------------------------------------------------ |
| `POST` | `/analyze` | Full OCR pipeline (YOLO → Paddle → GLiNER → MRZ) |

### 6.3 Resources Endpoints (`/api/v1/resources/`)

| Metodo            | Path                                              | Descrizione                        |
| ----------------- | ------------------------------------------------- | ---------------------------------- |
| `GET/POST/DELETE` | `/staff`                                          | CRUD Staff                         |
| `GET/POST/DELETE` | `/fleet`                                          | CRUD Fleet                         |
| `GET/POST/DELETE` | `/activity-rules`                                 | CRUD Activity Rules                |
| `GET`             | `/daily-schedule?date=`                           | Calendario giornaliero (calcolato) |
| `GET`             | `/availability/{resource_id}`                     | Regole disponibilità               |
| `POST`            | `/availability`                                   | Imposta disponibilità              |
| `GET`             | `/priority?date=&hour=&current_pax=&request_pax=` | Semaforo priorità                  |

### 6.4 Waivers (Legacy — `/api/v1/waivers/`)

| Metodo | Path                                   | Descrizione       |
| ------ | -------------------------------------- | ----------------- |
| `POST` | `/waivers/draft`                       | Crea bozza waiver |
| `POST` | `/waivers/{id}/finalize`               | Firma e finalizza |
| `GET`  | `/waivers/{id}/pdf?which=draft\|final` | Download PDF      |

---

## 7. AI/Vision Pipeline

### Data Flow

```
[Immagine Documento]
       │
       ▼
  YOLO v11-OBB ──→ Crop + Perspective Warp (1000×630px)
       │
       ▼
  PaddleOCR (Italiano) ──→ Testo OCR Grezzo
       │
       ├──→ MRZ Parser ──→ nome, cognome, doc_num, data_nascita, scadenza
       │                     (con checksum e self-repair)
       │
       ├──→ GLiNER NER ──→ campi anagrafici (confidence-based)
       │     (urchade/gliner_medium-v2.1)
       │
       ├──→ Regex Fallback ──→ codice_fiscale, doc_num specifico
       │
       └──→ Date Heuristic ──→ ordina date per assegnare nascita/scadenza

  MERGE: MRZ > AI_FRONT > AI_BACK > REGEX > HEURISTIC
       │
       ▼
  DocumentScanResponse.extracted: {
    nome, cognome, data_nascita, tipo_documento,
    numero_documento, scadenza_documento,
    comune_nascita, comune_residenza, codice_fiscale,
    stato_nascita, stato_residenza, cittadinanza,
    source: "HYBRID_NEURAL_V8"
  }
```

### Schema di Estrazione per Tipo Documento

| Tipo               | Schema                | MRZ |    Lati    |
| ------------------ | --------------------- | :-: | :--------: |
| CIE                | STANDARD              | ✅  | FRONT+BACK |
| PATENTE_IT         | PATENTE_SCHEMA        | ❌  | FRONT+BACK |
| PASSAPORTO         | PASSPORT_VISUAL + MRZ | ✅  | FRONT only |
| CI_CARTACEA        | STANDARD              | ❌  | FRONT+BACK |
| PERMESSO_SOGGIORNO | STANDARD              | ✅  | FRONT+BACK |
| ALTRO              | STANDARD              | ❌  | FRONT+BACK |

---

## 8. Suggerimenti Migrazione a Pydantic/FastAPI/Vue3 Ottimizzato

### 8.1 ❌ Anti-Pattern da Eliminare

| #   | Problema Legacy                                                          | Soluzione                                                                          |
| --- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| 1   | `PersonData(extra="allow")` — `codice_fiscale` è un campo "fantasma"     | Aggiungere campo esplicito `codice_fiscale: Optional[str] = None`                  |
| 2   | Date come `str` ("DD/MM/YYYY") con parsing manuale                       | Usare `datetime.date` con custom serializer/validator                              |
| 3   | `AvailabilityRule.staff_id` usato per Staff E Fleet                      | Rinominare in `resource_id` + aggiungere `resource_type: Literal["STAFF","FLEET"]` |
| 4   | `DailySlotView` duplicato nel file schemas                               | Rimuovere duplicazione                                                             |
| 5   | `booked_pax` sempre 0 nel `DailySlotView`                                | Implementare o rimuovere                                                           |
| 6   | Consensi in 2 posizioni (`payload.legal` e `participant.legal_consents`) | Unificare in un unico punto                                                        |
| 7   | Signature_base64 in 2 posizioni (root e dentro PersonData)               | Unificare: firma al root level, biometrici collegati                               |
| 8   | JSON file-based storage senza indici                                     | Migrare a SQLite o PostgreSQL per query efficienti                                 |
| 9   | WaiverService è codice morto (sostituito da RegistrationService)         | Rimuovere o archiviare                                                             |
| 10  | `PriorityEngine._load()` → try/except vuoto che swallows errori          | Aggiungere logging                                                                 |

### 8.2 ✅ Pattern da Mantenere

| #   | Buona Pratica                           | Perché                                             |
| --- | --------------------------------------- | -------------------------------------------------- |
| 1   | Audit hash-chaining                     | Tamper-evident, conforme GDPR                      |
| 2   | Lazy loading dei modelli AI             | Critico per hosting con RAM limitata (1GB Ergonet) |
| 3   | GDPR by design (RAM-only processing)    | Conformità privacy                                 |
| 4   | Biometric FEA collection                | Valore legale firma                                |
| 5   | Version archiving con `history/v_<ts>/` | Tracciabilità modifiche                            |
| 6   | `_safe_get()` helper                    | Robusto per accesso a dati misti dict/object       |
| 7   | Semaforo A/B/C/D con logica elasticità  | Business logic solida                              |
| 8   | Document specs knowledge base           | Manutenibile per nuovi tipi documento              |

### 8.3 📐 Schema Migrazione Proposto

```python
# NUOVO: PersonData esplicito
class PersonData(BaseModel):
    nome: str = Field(..., min_length=1)
    cognome: str = Field(..., min_length=1)
    data_nascita: date  # ← NOT str

    # Geografici (tutti espliciti)
    stato_nascita: str | None = None
    comune_nascita: str | None = None
    stato_residenza: str | None = None
    comune_residenza: str | None = None

    # Documenti
    cittadinanza_scelta: Literal["ITALIANA", "NON_ITALIANA"] | None = None
    codice_fiscale: str | None = None  # ← ESPLICITO, non più extra
    tipo_documento: DocType
    numero_documento: str = Field(..., min_length=2)
    scadenza_documento: date  # ← NOT str

    # Dati OCR
    source: str | None = None

# NUOVO: AvailabilityRule con resource_type
class AvailabilityRule(BaseModel):
    id: str
    resource_id: str  # ← Rinominato da staff_id
    resource_type: Literal["STAFF", "FLEET"]  # ← NUOVO
    ...

# NUOVO: Storage via SQLite/PostgreSQL
# Tabelle: registrations, persons, consents, audit_log,
#           staff, fleet, activity_rules, availability_rules
```

### 8.4 🗺️ Roadmap Migrazione Consigliata

1. **Fase 0**: Solidificare `PersonData` (campo `codice_fiscale` esplicito, date tipizzate)
2. **Fase 1**: Migrare `resources/` a SQLite (elimina TOCTOU su JSON concorrenti)
3. **Fase 2**: Migrare `registrations/` a SQLite (con BLOB per PDF/firma)
4. **Fase 3**: Rimuovere codice morto (`waiver_service.py`, `waivers.py` endpoint)
5. **Fase 4**: Unificare consensi e firme in un unico layout
6. **Fase 5**: Implementare `booked_pax` tramite collegamento Registrazioni ↔ Slot

---

_Fine Audit — Documento generato da analisi statica del dump completo del progetto legacy._
