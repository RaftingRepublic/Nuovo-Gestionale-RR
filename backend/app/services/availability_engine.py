"""
Availability Engine — Cervello Matematico del Gestionale.

Calcola dinamicamente per ogni ride di una data:
- total_capacity (posti totali = base + ARR bonus)
- arr_bonus_seats (posti ereditati da transito fiume)
- booked_pax (pax prenotati effettivi)
- remaining_seats (posti residui)
- status (VERDE / GIALLO / ROSSO)

Tiene conto di:
- Gommoni disponibili (FleetDB RAFT - eccezioni)
- Guide disponibili (FISSI in contratto senza assenze + EXTRA con turno)
- Overlap temporale (barche già in acqua a quell'ora)
- Matrice ARR: AD→CL (60min) → FA (30min) per trasporto posti vuoti
"""

import math
from datetime import date, datetime, timedelta
from typing import Dict, Any

from sqlalchemy.orm import Session, joinedload

from app.models.calendar import (
    ActivityDB, DailyRideDB, OrderDB, StaffDB, FleetDB,
    ResourceExceptionDB, ActivitySubPeriodDB,
)

# Stati ordine che occupano posti
COUNTING_STATUSES = {"CONFERMATO", "COMPLETATO"}
RAFT_PAX = 8  # Posti per gommone


