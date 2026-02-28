"""
ride_helpers.py — Fallback locale per pax e semaforo.

I pax reali arrivano SOLO via external_pax_map (caricato async nel router).
Queste funzioni sono fallback a 0 per contesti dove la mappa non è disponibile.
"""

from app.models.calendar import DailyRideDB


def recalculate_ride_status(ride: DailyRideDB, db) -> int:
    """Fallback: il semaforo reale è nell'AvailabilityEngine con external_pax_map."""
    return 0


def calculate_booked_pax(ride: DailyRideDB) -> int:
    """Fallback: i pax reali sono iniettati nel router via external_pax_map."""
    return 0


