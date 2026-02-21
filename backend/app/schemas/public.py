"""
Schema per le API pubbliche (check-in digitale).
Cantiere 3: Auto-Slotting via Magic Link.
"""

from pydantic import BaseModel
from typing import Optional


class PublicOrderInfo(BaseModel):
    """Info discesa per l'header del form consenso."""
    activity_name: str
    date: str
    time: str


class FillSlotPayload(BaseModel):
    """Dati inviati dal form di consenso per riempire uno slot vuoto."""
    first_name: str
    last_name: str
    email: str = ""
    phone: str = ""
    is_minor: bool = False
    accepted_terms: bool = True
