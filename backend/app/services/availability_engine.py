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
import json
from datetime import date, datetime, timedelta
from typing import Dict, Any, List

from sqlalchemy.orm import Session, joinedload

from app.models.calendar import (
    ActivityDB, DailyRideDB, OrderDB, StaffDB, FleetDB,
    ResourceExceptionDB, ActivitySubPeriodDB,
)

# Stati ordine che occupano posti
# CONFERMATO = web/bonifico confermato, COMPLETATO = turno concluso,
# PAGATO = saldato dal desk POS, IN_ATTESA = ordine con caparra parziale (conta comunque posti)
COUNTING_STATUSES = {"CONFERMATO", "COMPLETATO", "PAGATO", "IN_ATTESA"}


class AvailabilityEngine:
    """Motore di calcolo disponibilità per una singola data."""

    @staticmethod
    def _get_global_settings(db: Session) -> dict:
        """Legge le variabili dinamiche dal DB."""
        # TODO: Aggancio reale con il DB (Pannello Variabili).
        # Per ora restituiamo un dizionario difensivo temporaneo.
        return {
            "raft_capacity": 8,
            "van_seats": 9,
            "total_vans": 2,
        }

    @staticmethod
    def _parse_workflow_footprint(activity: ActivityDB) -> dict:
        """Estrae le logistics e i flows in modo difensivo."""
        workflow_schema = activity.workflow_schema

        if not workflow_schema:
            return {"logistics": {}, "flows": []}

        if isinstance(workflow_schema, str):
            try:
                schema_data = json.loads(workflow_schema)
                # Gestione stringhe double-escaped
                if isinstance(schema_data, str):
                    schema_data = json.loads(schema_data)
            except Exception:
                schema_data = {}
        else:
            schema_data = workflow_schema

        logistics = schema_data.get("logistics", {})
        flows = schema_data.get("flows", [])

        return {
            "logistics": logistics,
            "flows": flows
        }

    @staticmethod
    def _build_resource_timeline(ride_datetime: datetime, flows: list) -> list:
        """Scorre i flows e i blocks per calcolare l'assorbimento logistico (Two-Pass BPMN parser)."""
        # Pass 1: Trova la durata massima assoluta (Orizzonte degli eventi dell'attività)
        max_duration_min = 0
        for flow in flows:
            flow_duration = sum(
                b.get("duration_min", 0) 
                for b in flow.get("blocks", []) 
                if b.get("anchor", "start") == "start"
            )
            if flow_duration > max_duration_min:
                max_duration_min = flow_duration
                
        ride_end_datetime = ride_datetime + timedelta(minutes=max_duration_min)
        timeline = []

        # Pass 2: Costruisci la timeline assoluta
        for flow in flows:
            cursor = ride_datetime
            end_cursor = ride_end_datetime
            
            start_blocks = [b for b in flow.get("blocks", []) if b.get("anchor", "start") == "start"]
            end_blocks = [b for b in flow.get("blocks", []) if b.get("anchor", "start") == "end"]
            
            # I blocchi start avanzano nel tempo
            for block in start_blocks:
                duration_min = block.get("duration_min", 0)
                block_start = cursor
                block_end = cursor + timedelta(minutes=duration_min)
                cursor = block_end
                
                timeline.append({
                    "resources": block.get("resources", []),
                    "start": block_start,
                    "end": block_end,
                    "block_code": block.get("code", "")
                })
                
            # I blocchi end arretrano dal fondo (reversed per concatenarli correttamente)
            for block in reversed(end_blocks):
                duration_min = block.get("duration_min", 0)
                block_end = end_cursor
                block_start = block_end - timedelta(minutes=duration_min)
                end_cursor = block_start
                
                timeline.append({
                    "resources": block.get("resources", []),
                    "start": block_start,
                    "end": block_end,
                    "block_code": block.get("code", "")
                })

        return timeline

    @staticmethod
    def _evaluate_ride_capacity(target_ride_id: Any, rides_data: dict, pool_rafts: int, pool_guides: int, pool_vans: int) -> dict:
        """
        Motore di Intersezione (Time-Array Slicer): calcola i colli di bottiglia sovrapponendo i consumi al minuto.
        """
        usage_rafts = [0] * 1440
        usage_guides = [0] * 1440
        usage_vans = [0] * 1440

        # Costruisci l'assorbimento degli ALTRI
        for ride_id, data in rides_data.items():
            if ride_id == target_ride_id:
                continue
            
            needed_boats = data["needed_boats"]
            for block in data["timeline"]:
                start_m = int(block["start"].hour * 60 + block["start"].minute)
                end_m = int(block["end"].hour * 60 + block["end"].minute)
                
                # Clamp per evitare index out of bounds
                start_m = max(0, min(1439, start_m))
                end_m = max(0, min(1440, end_m))
                
                resources = block.get("resources", [])
                has_raft = "RAFT" in resources
                has_guide = any(g in resources for g in ["RAF4", "RAF3", "HYD", "SK", "SH"])
                has_van = "VAN" in resources
                
                for m in range(start_m, end_m):
                    if has_raft:
                        usage_rafts[m] += needed_boats
                    if has_guide:
                        usage_guides[m] += needed_boats
                    if has_van:
                        usage_vans[m] += needed_boats

        # Analisi dei colli di bottiglia del TARGET (Sweep)
        target_data = rides_data[target_ride_id]
        max_boats_for_target = 999
        yield_warning = False

        for block in target_data["timeline"]:
            start_m = int(block["start"].hour * 60 + block["start"].minute)
            end_m = int(block["end"].hour * 60 + block["end"].minute)
            
            start_m = max(0, min(1439, start_m))
            end_m = max(0, min(1440, end_m))
            
            resources = block.get("resources", [])
            has_raft = "RAFT" in resources
            has_guide = any(g in resources for g in ["RAF4", "RAF3", "HYD", "SK", "SH"])
            has_van = "VAN" in resources
            
            for m in range(start_m, end_m):
                if has_raft:
                    available = pool_rafts - usage_rafts[m]
                    max_boats_for_target = min(max_boats_for_target, available)
                if has_guide:
                    available = pool_guides - usage_guides[m]
                    max_boats_for_target = min(max_boats_for_target, available)
                if has_van:
                    available = pool_vans - usage_vans[m]
                    if available < 1:
                        yield_warning = True

        return {
            "max_boats_for_target": max(0, max_boats_for_target),
            "yield_warning": yield_warning
        }

    @staticmethod
    def calculate_availability(db: Session, target_date: date) -> Dict[str, Dict[str, Any]]:
        """
        Calcola disponibilità per tutti i ride di `target_date`.
        """
        date_str = target_date.strftime("%Y-%m-%d")
        settings = AvailabilityEngine._get_global_settings(db)
        raft_capacity = settings.get("raft_capacity", 8)

        # Il Fondo del Sacco Globale all'alba
        pool_rafts = AvailabilityEngine._count_available_rafts(db, date_str)
        pool_guides = AvailabilityEngine._count_active_guides(db, target_date, date_str)
        pool_vans = settings.get("total_vans", 2)

        # ═══ Carica ride della data ═══
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

        results = {}

        if not rides:
            return results

        # ─── Pre-calcolo dei Consumi (Censimento pass 1) ───
        rides_data = {}
        for ride in rides:
            activity = ride.activity
            if not activity:
                continue

            T = datetime.combine(target_date, ride.ride_time)
            booked_pax = AvailabilityEngine._calc_booked_pax(ride, raft_capacity)
            needed_boats = math.ceil(booked_pax / raft_capacity) if booked_pax > 0 else 0

            footprint = AvailabilityEngine._parse_workflow_footprint(activity)
            timeline = AvailabilityEngine._build_resource_timeline(T, footprint.get("flows", []))

            rides_data[ride.id] = {
                "activity": activity,
                "ride": ride,
                "booked_pax": booked_pax,
                "needed_boats": needed_boats,
                "timeline": timeline,
            }

        # ─── Il Semaforo Asimmetrico (Censimento pass 2) ───
        for ride_id, data in rides_data.items():
            activity = data["activity"]
            booked_pax = data["booked_pax"]

            eval_data = AvailabilityEngine._evaluate_ride_capacity(
                ride_id, rides_data, pool_rafts, pool_guides, pool_vans
            )

            total_capacity = eval_data["max_boats_for_target"] * raft_capacity
            remaining_seats = total_capacity - booked_pax

            overbooking_limit = AvailabilityEngine._get_effective_int(activity, "overbooking_limit", target_date)
            yellow_threshold = AvailabilityEngine._get_effective_int(activity, "yellow_threshold", target_date)

            if remaining_seats <= -overbooking_limit:
                status = "ROSSO"
            elif eval_data["yield_warning"] or remaining_seats <= yellow_threshold:
                status = "GIALLO"
            else:
                status = "VERDE"

            results[ride_id] = {
                "status": status,
                "total_capacity": total_capacity,
                "arr_bonus_seats": 0,
                "booked_pax": booked_pax,
                "remaining_seats": remaining_seats,
                "debug_yield_warning": eval_data["yield_warning"],
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
    def _calc_booked_pax(ride: DailyRideDB, raft_capacity: int) -> int:
        """Calcola posti prenotati contando ordini validi."""
        pax = 0
        for o in ride.orders:
            if o.order_status not in COUNTING_STATUSES:
                continue
            if o.is_exclusive_raft:
                pax += math.ceil(o.total_pax / raft_capacity) * raft_capacity
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
