---
description: Avvia i server di sviluppo Backend (FastAPI) e Frontend (Quasar/Vue3)
---

# 🚀 Avvio Ambiente di Sviluppo

## Prerequisiti

- Node.js installato
- Python 3.11+ con virtual environment già creato in `backend/venv`

---

## 1. Backend (FastAPI + Uvicorn)

Apri un terminale e lancia:

```
cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

// turbo

**Risultato atteso:**

- `✅ Database SQLite inizializzato (rafting.db)`
- `🚀 BACKEND AVVIATO`
- Server in ascolto su `http://localhost:8000`
- Docs Swagger su `http://localhost:8000/docs`

> ⚠️ ATTENZIONE: il file è `main:app` (nella root di backend/), NON `app.main:app`.

---

## 2. Frontend (Quasar Dev Server)

Apri un **secondo** terminale e lancia:

```
cd web-app
npx quasar dev
```

// turbo

**Risultato atteso:**

- Dev server SPA su `http://localhost:9000`
- Hot-reload attivo (modifiche ai .vue si riflettono istantaneamente)

---

## Riepilogo Porte

| Servizio        | URL                        |
| --------------- | -------------------------- |
| Backend FastAPI | http://localhost:8000      |
| Swagger Docs    | http://localhost:8000/docs |
| Frontend Quasar | http://localhost:9000      |

---

## Note

- I due server devono girare in **terminali separati** (o in background).
- Il frontend chiama il backend via proxy configurato in `quasar.config.js` → le chiamate `/api` vengono inoltrate a `:8000`.
- Per reinizializzare il DB da zero: `cd backend && .\venv\Scripts\python.exe init_db.py`
