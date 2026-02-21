"""
Schemi Pydantic V2 per il dominio Calendario.
"""

from __future__ import annotations

from datetime import date, time
from typing import Optional, List
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
    is_active: bool
    sub_periods: List[ActivitySubPeriodResponse] = []


class ActivitySeasonUpdate(BaseModel):
    manager: Optional[str] = None
    price: Optional[float] = None
    season_start: Optional[date] = None
    season_end: Optional[date] = None
    default_times: Optional[List[str]] = None
    allow_intersections: Optional[bool] = None
    activity_class: Optional[str] = None
    yellow_threshold: Optional[int] = None
    overbooking_limit: Optional[int] = None
    sub_periods: Optional[List[ActivitySubPeriodCreate]] = None


# ─── DISCESA GIORNALIERA ─────────────────────────────────

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
    total_capacity: int = 0
    arr_bonus_seats: int = 0
    remaining_seats: int = 0
    engine_status: str = "VERDE"


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

