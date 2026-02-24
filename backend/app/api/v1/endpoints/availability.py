"""
Endpoint API per il Yield Engine (Motore Matematico Disponibilità).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.availability import AvailabilityRequest, AvailabilityResponse
from app.services.yield_engine import calculate_slot_availability

router = APIRouter()


@router.post("/calculate", response_model=AvailabilityResponse)
async def calculate_availability(
    request: AvailabilityRequest,
    db: Session = Depends(get_db),
):
    """
    Calcola i posti vendibili (pax) per un dato slot (data + orario).

    Incrocia le risorse SQLite (staff + flotta) con le allocazioni
    Supabase (ride_allocations) e applica i vincoli logistici:
    - Acqua: guide × gommoni
    - Terra: furgoni gancio × autisti patente C × carrelli
    """
    try:
        return await calculate_slot_availability(request, db)
    except Exception as e:
        print(f"[AvailabilityEndpoint] Errore non gestito nel Yield Engine: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Errore interno nel motore di calcolo: {str(e)}"
        )