class AvailabilityEngine:
    """Motore di calcolo disponibilità per una singola data."""

    @staticmethod
    def calculate_availability(db: Session, target_date: date) -> Dict[str, Dict[str, Any]]:
        """
        Calcola disponibilità per tutti i ride di `target_date`.

        Returns:
            Dict[ride_id] -> {
                "status": "VERDE" | "GIALLO" | "ROSSO",
                "total_capacity": int,
                "arr_bonus_seats": int,
                "booked_pax": int,
                "remaining_seats": int,
            }
        """
        date_str = target_date.strftime("%Y-%m-%d")

        # ═══ STEP 1: Tetto giornaliero ═══
        total_rafts = AvailabilityEngine._count_available_rafts(db, date_str)
        active_guides = AvailabilityEngine._count_active_guides(db, target_date, date_str)
        max_concurrent_boats = max(0, min(total_rafts, active_guides))

        # ═══ STEP 2: Carica ride della data ═══
        rides = (
            db.query(DailyRideDB)
            .options(
                joinedload(DailyRideDB.activity).joinedload(ActivityDB.sub_periods),
                joinedload(DailyRideDB.orders),
            )
            .filter(DailyRideDB.ride_date == target_date)
            .order_by(DailyRideDB.ride_time)
            .all()
        )

        if not rides:
            return {}

        # ═══ STEP 3: Scorrimento e overlap ═══
        launched_boats = []  # [{"start": datetime, "end": datetime, "count": int}]
        river_transit = {}   # {"HH:MM": {"boats_in_water": int, "pax_in_water": int}}
        results = {}

        for ride in rides:
            activity = ride.activity
            if not activity:
                continue

            # Costruisci datetime completo per T
            T = datetime.combine(target_date, ride.ride_time)

            # Calcola booked_pax
            booked_pax = AvailabilityEngine._calc_booked_pax(ride)

            # Calcola barche già in acqua a quest'ora
            active_boats_at_T = sum(
                b["count"] for b in launched_boats
                if b["start"] <= T < b["end"]
            )
            available_base_boats = max(0, max_concurrent_boats - active_boats_at_T)
            base_capacity = available_base_boats * RAFT_PAX

            # Recupera parametri effettivi (override SubPeriod o base)
            allow_arr = AvailabilityEngine._get_effective_bool(
                activity, "allow_intersections", target_date
            )
            yellow_threshold = AvailabilityEngine._get_effective_int(
                activity, "yellow_threshold", target_date
            )
            overbooking_limit = AvailabilityEngine._get_effective_int(
                activity, "overbooking_limit", target_date
            )
            activity_class = activity.activity_class or "RAFTING"

            arr_bonus_seats = 0

            if allow_arr and activity_class == "RAFTING":
                # ═══ LOGICA ARR ═══
                transit = river_transit.get(
                    T.strftime("%H:%M"),
                    {"boats_in_water": 0, "pax_in_water": 0}
                )
                arr_bonus_seats = max(0, (transit["boats_in_water"] * RAFT_PAX) - transit["pax_in_water"])
                total_capacity = base_capacity + arr_bonus_seats

                # Barche da lanciare dalla base per i pax eccedenti il bonus
                pax_to_accommodate_from_base = max(0, booked_pax - arr_bonus_seats)
                new_boats_launched = math.ceil(pax_to_accommodate_from_base / RAFT_PAX) if pax_to_accommodate_from_base > 0 else 0

                # Registra lancio
                launched_boats.append({
                    "start": T,
                    "end": T + timedelta(hours=activity.duration_hours),
                    "count": new_boats_launched,
                })

                # Calcola flusso in uscita verso la prossima stazione ARR
                out_boats = transit["boats_in_water"] + new_boats_launched
                out_pax = transit["pax_in_water"] + booked_pax
                code = activity.code.upper() if activity.code else ""

                if code == "AD":
                    next_time = T + timedelta(minutes=60)
                    next_key = next_time.strftime("%H:%M")
                    existing = river_transit.get(next_key, {"boats_in_water": 0, "pax_in_water": 0})
                    river_transit[next_key] = {
                        "boats_in_water": existing["boats_in_water"] + out_boats,
                        "pax_in_water": existing["pax_in_water"] + out_pax,
                    }
                elif code == "CL":
                    next_time = T + timedelta(minutes=30)
                    next_key = next_time.strftime("%H:%M")
                    existing = river_transit.get(next_key, {"boats_in_water": 0, "pax_in_water": 0})
                    river_transit[next_key] = {
                        "boats_in_water": existing["boats_in_water"] + out_boats,
                        "pax_in_water": existing["pax_in_water"] + out_pax,
                    }
            else:
                # ═══ NO ARR (Hydro, Kayak, o ARR disabilitato) ═══
                total_capacity = base_capacity
                new_boats_launched = math.ceil(booked_pax / RAFT_PAX) if booked_pax > 0 else 0
                launched_boats.append({
                    "start": T,
                    "end": T + timedelta(hours=activity.duration_hours),
                    "count": new_boats_launched,
                })

            # ═══ STEP 4: Semaforo ═══
            remaining_seats = total_capacity - booked_pax

            if remaining_seats <= -overbooking_limit:
                status = "ROSSO"
            elif remaining_seats <= yellow_threshold:
                status = "GIALLO"
            else:
                status = "VERDE"

            results[ride.id] = {
                "status": status,
                "total_capacity": total_capacity,
                "arr_bonus_seats": arr_bonus_seats,
                "booked_pax": booked_pax,
                "remaining_seats": remaining_seats,
            }

        return results

    # ─── HELPER: Conteggio Gommoni disponibili ───
    @staticmethod
    def _count_available_rafts(db: Session, date_str: str) -> int:
        """Somma total_quantity di tutti i RAFT attivi, meno eccezioni assenza."""
        fleets = db.query(FleetDB).filter(
            FleetDB.category == "RAFT",
            FleetDB.is_active == True,  # noqa: E712
        ).all()

        total = sum(f.total_quantity for f in fleets)

        # Sottrai eccezioni flotta per questa data
        for fleet in fleets:
            exceptions = db.query(ResourceExceptionDB).filter(
                ResourceExceptionDB.resource_id == fleet.id,
                ResourceExceptionDB.resource_type == "FLEET",
                ResourceExceptionDB.is_available == False,  # noqa: E712
            ).all()
            for exc in exceptions:
                if date_str in (exc.dates or []):
                    # Rimuovi un'unità per eccezione (es. guasto)
                    total -= 1

        return max(0, total)

    # ─── HELPER: Conteggio Guide attive ───
    @staticmethod
    def _count_active_guides(db: Session, target_date: date, date_str: str) -> int:
        """
        Guide disponibili:
        - FISSI con is_guide=True + contratto valido per la data + no eccezioni assenza
        - EXTRA con is_guide=True + eccezione presenza per la data
        """
        all_guides = db.query(StaffDB).filter(
            StaffDB.is_guide == True,  # noqa: E712
            StaffDB.is_active == True,  # noqa: E712
        ).all()

        count = 0
        for guide in all_guides:
            if guide.contract_type == "FISSO":
                # Verifica se la data cade in un periodo contrattuale
                in_contract = False
                for cp in (guide.contract_periods or []):
                    cp_start = date.fromisoformat(cp["start"])
                    cp_end = date.fromisoformat(cp["end"])
                    if cp_start <= target_date <= cp_end:
                        in_contract = True
                        break
                if not in_contract:
                    continue

                # Verifica che non abbia eccezione assenza
                has_absence = AvailabilityEngine._has_exception(
                    db, guide.id, "STAFF", date_str, is_available=False
                )
                if has_absence:
                    continue

                count += 1

            elif guide.contract_type == "EXTRA":
                # Extra: presente SOLO se ha eccezione presenza
                has_presence = AvailabilityEngine._has_exception(
                    db, guide.id, "STAFF", date_str, is_available=True
                )
                if has_presence:
                    count += 1

        return count

    # ─── HELPER: Check eccezione ───
    @staticmethod
    def _has_exception(db: Session, resource_id: str, resource_type: str,
                       date_str: str, is_available: bool) -> bool:
        """Controlla se esiste un'eccezione per questa risorsa in questa data."""
        exceptions = db.query(ResourceExceptionDB).filter(
            ResourceExceptionDB.resource_id == resource_id,
            ResourceExceptionDB.resource_type == resource_type,
            ResourceExceptionDB.is_available == is_available,
        ).all()
        for exc in exceptions:
            if date_str in (exc.dates or []):
                return True
        return False

    # ─── HELPER: Booked pax per ride ───
    @staticmethod
    def _calc_booked_pax(ride: DailyRideDB) -> int:
        """Calcola posti prenotati contando gli ordini validi."""
        pax = 0
        for o in ride.orders:
            if o.order_status not in COUNTING_STATUSES:
                continue
            if o.is_exclusive_raft:
                pax += math.ceil(o.total_pax / RAFT_PAX) * RAFT_PAX
            else:
                pax += o.total_pax
        return pax

    # ─── HELPER: Parametro effettivo (override SubPeriod o base) ───
    @staticmethod
    def _get_effective_bool(activity: ActivityDB, field: str, target_date: date) -> bool:
        """Ritorna il valore booleano effettivo, con override da SubPeriod se presente."""
        date_str = target_date.strftime("%Y-%m-%d")
        for sp in (activity.sub_periods or []):
            if date_str in (sp.dates or []):
                override_val = getattr(sp, field, None)
                if override_val is not None:
                    return override_val
        return getattr(activity, field, False)

    @staticmethod
    def _get_effective_int(activity: ActivityDB, field: str, target_date: date) -> int:
        """Ritorna il valore intero effettivo, con override da SubPeriod se presente."""
        date_str = target_date.strftime("%Y-%m-%d")
        for sp in (activity.sub_periods or []):
            if date_str in (sp.dates or []):
                override_val = getattr(sp, field, None)
                if override_val is not None:
                    return override_val
        return getattr(activity, field, 0) or 0
