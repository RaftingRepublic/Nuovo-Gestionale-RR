### backend/app/api/v1/api.py
from fastapi import APIRouter

# Import dei router esistenti
from app.api.v1.endpoints.ai import router as ai_router
from app.api.v1.endpoints.vision import router as vision_router

# Registration e Waivers (Legacy)
try:
    from app.api.v1.endpoints.registration import router as registration_router
except Exception:
    registration_router = None

try:
    from app.api.v1.endpoints.waivers import router as waivers_router
except Exception:
    waivers_router = None

# --- RISORSE (NUOVO) ---
# IMPORTANTE: Qui NON usiamo try/except. Se questo fallisce, DEVE mostrare l'errore.
from app.api.v1.endpoints.resources import router as resources_router
# -----------------------

api_router = APIRouter()

api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(vision_router, prefix="/vision", tags=["vision"])

if registration_router:
    api_router.include_router(registration_router, prefix="", tags=["registration"])

if waivers_router:
    api_router.include_router(waivers_router, prefix="/waivers", tags=["waivers"])

# Registrazione Router Risorse
api_router.include_router(resources_router, prefix="/resources", tags=["resources"])