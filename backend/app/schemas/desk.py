"""
Schemi Pydantic V2 per il dominio Desk POS (Cantiere 2).

DeskOrderCreate: payload dal form segreteria con multi-transazione in-line.
TransactionCreate/Response: singolo movimento contabile.
DeskOrderResponse: ordine completo con transazioni e registrazioni annidate.
"""

from __future__ import annotations

from datetime import date, time, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── TRANSAZIONE ──────────────────────────────────────────

class TransactionCreate(BaseModel):
    """Singola transazione inline nel form desk."""
    amount: float = Field(ge=0, description="Importo del pagamento")
    method: str = Field(description="CASH, SUMUP, BONIFICO, PARTNERS")
    type: str = Field(default="SALDO", description="CAPARRA o SALDO")
    note: Optional[str] = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    amount: float
    method: str
    type: str
    note: Optional[str] = None
    timestamp: Optional[datetime] = None


# ─── ORDINE DESK (CREAZIONE) ─────────────────────────────

class DeskOrderCreate(BaseModel):
    """
    Payload per creare un ordine dal bancone (Desk POS).

    Il prezzo viene CALCOLATO dal server: (pax * prezzo_base) + extras + adjustments.
    Le transazioni vengono registrate inline per gestire pagamenti misti
    (caparra bonifico + saldo POS/Cash + Voucher).
    """
    activity_id: str
    date: date
    time: time
    booker_name: str
    booker_phone: Optional[str] = None
    booker_email: Optional[str] = None
    pax: int = Field(ge=1, default=1)
    adjustments: float = Field(default=0.0, description="Penali no-show (+) o sconti (-)")
    extras: List[dict] = Field(default_factory=list, description='Es. [{"name":"Foto","price":15}]')
    transactions: List[TransactionCreate] = Field(default_factory=list)
    notes: Optional[str] = None


# ─── REGISTRAZIONE (Mini, per annidamento ordine) ────────

class DeskRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nome: str
    cognome: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    is_lead: bool = False
    status: str = "EMPTY"
    firaft_status: str = "NON_RICHIESTO"


# ─── ORDINE DESK (RISPOSTA) ──────────────────────────────

class DeskOrderResponse(BaseModel):
    """Ordine completo con transazioni e registrazioni annidate."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    ride_id: str
    booker_name: Optional[str] = None
    booker_phone: Optional[str] = None
    booker_email: Optional[str] = None
    total_pax: int
    price_total: float = 0.0
    adjustments: float = 0.0
    extras: list = []
    order_status: str = "IN_ATTESA"
    source: str = "DESK"
    notes: Optional[str] = None
    customer_name: Optional[str] = None

    transactions: List[TransactionResponse] = []
    registrations: List[DeskRegistrationResponse] = []

    # Calcolati
    total_paid: float = 0.0
    remaining: float = 0.0


# ─── AGGIORNAMENTO ORDINE (Drop-outs & Penali) ──────────

class DeskOrderUpdate(BaseModel):
    """Payload per aggiornare pax e/o penali di un ordine esistente."""
    pax: Optional[int] = Field(default=None, ge=1)
    adjustments: Optional[float] = None
    notes: Optional[str] = None
