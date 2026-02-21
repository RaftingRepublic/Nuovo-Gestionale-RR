### backend/main.py
# --- FIX CRITICO WINDOWS ---
# Importiamo torch per primo per evitare conflitti DLL (WinError 127) 
# con altre lib come Paddle o OpenCV.
import os
import sys
try:
    import torch
except ImportError:
    pass
# ---------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import dei Router
from app.api.v1.endpoints import vision
from app.api.v1.endpoints import registration

# --- NUOVO: Importiamo il router delle risorse ---
try:
    from app.api.v1.endpoints import resources
except ImportError as e:
    print(f"⚠️ ERRORE IMPORT RESOURCES: {e}")
    resources = None
# -----------------------------------------------

# --- DATABASE SQLAlchemy (SQLite) ---
from app.db.database import engine, Base
from app.models.registration import RegistrationDB  # noqa: F401 — import necessario per creare la tabella
from app.models.calendar import (  # noqa: F401
    ActivityDB, DailyRideDB, OrderDB, StaffDB, FleetDB, CrewAssignmentDB,
    ResourceExceptionDB, SystemSettingDB, ActivitySubPeriodDB,
)

app = FastAPI(title="AI Modular Backend", version="0.3.0")

# Crea le tabelle SQL al primo avvio (se non esistono)
Base.metadata.create_all(bind=engine)
print("✅ Database SQLite inizializzato (rafting.db)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "active", "message": "Backend Operativo v2"}

# --- HEALTH CHECK per monitoring produzione ---
@app.get("/api/v1/health")
def health_check():
    ai_status = getattr(vision, 'AI_AVAILABLE', False)
    return {
        "status": "healthy",
        "ai_available": ai_status,
        "version": "0.2.0"
    }

# --- REGISTRAZIONE ROTTE ---

# 1. Vision AI
app.include_router(vision.router, prefix="/api/v1/vision", tags=["AI Vision"])

# 2. Registration (Ha già prefix interno, ma per sicurezza mappiamo su /api/v1)
# Nota: registration.router ha già "/registration" nel suo file, quindi qui usiamo /api/v1
app.include_router(registration.router, prefix="/api/v1", tags=["Registration"])

# 3. Resources (Gestione Staff e Turni)
if resources:
    app.include_router(resources.router, prefix="/api/v1/resources", tags=["Resources"])
else:
    print("❌ Router Resources NON caricato. Controlla gli errori sopra.")

# 4. Reservations & Overrides
from app.api.v1.endpoints import reservations
app.include_router(reservations.router, prefix="/api/v1/reservations", tags=["Reservations"])

# 5. Calendar (BFF — Motore Calendario SQL)
from app.api.v1.endpoints import calendar
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["Calendar"])

# 6. Orders (Creazione Ordini, Logica Tetris, Ponte d'Oro)
from app.api.v1.endpoints import orders
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])

# 7. FiRaft (Gestione Tesseramento)
from app.api.v1.endpoints import firaft
app.include_router(firaft.router, prefix="/api/v1/firaft", tags=["FiRaft"])

# 8. Logistics (Motore Logistico Operativo)
from app.api.v1.endpoints import logistics
app.include_router(logistics.router, prefix="/api/v1/logistics", tags=["Logistics"])

# --- LOG AVVIO ---
print("\n" + "="*60)
print("🚀 BACKEND AVVIATO")
print(f"   AI Vision: {'✅ Abilitato' if getattr(vision, 'AI_AVAILABLE', False) else '❌ Disabilitato (librerie non installate)'}")
print(f"   Resources: {'✅ Caricato' if resources else '❌ Non caricato'}")
print("="*60 + "\n")