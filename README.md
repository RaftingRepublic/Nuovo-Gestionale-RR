🚣 Rafting Republic - Gestionale AI (GDPR Compliant)
Versione: 2.0 (Migration & Compliance Edition) Stack: Python 3.10 (FastAPI) + Vue 3 (Quasar) Focus: OCR Ibrido (Paddle+YOLO+GLiNER), Sicurezza Legale (FEA), Zero-Data-Retention.

⚠️ 1. Prerequisiti Tassativi (Windows)
Prima di scaricare il codice, assicurati di avere questi componenti. Non ignorare questa sezione, è la causa del 99% dei crash (Error 127).

Python 3.10.x: Scarica qui.

Non usare 3.11 o 3.12 (incompatibili con alcune lib AI).

Spunta "Add Python to PATH" durante l'installazione.

Visual C++ Redistributable 2015-2022 (x64): Scarica Ufficiale Microsoft.

Necessario per PyTorch e PaddleOCR. Riavvia il PC dopo l'installazione.

Node.js (LTS): Scarica qui.

Git: Scarica qui.

🛠️ 2. Installazione Backend (Il Motore AI)
Il backend richiede una gestione chirurgica delle dipendenze per evitare il "DLL Hell" di Windows.

2.1 Setup Ambiente
Apri PowerShell come Amministratore nella cartella del progetto:

PowerShell
cd backend

# 1. Crea Ambiente Virtuale (Python 3.10)
py -3.10 -m venv venv

# 2. Attiva Ambiente
.\venv\Scripts\activate
# (Dovresti vedere "(venv)" all'inizio della riga)

# 3. Aggiorna PIP
python -m pip install --upgrade pip setuptools wheel
2.2 Installazione "Golden Version" (CPU Only)
Esegui questi comandi in ordine per installare le versioni stabili e certificate:

PowerShell
# A. Installa PyTorch CPU (Evita driver Nvidia pesanti)
pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cpu

# B. Installa librerie Core e AI
pip install paddlepaddle==2.6.2 paddleocr==2.7.3 ultralytics==8.3.20 opencv-python-headless fastapi uvicorn[standard] python-multipart python-dotenv

# C. Installa GLiNER Compatibile (Versione 0.2.7 per evitare crash su huggingface)
pip install gliner==0.2.7 huggingface-hub==0.23.0

# D. Fix per Windows "Error 127" (Librerie Intel OpenMP)
pip install intel-openmp
2.3 Configurazione Privacy (.env)
Crea un file chiamato .env dentro la cartella backend/ con questo contenuto:

Ini, TOML
# backend/.env

APP_ENV=production
LOG_LEVEL=INFO

# --- COMPLIANCE LEGALE (GDPR) ---
# NONE: Le immagini vengono elaborate in RAM e distrutte subito (Produzione)
# DEBUG: Le immagini vengono salvate in storage/dataset_raw (Sviluppo)
ID_IMAGE_RETENTION=NONE

# Configurazione Email (Opzionale)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=none
SMTP_PASS=none
SMTP_FROM=noreply@raftingrepublic.it
2.4 Patch Critica "Main.py"
Assicurati che il file backend/main.py inizi con questo blocco per prevenire conflitti DLL:

Python
# backend/main.py
import os
import sys
try:
    import torch  # <-- DEVE ESSERE IL PRIMO IMPORT
except ImportError:
    pass
from fastapi import FastAPI
# ... resto del codice
🎨 3. Installazione Frontend (Quasar)
Apri un nuovo terminale (non quello del backend):

PowerShell
cd web-app

# 1. Installa dipendenze
npm install

# (Opzionale) Se npm da errori strani, usa: npm install --legacy-peer-deps
🚀 4. Avvio del Sistema
Terminale 1: Backend
PowerShell
cd backend
.\venv\Scripts\activate
# Avvia il server (su 0.0.0.0 per essere raggiungibile da mobile in LAN)
uvicorn main:app --host 0.0.0.0 --port 8000
Attendi finché non leggi: "Application startup complete".

Terminale 2: Frontend
PowerShell
cd web-app
npx quasar dev
Si aprirà il browser automaticamente.

⚖️ 5. Architettura di Compliance Legale
Questa installazione include tre pilastri fondamentali per la protezione legale dell'azienda:

Minimizzazione Dati (GDPR Art. 5):

Logica "Scan & Discard". Le immagini dei documenti (CIE/Passaporti) vengono processate in memoria volatile (RAM) e distrutte immediatamente dopo l'estrazione dei dati. Non vengono mai salvate su disco se ID_IMAGE_RETENTION=NONE.

Firma Grafometrica (Predisposizione FEA):

Il componente di firma (SignaturePad.vue) non cattura solo l'immagine, ma registra i vettori biometrici (coordinate X/Y, tempo, velocità del tratto). Questi dati vengono passati al backend per eventuale hashing/crittografia forense.

Integrità dei Log (Hash Chaining):

Il registro delle operazioni (audit.json) utilizza una catena di hash stile Blockchain. Ogni log contiene l'hash del precedente. Qualsiasi manomissione manuale di un file di log (es. per nascondere un errore) rompe la catena matematica, rendendo la manomissione evidente ("Tamper-Evident").

🚑 6. Troubleshooting Rapido
Errore [WinError 127] ... shm.dll: Manca Visual C++ Redistributable o c'è un conflitto di ordine.

Fix: Riavvia PC -> Controlla che import torch sia la prima riga di main.py -> Esegui pip install intel-openmp.

Errore GLiNER ... missing arguments: Versione GLiNER troppo nuova.

Fix: pip install gliner==0.2.7 huggingface-hub==0.23.0.

Errore Ultralytics settings reset: Normale al primo avvio, ignorare.