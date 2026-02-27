"""
ride_helpers.py — Funzioni helper per calcolo pax e semaforo rides.

Estratte dal defunto router orders.py (Fase 8) per essere usate da
calendar.py e altri endpoint che ne hanno ancora bisogno.
"""

import math
from sqlalchemy.orm import Session
from app.models.calendar import DailyRideDB


# Capacità default (legacy, sarà dinamica in futuro via SystemSettings)
DEFAULT_CAPACITY = 16
RAFT_SIZE = 8

# Stati che "occupano posti" nel calcolo del semaforo
COUNTING_STATUSES = {"CONFERMATO", "COMPLETATO", "PAGATO", "IN_ATTESA"}


def recalculate_ride_status(ride: DailyRideDB, db: Session) -> int:
    """
    Ricalcola booked_pax e aggiorna il semaforo del ride.

    REGOLA ESCLUSIVA: se un ordine ha `is_exclusive_raft=True`,
    il conteggio posti è `ceil(total_pax / 8) * 8` (interi gommoni),
    non il numero reale di persone.

    Ritorna il booked_pax calcolato.
    """
    booked_pax = 0
    for o in ride.orders:
        if o.order_status not in COUNTING_STATUSES:
            continue
        if o.is_exclusive_raft:
            booked_pax += math.ceil(o.total_pax / RAFT_SIZE) * RAFT_SIZE
        else:
            booked_pax += o.total_pax

    # Aggiorna semaforo SOLO se non forzato manualmente
    if not ride.is_overridden:
        if booked_pax >= DEFAULT_CAPACITY:
            ride.status = "C"    # Rosso - Sold Out
        elif booked_pax >= 14:
            ride.status = "B"    # Giallo - Ultimi posti
        elif booked_pax >= 4:
            ride.status = "D"    # Blu - Confermato
        else:
            ride.status = "A"    # Verde - Da caricare

    return booked_pax


def calculate_booked_pax(ride: DailyRideDB) -> int:
    """Calcola booked_pax senza modificare il ride (per le GET)."""
    booked_pax = 0
    for o in ride.orders:
        if o.order_status not in COUNTING_STATUSES:
            continue
        if o.is_exclusive_raft:
            booked_pax += math.ceil(o.total_pax / RAFT_SIZE) * RAFT_SIZE
        else:
            booked_pax += o.total_pax
    return booked_pax
