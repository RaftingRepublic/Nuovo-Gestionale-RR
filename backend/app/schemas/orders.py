"""
Schemi Pydantic V2 per il dominio Ordini.

OrderCreate: payload in ingresso dal frontend/Swagger per creare un ordine.
OrderResponse: payload in uscita, include dati calcolati (ride_id, status, ecc.).
"""

from __future__ import annotations

from datetime import date, time
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    """
    Payload per creare un nuovo ordine.

    Il frontend invia activity_id + ride_date + ride_time.
    Il backend cerca (o crea) il DailyRide corrispondente.
    Il prezzo viene CALCOLATO dal server (pricing engine incorruttibile).
    """
    activity_id: str
    ride_date: date                              # "2025-06-21"
    ride_time: time                              # "09:00"
    total_pax: int = Field(default=1, ge=1)
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    price_total: Optional[float] = None          # Ignorato dal server, calcolato internamente
    payment_type: str = Field(
        default="CARTA",
        description="Metodo di pagamento: 'CARTA' (confermato subito) o 'BONIFICO' (resta in attesa)"
    )
    is_exclusive_raft: bool = Field(
        default=False,
        description="True se il gruppo vuole gommone privato (prenota interi gommoni da 8)"
    )

    # Ponte d'Oro: lista opzionale di ID registrazioni-kiosk da agganciare
    registration_ids: List[str] = []


class OrderResponse(BaseModel):
    """Risposta dopo la creazione di un ordine."""

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

    # Campi arricchiti dall'endpoint (non colonne dirette di OrderDB)
    ride_status: str = "A"
    linked_registrations: int = 0


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
