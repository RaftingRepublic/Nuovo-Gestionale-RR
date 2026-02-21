### backend/app/api/v1/api.py
"""
Router master: registra tutti gli endpoint dell'applicazione.
Gli import opzionali (ai, vision, registration, waivers) sono wrappati
in try/except per evitare che un modulo mancante blocchi l'intero server.
"""
from fastapi import APIRouter

api_router = APIRouter()

# ── Import OPZIONALI (moduli AI/OCR possono non esistere in dev) ──
try:
    from app.api.v1.endpoints.ai import router as ai_router
    api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
except Exception:
    print("⚠️  Router AI non trovato, skip.")

try:
    from app.api.v1.endpoints.vision import router as vision_router
    api_router.include_router(vision_router, prefix="/vision", tags=["vision"])
except Exception:
    print("⚠️  Router Vision non trovato, skip.")

try:
    from app.api.v1.endpoints.registration import router as registration_router
    api_router.include_router(registration_router, prefix="", tags=["registration"])
except Exception:
    print("⚠️  Router Registration non trovato, skip.")

try:
    from app.api.v1.endpoints.waivers import router as waivers_router
    api_router.include_router(waivers_router, prefix="/waivers", tags=["waivers"])
except Exception:
    print("⚠️  Router Waivers non trovato, skip.")

# ── Import OBBLIGATORI (devono funzionare, altrimenti crash esplicito) ──
from app.api.v1.endpoints.resources import router as resources_router
api_router.include_router(resources_router, prefix="/resources", tags=["resources"])

# ── Cantiere 3: API Pubbliche (Check-in Digitale, senza Auth) ──
from app.api.v1.endpoints.public import router as public_router
api_router.include_router(public_router, prefix="/public", tags=["public"])