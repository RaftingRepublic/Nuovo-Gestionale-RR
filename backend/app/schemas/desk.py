from __future__ import annotations
from datetime import date, time, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

class TransactionCreate(BaseModel):
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

class DeskOrderCreate(BaseModel):
    @field_validator('date', mode='before')
    @classmethod
    def fix_date_format(cls, value):
        if value == "" or value is None:
            raise ValueError("⚠️ [FRONTEND BUG] Data mancante. DeskBookingForm.vue sta inviando una stringa vuota al posto della data del turno.")
        if isinstance(value, str):
            return value.replace('/', '-')[:10]
        return value

    @field_validator('time', mode='before')
    @classmethod
    def fix_time_format(cls, value):
        if value == "" or value is None:
            raise ValueError("⚠️ [FRONTEND BUG] Ora mancante. DeskBookingForm.vue sta inviando una stringa vuota al posto dell'orario del turno.")
        if isinstance(value, str):
            return value[:8]
        return value

    activity_id: str
    date: date
    time: time
    booker_name: str
    booker_phone: Optional[str] = None
    booker_email: Optional[str] = None
    pax: int = Field(ge=1, default=1)
    adjustments: float = Field(default=0.0)
    extras: List[dict] = Field(default_factory=list)
    transactions: List[TransactionCreate] = Field(default_factory=list)
    notes: Optional[str] = None

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

class DeskOrderResponse(BaseModel):
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
    total_paid: float = 0.0
    remaining: float = 0.0

class DeskOrderUpdate(BaseModel):
    pax: Optional[int] = Field(default=None, ge=1)
    adjustments: Optional[float] = None
    notes: Optional[str] = None
