"""
Schemi Pydantic V2 per il dominio Calendario.
"""

from __future__ import annotations

from datetime import date, time
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, ConfigDict


# ─── SOTTOPERIODO ─────────────────────────────────────────

class ActivitySubPeriodCreate(BaseModel):
    name: Optional[str] = None
    dates: List[str] = []
    override_price: Optional[float] = None
    override_times: List[str] = []
    is_closed: bool = False
    allow_intersections: Optional[bool] = None
    yellow_threshold: Optional[int] = None
    overbooking_limit: Optional[int] = None

class ActivitySubPeriodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    activity_id: str
    name: Optional[str] = None
    dates: List[str] = []
    override_price: Optional[float] = None
    override_times: List[str] = []
    is_closed: bool = False
    allow_intersections: Optional[bool] = None
    yellow_threshold: Optional[int] = None
    overbooking_limit: Optional[int] = None


# ─── ATTIVITÀ ────────────────────────────────────────────

class ActivityCreate(BaseModel):
    name: str
    code: str
    color_hex: str = "#1976D2"
    price: float = 0.0
    duration_hours: float = 2.0
    river_segments: Optional[str] = None
    manager: str = "Grape"
    season_start: Optional[date] = None
    season_end: Optional[date] = None
    default_times: List[str] = []
    allow_intersections: bool = False
    activity_class: str = "RAFTING"
    yellow_threshold: int = 8
    overbooking_limit: int = 0
    workflow_schema: Optional[Dict[str, Any]] = None

class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    price: float
    duration_hours: float
    color_hex: str
    river_segments: Optional[str] = None
    manager: str = "Grape"
    season_start: Optional[date] = None
    season_end: Optional[date] = None
    default_times: List[str] = []
    allow_intersections: bool = False
    activity_class: str = "RAFTING"
    yellow_threshold: int = 8
    overbooking_limit: int = 0
    workflow_schema: Optional[Dict[str, Any]] = None
    is_active: bool
    sub_periods: List[ActivitySubPeriodResponse] = []


class ActivitySeasonUpdate(BaseModel):
    code: Optional[str] = None
    color_hex: Optional[str] = None
    duration_hours: Optional[float] = None
    river_segments: Optional[str] = None
    manager: Optional[str] = None
    price: Optional[float] = None
    season_start: Optional[date] = None
    season_end: Optional[date] = None
    default_times: Optional[List[str]] = None
    allow_intersections: Optional[bool] = None
    activity_class: Optional[str] = None
    yellow_threshold: Optional[int] = None
    overbooking_limit: Optional[int] = None
    workflow_schema: Optional[Dict[str, Any]] = None
    sub_periods: Optional[List[ActivitySubPeriodCreate]] = None


# ─── DISCESA GIORNALIERA ─────────────────────────────────

class AssignedResource(BaseModel):
    """Risorsa assegnata (Staff o Mezzo) — id, nome e categoria per la UI."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    category: Optional[str] = None  # 'RAFT' | 'VAN' per fleet, None per staff

class DailyRideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    activity_id: str
    ride_date: date
    ride_time: time

    status: str
    is_overridden: bool
    notes: Optional[str] = None

    activity_name: str = ""
    color_hex: str = "#4CAF50"
    booked_pax: int = 0

    # Campi calcolati dall'AvailabilityEngine
    # --- SENSORI MOTORE PREDITTIVO V6 ---
    total_capacity: int | None = 0
    arr_bonus_seats: int | None = 0
    yield_warning: bool | None = False
    remaining_seats: int = 0
    engine_status: str = "VERDE"

    # Cantiere 5: Risorse assegnate
    assigned_staff: List[AssignedResource] = []
    assigned_fleet: List[AssignedResource] = []


class RideAllocationUpdate(BaseModel):
    """Payload per aggiornare le assegnazioni staff/fleet di una discesa."""
    staff_ids: List[str] = []
    fleet_ids: List[str] = []
    # Campi opzionali per lazy-creation del turno (se non esiste ancora in DB)
    date: Optional[str] = None
    time: Optional[str] = None
    activity_id: Optional[str] = None


# ─── CRUSCOTTO OPERATIVO (Calendario Mensile) ────────────

class BookedRideSlot(BaseModel):
    """Singolo 'mattoncino' colorato nel calendario mensile."""
    time: str
    activity_code: str
    color_hex: str
    pax: int

class DailyScheduleResponse(BaseModel):
    """Un giorno nel calendario mensile: solo prenotazioni reali."""
    date: str
    booked_rides: List[BookedRideSlot] = []
    staff_count: int = 0


