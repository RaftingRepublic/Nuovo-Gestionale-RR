"""
Schemi Pydantic per l'Availability Engine (Motore Matematico Yield).
"""
from pydantic import BaseModel


class AvailabilityRequest(BaseModel):
    """Richiesta calcolo disponibilità per data/orario specifico."""
    date: str         # formato YYYY-MM-DD
    time: str         # formato HH:MM


class AvailabilityResponse(BaseModel):
    """Risposta con pax vendibili e dettaglio colli di bottiglia."""
    available_pax: int
    bottleneck: str
    debug_info: dict = {}
