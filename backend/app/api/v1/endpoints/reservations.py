from fastapi import APIRouter, Query, HTTPException, Body
from typing import List, Optional
from app.schemas.resources import (
    Reservation, ReservationCreate,
    ManualOverride, ManualOverrideCreate
)
from app.services.resources.priority_engine import PriorityEngine

router = APIRouter()
engine = PriorityEngine()

# --- RESERVATIONS ---
@router.post("/", response_model=Reservation)
def create_reservation(payload: ReservationCreate):
    return engine.add_reservation(payload)

@router.get("/", response_model=List[Reservation])
def list_reservations(date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$")):
    return engine.list_reservations(date)

@router.delete("/{id}")
def delete_reservation(id: str):
    engine.delete_reservation(id)
    return {"status": "deleted", "id": id}

# --- MANUAL OVERRIDES ---
@router.post("/overrides", response_model=ManualOverride)
def create_override(payload: ManualOverrideCreate):
    return engine.add_manual_override(payload)

@router.get("/overrides", response_model=List[ManualOverride])
def list_overrides(date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$")):
    return engine.list_manual_overrides(date)

@router.delete("/overrides/{id}")
def delete_override(id: str):
    engine.delete_manual_override(id)
    return {"status": "deleted", "id": id}
