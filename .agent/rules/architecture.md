---
trigger: always_on
---

# RAFTING REPUBLIC - ARCHITECTURE & DEPLOY RULES

## 1. PROTOCOLLO FILE-FIRST & NO-HALLUCINATION
- **Source of Truth:** Prima di modificare, leggi SEMPRE il file esistente (`@filename`).
- **Integrità:** Non rimuovere mai import o metodi helper a meno che non siano esplicitamente obsoleti.
- **Output:** Restituisci sempre il file completo. Mai usare `// ...rest of code`.

## 2. VINCOLI INFRASTRUTTURA ERGONET (CRITICO)
- **Environment:** CloudLinux con LVE (Lightweight Virtual Environment).
- **RAM Limit:** Max 1GB  Ottimizza per basso footprint.
- **Concurrency:** Usa `passenger_wsgi.py` con `a2wsgi`. NON usare `uvicorn` diretto.
- **AI Models:**
    - I modelli (YOLO, Paddle, GLiNER) DEVONO usare il pattern **Lazy Loading** (inizializza solo alla prima chiamata).
    - Mai caricare modelli nel Global Scope (`import` time).
    - Invoca `gc.collect()` dopo ogni inferenza pesante.

## 3. SICUREZZA & GDPR
- **No Storage:** Nessuna immagine di documenti (CIE/Passaporti) deve essere salvata su disco (`storage/`) in chiaro.
- **Logs:** Usa solo `audit.json` con logica append-only.