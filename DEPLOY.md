# 🚀 Guida Deploy — Quarto RR Gestionale

Guida passo-passo per il deploy su **Ergonet Plesk** (`gestionale.raftingrepublic.com`).

---

## Prerequisiti

- ✅ Accesso SSH al server
- ✅ Accesso al pannello Plesk
- ✅ Python 3.9+ installato sul server
- ✅ Node.js 18+ installato **in locale** (per la build)

---

## STEP 1: Build del Frontend (dal tuo PC)

```bash
cd web-app
npx quasar build
```

Questo crea la cartella `web-app/dist/spa/` con tutti i file statici pronti.

---

## STEP 2: Upload dei file sul server

Usa **FileZilla** o un client SFTP qualsiasi.

### 2a. Frontend → httpdocs

Carica il **contenuto** di `web-app/dist/spa/` nella cartella del sottodominio:

```
Locale:  web-app/dist/spa/*
Remoto:  /var/www/vhosts/raftingrepublic.com/subdomains/gestionale/httpdocs/
```

> ⚠️ Carica i **file dentro** `spa/`, non la cartella `spa` stessa.  
> Il file `index.html` deve trovarsi direttamente in `httpdocs/index.html`.

### 2b. Backend → home directory

Carica la **cartella `backend/`** nella home directory del tuo account:

```
Locale:  backend/
Remoto:  /var/www/vhosts/raftingrepublic.com/backend/
```

> ⚠️ **NON caricare** le cartelle `venv/`, `__pycache__/`, `storage/debug_captures/`, `test/`, `tools/`.  
> Carica solo: `app/`, `main.py`, `requirements_production.txt`, `.env`, `assets/`.

---

## STEP 3: Setup Backend via SSH

Collegati al server via SSH:

```bash
ssh tuouser@raftingrepublic.com
```

### 3a. Verifica Python

```bash
python3 --version
# Deve essere 3.9 o superiore
```

Se non c'è Python 3.9+, chiedi a Ergonet di installarlo o usa `pyenv`.

### 3b. Crea Virtual Environment

```bash
cd /var/www/vhosts/raftingrepublic.com/backend
python3 -m venv venv
source venv/bin/activate
```

### 3c. Installa Dipendenze

```bash
pip install --upgrade pip
pip install -r requirements_production.txt
```

### 3d. Configura .env

```bash
cp .env.example .env
nano .env
# Configura i valori SMTP se hai un servizio email
```

### 3e. Crea cartelle storage

```bash
mkdir -p storage/resources
mkdir -p storage/registrations
mkdir -p storage/waivers
```

### 3f. Test Avvio

```bash
python3 -c "from main import app; print('✅ Backend OK')"
```

---

## STEP 4: Avvia il Backend

### Opzione A: Screen (semplice, consigliata)

```bash
# Crea una sessione screen persistente
screen -S backend

# Attiva il virtualenv e avvia
cd /var/www/vhosts/raftingrepublic.com/backend
source venv/bin/activate
gunicorn main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -

# Per staccarsi dalla sessione: premi Ctrl+A poi D
# Per ricollegarsi: screen -r backend
```

### Opzione B: Systemd (robusta, auto-restart)

Se hai accesso root, crea un servizio systemd:

```bash
sudo nano /etc/systemd/system/gestionale-backend.service
```

Contenuto:

```ini
[Unit]
Description=Gestionale Backend API
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/vhosts/raftingrepublic.com/backend
ExecStart=/var/www/vhosts/raftingrepublic.com/backend/venv/bin/gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000 --timeout 60
Restart=always
RestartSec=5
Environment=PATH=/var/www/vhosts/raftingrepublic.com/backend/venv/bin

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable gestionale-backend
sudo systemctl start gestionale-backend
sudo systemctl status gestionale-backend
```

---

## STEP 5: Configura il Proxy in Plesk

Devi fare in modo che le richieste a `gestionale.raftingrepublic.com/api/*` vengano inoltrate al backend Python.

### Dal pannello Plesk:

1. Vai in **Siti Web e Domini** → **gestionale.raftingrepublic.com**
2. Clicca su **Impostazioni Apache & Nginx**
3. Scorri fino a **Direttive Nginx aggiuntive** (o "Additional nginx directives")
4. Aggiungi questo blocco:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 30s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    client_max_body_size 20M;
}
```

5. Clicca **OK / Applica**

---

## STEP 6: Verifica

### Test 1 — Frontend
Apri `https://gestionale.raftingrepublic.com` nel browser.  
Dovresti vedere l'app caricata.

### Test 2 — Backend API
```bash
curl https://gestionale.raftingrepublic.com/api/v1/health
# Risposta attesa: {"status":"healthy","ai_available":false,"version":"0.2.0"}
```

### Test 3 — Root API
```bash
curl https://gestionale.raftingrepublic.com/
# Dovrebbe caricare il frontend (HTML)
```

---

## 🔄 Comandi Utili

### Aggiornare il Frontend
```bash
# In locale
cd web-app
npx quasar build
# Poi ricaricare i file da dist/spa/ in httpdocs/ via SFTP
```

### Aggiornare il Backend
```bash
# Upload nuovi file via SFTP, poi:
ssh tuouser@raftingrepublic.com
screen -r backend
# Ctrl+C per stoppare, poi rieseguire il comando gunicorn
```

### Vedere i log
```bash
screen -r backend
# I log sono visibili in tempo reale
```

### Riavviare il Backend (con systemd)
```bash
sudo systemctl restart gestionale-backend
sudo journalctl -u gestionale-backend -f  # Log in tempo reale
```

---

## ⚠️ Note Importanti

1. **HTTPS**: Plesk gestisce automaticamente i certificati SSL tramite Let's Encrypt. Verifica che sia attivo dal pannello Plesk → gestionale.raftingrepublic.com → Certificati SSL/TLS.

2. **AI disabilitata**: Con `requirements_production.txt` le funzioni AI (OCR, visione) non sono disponibili. Gli endpoint `/api/v1/vision/analyze` e `/api/v1/registration/scan` restituiranno errore 503. Tutte le altre funzioni (prenotazioni, calendario, staff, registrazioni manuali, PDF) funzionano normalmente.

3. **Abilitare AI in futuro**: Serve upgrade RAM del server a minimo 2GB, poi installare `requirements_fixed.txt` al posto di `requirements_production.txt`.

4. **Backup dati**: I dati sono in `backend/storage/`. Pianifica backup regolari di questa cartella.
