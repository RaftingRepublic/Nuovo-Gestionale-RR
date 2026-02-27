"""
Schemi Pydantic V2 per la lettura profonda Matrioska e semafori.

Fase 8 (27/02/2026): OrderCreate e OrderResponse ELIMINATI.
Il router legacy è stato incenerito. Restano gli schemi usati
da calendar.py (Matrioska, Override).
"""

from __future__ import annotations

from datetime import date, time
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── SCHEMI PER LETTURA PROFONDA "MATRIOSKA" ────────────

class RegistrationResponse(BaseModel):
    """Dati base di un partecipante (per la modale dettagli discesa)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    nome: str
    cognome: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    is_minor: bool = False
    status: str = "EMPTY"
    is_lead: bool = False
    firaft_status: str = "NON_RICHIESTO"


class OrderWithRegistrationsResponse(BaseModel):
    """Un ordine con la lista dei suoi partecipanti annidati."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    ride_id: str
    total_pax: int
    order_status: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    price_total: float = 0.0
    is_exclusive_raft: bool = False
    discount_applied: float = 0.0
    registrations: List[RegistrationResponse] = []


class DailyRideDetailResponse(BaseModel):
    """
    Risposta "Matrioska" per la modale dettagli discesa.

    Contiene: Ride → [Ordini → [Registrazioni]]
    + campi arricchiti (activity_name, color_hex, booked_pax).
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    activity_id: str
    ride_date: date
    ride_time: time
    status: str
    is_overridden: bool
    notes: Optional[str] = None

    # Campi arricchiti
    activity_name: str = ""
    color_hex: str = "#4CAF50"
    booked_pax: int = 0

    # Campi calcolati dall'AvailabilityEngine
    total_capacity: int = 0
    arr_bonus_seats: int = 0
    remaining_seats: int = 0
    engine_status: str = "VERDE"

    # La "Matrioska": ordini con registrazioni annidate
    orders: List[OrderWithRegistrationsResponse] = []


# ─── SCHEMA PER FORZATURA SEMAFORO (Override) ────────────

class RideOverrideRequest(BaseModel):
    """Body per forzare/rilasciare il semaforo di una discesa."""
    forced_status: str = Field(
        default="A",
        description="Stato forzato: A (Verde), B (Giallo), C (Rosso), D (Blu)"
    )
    clear_override: bool = Field(
        default=False,
        description="Se True, rilascia la forzatura e ricalcola il semaforo automaticamente"
    )
