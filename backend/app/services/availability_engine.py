""" Availability Engine — Cervello Matematico del Gestionale.
Calcola dinamicamente per ogni ride di una data:
total_capacity (posti totali = base + ARR bonus)
arr_bonus_seats (posti ereditati da transito fiume)
booked_pax (pax prenotati effettivi)
remaining_seats (posti residui)
status (VERDE / GIALLO / ROSSO)
Tiene conto di:
Gommoni disponibili (FleetDB RAFT - eccezioni)
Guide disponibili (Safety Kayak Hard Floor + eccezioni)
Overlap temporale (barche già in acqua a quell'ora)
Matrice ARR (River Ledger): AD→CL (60min) → FA (30min) per trasporto e consumo posti vuoti in cascata """

import math
import json
from datetime import date, datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session, joinedload
from app.models.calendar import (
    ActivityDB, DailyRideDB, OrderDB, StaffDB, FleetDB,
    ResourceExceptionDB, ActivitySubPeriodDB, SystemSettingDB
)

# Stati ordine che occupano posti
COUNTING_STATUSES = {"CONFERMATO", "COMPLETATO", "PAGATO", "IN_ATTESA"}

class AvailabilityEngine:
    """Motore di calcolo disponibilità per una singola data."""

    @staticmethod
    def _get_global_settings(db: Session) -> dict:
        """Legge le variabili dinamiche dal DB EAV e converte in interi in modo difensivo."""
        settings = {
            "raft_capacity": 8,
            "van_total_seats": 9,
            "van_driver_seats": 1,
            "van_guide_seats": 1,
        }
        
        rows = db.query(SystemSettingDB).all()
        for row in rows:
            try:
                settings[row.key] = int(row.value)
            except ValueError:
                pass
        
        settings["van_net_seats"] = max(1, settings["van_total_seats"] - settings["van_driver_seats"] - settings["van_guide_seats"])
        return settings

    @staticmethod
    def _get_arr_node(activity: ActivityDB) -> str:
        """Classifica l'attività nel fiume per la cascata ARR (AD -> CL -> FA)."""
        code = (activity.code or "").strip().upper()
        name = (activity.name or "").strip().upper()
        if code == "AD" or "ADVANCED" in name or "ADRENALINA" in name: return "AD"
        if code == "CL" or "CLASSIC" in name or "CLASSICA" in name: return "CL"
        if code == "FA" or "FAMILY" in name or "FAMIGLIA" in name: return "FA"
        return None

    @staticmethod
    def _parse_workflow_footprint(activity: ActivityDB) -> dict:
        """Estrae le logistics e i flows in modo difensivo."""
        workflow_schema = activity.workflow_schema

        if not workflow_schema:
            return {"logistics": {}, "flows": []}

        if isinstance(workflow_schema, str):
            try:
                schema_data = json.loads(workflow_schema)
                if isinstance(schema_data, str):
                    schema_data = json.loads(schema_data)
            except Exception:
                schema_data = {}
        else:
            schema_data = workflow_schema

        return {
            "logistics": schema_data.get("logistics", {}),
            "flows": schema_data.get("flows", [])
        }

    @staticmethod
    def _build_resource_timeline(ride_datetime: datetime, flows: list) -> list:
        """Scorre i flows e i blocks per calcolare l'assorbimento logistico (Two-Pass BPMN parser)."""
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

        for flow in flows:
            cursor = ride_datetime
            end_cursor = ride_end_datetime
            
            start_blocks = [b for b in flow.get("blocks", []) if b.get("anchor", "start") == "start"]
            end_blocks = [b for b in flow.get("blocks", []) if b.get("anchor", "start") == "end"]
            
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
    def _evaluate_ride_capacity(target_ride_id: Any, rides_data: dict, pool_rafts: int, pool_guides: int, pool_vans: int, settings: dict) -> dict:
        """Motore di Intersezione (Time-Array Slicer) con Safety Kayak Hard Floor."""
        usage_rafts = [0] * 1440
        usage_guides = [0] * 1440
        usage_vans = [0] * 1440
        
        van_net_seats = settings.get("van_net_seats", 7)

        for ride_id, data in rides_data.items():
            if ride_id == target_ride_id:
                continue
            
            needed_boats = data["needed_boats"]
            guides_needed = max(data["min_guides_absolute"], needed_boats) if needed_boats > 0 else 0
            vans_needed = math.ceil(data["booked_pax"] / van_net_seats) if data["requires_van"] and data["booked_pax"] > 0 else 0
            
            for block in data["timeline"]:
                start_m = max(0, min(1439, int(block["start"].hour * 60 + block["start"].minute)))
                end_m = max(0, min(1440, int(block["end"].hour * 60 + block["end"].minute)))
                
                resources = block.get("resources", [])
                has_raft = "RAFT" in resources
                has_guide = any(g in resources for g in ["RAF4", "RAF3", "HYD", "SK", "SH"])
                has_van = "VAN" in resources
                
                for m in range(start_m, end_m):
                    if has_raft: usage_rafts[m] += needed_boats
                    if has_guide: usage_guides[m] += guides_needed
                    if has_van: usage_vans[m] += vans_needed

        target_data = rides_data[target_ride_id]
        max_boats_for_target = 999
        yield_warning = False
        
        target_min_guides_abs = target_data["min_guides_absolute"]
        target_vans_needed = math.ceil((target_data["booked_pax"] + 1) / van_net_seats) if target_data["requires_van"] else 0

        for block in target_data["timeline"]:
            start_m = max(0, min(1439, int(block["start"].hour * 60 + block["start"].minute)))
            end_m = max(0, min(1440, int(block["end"].hour * 60 + block["end"].minute)))
            
            resources = block.get("resources", [])
            has_raft = "RAFT" in resources
            has_guide = any(g in resources for g in ["RAF4", "RAF3", "HYD", "SK", "SH"])
            has_van = "VAN" in resources
            
            for m in range(start_m, end_m):
                if has_raft:
                    max_boats_for_target = min(max_boats_for_target, pool_rafts - usage_rafts[m])
                if has_guide:
                    available_guides = pool_guides - usage_guides[m]
                    if available_guides < target_min_guides_abs:
                        max_boats_for_target = 0
                    else:
                        max_boats_for_target = min(max_boats_for_target, available_guides)
                if has_van:
                    if (pool_vans - usage_vans[m]) < target_vans_needed:
                        yield_warning = True

        return {
            "max_boats_for_target": max(0, max_boats_for_target),
            "yield_warning": yield_warning
        }

    @staticmethod
    def calculate_availability(db: Session, target_date: date) -> Dict[str, Dict[str, Any]]:
        date_str = target_date.strftime("%Y-%m-%d")
        settings = AvailabilityEngine._get_global_settings(db)
        raft_capacity = settings.get("raft_capacity", 8)

        pool_rafts = AvailabilityEngine._count_available_rafts(db, date_str)
        pool_guides = AvailabilityEngine._count_active_guides(db, target_date, date_str)
        pool_vans = AvailabilityEngine._count_available_vans(db, date_str)

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
        if not rides: return results

        # ─── RIVER LEDGER: Pass 1 Chronologico (Calcolo Matrice ARR & Consumi) ───
        rides_data = {}
        river_boats = [] # [{'arrive_CL': datetime, 'arrive_FA': datetime, 'empty_seats': int}]

        for ride in rides:
            activity = ride.activity
            if not activity: continue

            T = datetime.combine(target_date, ride.ride_time)
            booked_pax = AvailabilityEngine._calc_booked_pax(ride, raft_capacity)
            
            node = AvailabilityEngine._get_arr_node(activity)
            allow_arr = AvailabilityEngine._get_effective_bool(activity, "allow_intersections", target_date)
            
            arr_bonus_available = 0
            pax_to_seat = booked_pax

            # 1. Harvesting: Consuma i posti vuoti delle barche già in acqua
            if allow_arr and node:
                for b in river_boats:
                    if b['empty_seats'] <= 0: continue
                    match = False
                    if node == "CL" and b.get('arrive_CL') == T: match = True
                    elif node == "FA" and b.get('arrive_FA') == T: match = True
                    
                    if match:
                        arr_bonus_available += b['empty_seats']
                        take = min(pax_to_seat, b['empty_seats'])
                        b['empty_seats'] -= take
                        pax_to_seat -= take

            # 2. Quante barche FISICHE extra devo prendere dalla base?
            physical_pax = pax_to_seat
            needed_boats = math.ceil(physical_pax / raft_capacity) if physical_pax > 0 else 0

            # 3. Lancio nuove barche fisiche sul fiume (generano posti vuoti in cascata)
            if allow_arr and needed_boats > 0 and node in ["AD", "CL"]:
                new_empty_seats = (needed_boats * raft_capacity) - physical_pax
                if new_empty_seats > 0:
                    if node == "AD":
                        river_boats.append({
                            'arrive_CL': T + timedelta(minutes=60),
                            'arrive_FA': T + timedelta(minutes=90),
                            'empty_seats': new_empty_seats
                        })
                    elif node == "CL":
                        river_boats.append({
                            'arrive_CL': None,
                            'arrive_FA': T + timedelta(minutes=30),
                            'empty_seats': new_empty_seats
                        })

            footprint = AvailabilityEngine._parse_workflow_footprint(activity)
            timeline = AvailabilityEngine._build_resource_timeline(T, footprint.get("flows", []))
            logistics = footprint.get("logistics", {})

            rides_data[ride.id] = {
                "activity": activity,
                "ride": ride,
                "booked_pax": booked_pax,
                "needed_boats": needed_boats,  # Solo barche fisiche lanciate
                "timeline": timeline,
                "min_guides_absolute": int(logistics.get("min_guides", 1)),
                "requires_van": bool(logistics.get("requires_van", False)),
                "arr_bonus_seats": arr_bonus_available  # Totale posti gratis trovati passando
            }

        # ─── Semaforo Asimmetrico: Pass 2 (Valutazione Colli Bottiglia) ───
        for ride_id, data in rides_data.items():
            activity = data["activity"]
            booked_pax = data["booked_pax"]

            eval_data = AvailabilityEngine._evaluate_ride_capacity(
                ride_id, rides_data, pool_rafts, pool_guides, pool_vans, settings
            )

            # Il miracolo matematico: I posti ARR si sommano alla capienza della flotta fisica
            total_capacity = (eval_data["max_boats_for_target"] * raft_capacity) + data["arr_bonus_seats"]
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
                "arr_bonus_seats": data["arr_bonus_seats"],
                "booked_pax": booked_pax,
                "remaining_seats": remaining_seats,
                "debug_yield_warning": eval_data["yield_warning"],
            }

        return results

    # ─── HELPER FUNCTIONS ───
    @staticmethod
    def _count_available_rafts(db: Session, date_str: str) -> int:
        fleets = db.query(FleetDB).filter(FleetDB.category == "RAFT", FleetDB.is_active == True).all()
        total = sum(f.total_quantity for f in fleets)
        for fleet in fleets:
            exceptions = db.query(ResourceExceptionDB).filter(
                ResourceExceptionDB.resource_id == fleet.id,
                ResourceExceptionDB.resource_type == "FLEET",
                ResourceExceptionDB.is_available == False,
            ).all()
            for exc in exceptions:
                if date_str in (exc.dates or []): total -= 1
        return max(0, total)

    @staticmethod
    def _count_available_vans(db: Session, date_str: str) -> int:
        fleets = db.query(FleetDB).filter(FleetDB.category == "VAN", FleetDB.is_active == True).all()
        total = sum(f.total_quantity for f in fleets)
        for fleet in fleets:
            exceptions = db.query(ResourceExceptionDB).filter(
                ResourceExceptionDB.resource_id == fleet.id,
                ResourceExceptionDB.resource_type == "FLEET",
                ResourceExceptionDB.is_available == False,
            ).all()
            for exc in exceptions:
                if date_str in (exc.dates or []): total -= 1
        return max(0, total)

    @staticmethod
    def _count_active_guides(db: Session, target_date: date, date_str: str) -> int:
        all_guides = db.query(StaffDB).filter(StaffDB.is_guide == True, StaffDB.is_active == True).all()
        count = 0
        for guide in all_guides:
            if guide.contract_type == "FISSO":
                in_contract = False
                for cp in (guide.contract_periods or []):
                    try:
                        cp_start = date.fromisoformat(cp["start"])
                        cp_end = date.fromisoformat(cp["end"])
                        if cp_start <= target_date <= cp_end:
                            in_contract = True
                            break
                    except Exception:
                        pass
                if not in_contract: continue
                if AvailabilityEngine._has_exception(db, guide.id, "STAFF", date_str, False): continue
                count += 1
            elif guide.contract_type == "EXTRA":
                if AvailabilityEngine._has_exception(db, guide.id, "STAFF", date_str, True): count += 1
        return count

    @staticmethod
    def _has_exception(db: Session, res_id: str, res_type: str, date_str: str, is_avail: bool) -> bool:
        exceptions = db.query(ResourceExceptionDB).filter(
            ResourceExceptionDB.resource_id == res_id,
            ResourceExceptionDB.resource_type == res_type,
            ResourceExceptionDB.is_available == is_avail,
        ).all()
        for exc in exceptions:
            if date_str in (exc.dates or []): return True
        return False

    @staticmethod
    def _calc_booked_pax(ride: DailyRideDB, raft_capacity: int) -> int:
        pax = 0
        for o in ride.orders:
            if o.order_status not in COUNTING_STATUSES: continue
            if o.is_exclusive_raft: pax += math.ceil(o.total_pax / raft_capacity) * raft_capacity
            else: pax += o.total_pax
        return pax

    @staticmethod
    def _get_effective_bool(activity: ActivityDB, field: str, target_date: date) -> bool:
        date_str = target_date.strftime("%Y-%m-%d")
        for sp in (activity.sub_periods or []):
            if date_str in (sp.dates or []):
                override_val = getattr(sp, field, None)
                if override_val is not None: return override_val
        return getattr(activity, field, False)

    @staticmethod
    def _get_effective_int(activity: ActivityDB, field: str, target_date: date) -> int:
        date_str = target_date.strftime("%Y-%m-%d")
        for sp in (activity.sub_periods or []):
            if date_str in (sp.dates or []):
                override_val = getattr(sp, field, None)
                if override_val is not None: return override_val
        return getattr(activity, field, 0) or 0
