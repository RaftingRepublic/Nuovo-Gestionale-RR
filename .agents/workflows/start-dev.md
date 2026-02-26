---
description: Avvia i server di sviluppo Backend (FastAPI) e Frontend (Quasar/Vue3)
---

# Start Dev — Avvio Server Sviluppo Locale

## Prerequisiti

- Python 3.11+ con virtualenv in `backend/venv`
- Node.js 20+ con dipendenze installate in `web-app/node_modules`

## Passi

// turbo-all

1. Avvia il **Backend FastAPI** con uvicorn in modalità dev (reload automatico):

   ```bash
   cd backend && venv\Scripts\activate && python -m uvicorn main:app --reload --port 8000
   ```

2. Avvia il **Frontend Quasar** in modalità dev:

   ```bash
   cd web-app && npx quasar dev
   ```

## Note

- Il backend gira su `http://localhost:8000`
- Il frontend gira su `http://localhost:9000` (default Quasar)
- Il modulo FastAPI è `main:app` (nella root di backend/, NON app.main:app)
- In produzione si usa `passenger_wsgi.py` con `a2wsgi`, MAI uvicorn diretto (vincolo Ergonet CloudLinux)
