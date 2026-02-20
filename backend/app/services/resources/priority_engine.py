import json
import uuid
import math
import os
import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from app.schemas.resources import (
    StaffMember, StaffCreate, 
    FleetResource, FleetCreate, 
    ActivityRule, ActivityRuleCreate, DailySlotView,
    AvailabilityRule, AvailabilityCreate, 
    PriorityResponse, PriorityColor,
    Reservation, ReservationCreate,
    ManualOverride, ManualOverrideCreate
)

class PriorityEngine:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parents[3]
        self.storage_dir = self.base_dir / "storage" / "resources"
        
        self.staff_file = self.storage_dir / "staff.json"
        self.fleet_file = self.storage_dir / "fleet.json"
        self.activity_rules_file = self.storage_dir / "activity_rules.json"
        self.rules_file = self.storage_dir / "availability_rules.json"
        self.reservations_file = self.storage_dir / "reservations.json"
        self.overrides_file = self.storage_dir / "overrides.json"
        self.config_file = self.storage_dir / "config.json"
        
        self.rule_cache = None # Optimization for bulk operations
        
        self._ensure_files()

    # --- CHECK AVAILABILITY ---
    def _is_available(self, resource_id: str, date: str, hour_start: int, duration: int = 3) -> bool:
        if self.rule_cache is not None:
            rules = self.rule_cache
        else:
            rules = self._load(self.rules_file)
            
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            dow = dt.weekday()
        except: return False
        
        hour_end = hour_start + duration
        res_rules = [r for r in rules if r['staff_id'] == resource_id]
        
        # 1. Check Indisponibilità Specifica
        unavailable_rule = next((r for r in res_rules if r.get('specific_date') == date and r.get('type') == 'UNAVAILABLE'), None)
        if unavailable_rule: return False

        # 2. Check Disponibilità Specifica
        specific = next((r for r in res_rules if r.get('specific_date') == date and r.get('type') == 'AVAILABLE'), None)
        if specific:
            return specific['start_hour'] <= hour_start and specific['end_hour'] >= hour_end
            
        # 3. Check Ricorrenza
        recurring = next((r for r in res_rules if r.get('day_of_week') == dow and not r.get('specific_date') and r.get('type') == 'AVAILABLE'), None)
        if recurring:
            return recurring['start_hour'] <= hour_start and recurring['end_hour'] >= hour_end
            
        return False

    def _ensure_files(self):
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        for f in [self.staff_file, self.fleet_file, self.activity_rules_file, self.rules_file, self.reservations_file, self.overrides_file]:
            if not f.exists(): self._save(f, [])
        if not self.config_file.exists():
            self._save(self.config_file, {
                "raft_capacity": 8, 
                "safety_buffer_guides": 1,
                "min_pax_confirm": 4, # Green -> Blue threshold
                "safety_pax_buffer": 2 # Blue -> Yellow threshold (slots remaining)
            })

    def _load(self, path: Path) -> list:
        try: return json.loads(path.read_text(encoding="utf-8"))
        except: return []

    def _save(self, path: Path, data: any):
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # --- DELETE HELPERS ---
    def _delete_item(self, path: Path, item_id: str):
        data = self._load(path)
        new_data = [d for d in data if d.get('id') != item_id]
        self._save(path, new_data)
        if path in [self.staff_file, self.fleet_file]:
            rules = self._load(self.rules_file)
            rules = [r for r in rules if r.get('staff_id') != item_id]
            self._save(self.rules_file, rules)

    # --- STAFF ---
    def add_staff(self, payload: StaffCreate) -> StaffMember:
        data = self._load(self.staff_file)
        new_obj = payload.dict()
        new_obj.update({"id": str(uuid.uuid4()), "is_active": True, "default_max_trips": 2})
        data.append(new_obj)
        self._save(self.staff_file, data)
        return StaffMember(**new_obj)

    def list_staff(self) -> List[StaffMember]:
        data = self._load(self.staff_file)
        res = []
        for d in data:
            if 'role' in d: # Legacy
                d.update({'is_guide': d['role']=='GUIDE', 'is_driver': d['role']=='DRIVER', 'is_photographer': False, 'guide_skills': []})
            try: res.append(StaffMember(**d))
            except: pass
        return res

    def delete_staff(self, id: str): self._delete_item(self.staff_file, id)

    # --- FLEET ---
    def add_fleet(self, payload: FleetCreate) -> FleetResource:
        data = self._load(self.fleet_file)
        new_obj = payload.dict()
        new_obj.update({"id": str(uuid.uuid4()), "is_active": True})
        data.append(new_obj)
        data.sort(key=lambda x: x['priority'])
        self._save(self.fleet_file, data)
        return FleetResource(**new_obj)

    def list_fleet(self) -> List[FleetResource]:
        return [FleetResource(**d) for d in self._load(self.fleet_file)]

    def delete_fleet(self, id: str): self._delete_item(self.fleet_file, id)

    # --- ACTIVITY RULES ---
    def add_activity_rule(self, payload: ActivityRuleCreate) -> ActivityRule:
        data = self._load(self.activity_rules_file)
        new_obj = payload.dict()
        new_obj.update({"id": str(uuid.uuid4()), "is_active": True})
        data.append(new_obj)
        self._save(self.activity_rules_file, data)
        return ActivityRule(**new_obj)

    def list_activity_rules(self) -> List[ActivityRule]:
        return [ActivityRule(**d) for d in self._load(self.activity_rules_file)]

    def delete_activity_rule(self, id: str):
        self._delete_item(self.activity_rules_file, id)

    # --- RESERVATIONS ---
    def add_reservation(self, payload: ReservationCreate) -> Reservation:
        data = self._load(self.reservations_file)
        new_obj = payload.dict()
        new_obj.update({
            "id": str(uuid.uuid4()), 
            "created_at": datetime.now().isoformat()
        })
        data.append(new_obj)
        self._save(self.reservations_file, data)
        return Reservation(**new_obj)

    def list_reservations(self, date: Optional[str] = None) -> List[Reservation]:
        data = self._load(self.reservations_file)
        res = []
        for d in data:
            if date and d.get('date') != date: continue
            res.append(Reservation(**d))
        return res

    def delete_reservation(self, id: str):
        self._delete_item(self.reservations_file, id)

    # --- MANUAL OVERRIDES ---
    def add_manual_override(self, payload: ManualOverrideCreate) -> ManualOverride:
        data = self._load(self.overrides_file)
        # Remove existing override for same slot if any
        data = [d for d in data if not (
            d['date'] == payload.date and 
            d['time'] == payload.time and 
            d['activity_type'] == payload.activity_type
        )]
        
        new_obj = payload.dict()
        new_obj.update({"id": str(uuid.uuid4())})
        data.append(new_obj)
        self._save(self.overrides_file, data)
        return ManualOverride(**new_obj)

    def list_manual_overrides(self, date: Optional[str] = None) -> List[ManualOverride]:
        data = self._load(self.overrides_file)
        res = []
        for d in data:
            if date and d.get('date') != date: continue
            res.append(ManualOverride(**d))
        return res
        
    def delete_manual_override(self, id: str):
        self._delete_item(self.overrides_file, id)

    # --- HELPER ORARI ROBUSTO ---
    def _parse_hour(self, time_str: str) -> int:
        try:
            clean = time_str.replace('.', ':').strip()
            if ':' in clean: return int(clean.split(':')[0])
            return int(clean)
        except: return 9

    # --- LOGICA PRIORITY STATUS ---
    def _determine_status(self, booked: int, capacity: int, override: Optional[PriorityColor]) -> dict:
        if override:
            desc_map = {"A": "Aperto", "B": "Quasi Pieno", "C": "Pieno", "D": "Confermato"}
            hex_map = {"A": "#4CAF50", "B": "#FFC107", "C": "#F44336", "D": "#2196F3"}
            return {"code": override, "hex": hex_map[override], "desc": desc_map[override]}

        config = self._load(self.config_file)
        MIN_CONFIRM = config.get("min_pax_confirm", 4)
        PAX_BUFFER = config.get("safety_pax_buffer", 2)
        
        if capacity == 0:
             return {"code": "C", "hex": "#F44336", "desc": "Chiuso (No Guide)"}
             
        if booked >= capacity:
             return {"code": "C", "hex": "#F44336", "desc": "Sold Out"}
             
        remaining = capacity - booked
        
        if remaining < PAX_BUFFER:
            return {"code": "B", "hex": "#FFC107", "desc": "Ultimi Posti"} # Yellow
            
        if booked >= MIN_CONFIRM:
            return {"code": "D", "hex": "#2196F3", "desc": "Confermato"} # Blue
            
        return {"code": "A", "hex": "#4CAF50", "desc": "Da Caricare"} # Green

    # --- CALENDARIO GIORNALIERO ---
    def get_daily_schedule(self, target_date: str) -> List[DailySlotView]:
        rules = self.list_activity_rules()
        staff = self.list_staff()
        fleet = self.list_fleet()
        reservations = self.list_reservations(target_date)
        overrides = self.list_manual_overrides(target_date)
        
        config = self._load(self.config_file)
        RAFT_CAP = config.get("raft_capacity", 8)
        
        try:
            dt = datetime.strptime(target_date, "%Y-%m-%d")
            dow = dt.weekday()
        except: return []
        
        daily_slots = []
        active_times = []
        
        for r in rules:
            if not r.is_active: continue
            try:
                s = datetime.strptime(r.valid_from, "%Y-%m-%d")
                e = datetime.strptime(r.valid_to, "%Y-%m-%d")
                if s <= dt <= e and dow in r.days_of_week:
                    for t in r.start_times: active_times.append((t, r.activity_type))
            except: continue
        
        # Elimina duplicati orari se ci sono più regole
        active_times = list(set(active_times))
        
        for time_str, type_act in active_times:
            start_h = self._parse_hour(time_str)
            
            avail_guides = [s for s in staff if s.is_guide and self._is_available(s.id, target_date, start_h)]
            avail_drivers = [s for s in staff if s.is_driver and self._is_available(s.id, target_date, start_h)]
            avail_photos = [s for s in staff if s.is_photographer and self._is_available(s.id, target_date, start_h)]
            
            avail_rafts = [f for f in fleet if f.type == 'RAFT' and self._is_available(f.id, target_date, start_h)]
            avail_vans = [f for f in fleet if f.type == 'VAN' and self._is_available(f.id, target_date, start_h)]
            avail_trailers = [f for f in fleet if f.type == 'TRAILER' and self._is_available(f.id, target_date, start_h)]
            
            cap_guides = len(avail_guides) * RAFT_CAP
            cap_rafts = sum(r.capacity for r in avail_rafts)
            cap_vans = sum(v.capacity for v in avail_vans)
            
            # Calcolo Capacità Effettiva
            real_capacity = min(cap_guides, cap_rafts) 
            
            # Calcolo Prenotazioni
            slot_res = [r for r in reservations if r.time == time_str and r.activity_type == type_act]
            booked_pax = sum(r.pax for r in slot_res)
            
            # Check Override
            override_entry = next((o for o in overrides if o.time == time_str and o.activity_type == type_act), None)
            forced_status = override_entry.forced_status if override_entry else None
            
            status_info = self._determine_status(booked_pax, real_capacity, forced_status)

            daily_slots.append(DailySlotView(
                time=time_str,
                activity_type=type_act,
                is_active=True,
                status=status_info["code"],
                color_hex=status_info["hex"],
                status_desc=status_info["desc"],
                is_overridden=bool(override_entry),
                avail_guides=len(avail_guides),
                avail_drivers=len(avail_drivers),
                avail_photographers=len(avail_photos),
                avail_rafts=len(avail_rafts),
                avail_vans=len(avail_vans),
                avail_trailers=len(avail_trailers),
                cap_guides_pax=cap_guides,
                cap_rafts_pax=cap_rafts,
                cap_vans_pax=cap_vans,
                booked_pax=booked_pax
            ))
        
        daily_slots.sort(key=lambda x: self._parse_hour(x.time))
        return daily_slots

    # --- AVAILABILITY ---
    def get_availability_rules(self, staff_id: str) -> List[AvailabilityRule]:
        rules = self._load(self.rules_file)
        return [AvailabilityRule(**r) for r in rules if r['staff_id'] == staff_id]

    def add_availability(self, payload: AvailabilityCreate) -> List[AvailabilityRule]:
        data = self._load(self.rules_file)
        created = []
        def _create(day=None, date=None):
            if date: data[:] = [x for x in data if not (x['staff_id'] == payload.staff_id and x.get('specific_date') == date)]
            
            r = { 
                "id": str(uuid.uuid4()), "staff_id": payload.staff_id, 
                "day_of_week": day, "specific_date": date, 
                "start_hour": payload.start_hour, "end_hour": payload.end_hour, 
                "type": payload.type, "notes": payload.notes
            }
            data.append(r)
            created.append(AvailabilityRule(**r))

        if payload.mode == "RECURRING":
            for d in payload.days_of_week: _create(day=d)
        elif payload.mode == "SPECIFIC":
            for d in payload.specific_dates: _create(date=d)

        self._save(self.rules_file, data)
        return created

    # --- PRIORITY CORE (Richiesta Puntuale) ---
    def calculate_priority(self, date_iso: str, hour: int, current_pax: int, request_pax: int, activity_type: str = "CLASSICA") -> PriorityResponse:
        schedule = self.get_daily_schedule(date_iso)
        
        target_slot = None
        for slot in schedule:
            s_h = self._parse_hour(slot.time)
            if s_h == hour and slot.activity_type == activity_type:
                target_slot = slot
                break
        
        if not target_slot:
            return PriorityResponse(
                status="C", color_hex="#F44336", description="Chiuso", 
                total_capacity=0, remaining_capacity=0, elastic_buffer=0, active_guides=0
            )
            
        total_capacity = min(target_slot.cap_guides_pax, target_slot.cap_rafts_pax)
        real_booked = target_slot.booked_pax
        new_total = real_booked + request_pax
        
        status_info = self._determine_status(new_total, total_capacity, None)
        
        if target_slot.status == "C":
             status_info = {"code": "C", "hex": "#F44336", "desc": "Chiuso (Manuale)"}

        return PriorityResponse(
            status=status_info["code"], 
            color_hex=status_info["hex"], 
            description=status_info["desc"], 
            total_capacity=total_capacity, 
            remaining_capacity=max(0, total_capacity - real_booked), 
            elastic_buffer=0, 
            active_guides=target_slot.avail_guides
        )

    # --- MONTH OVERVIEW ---
    def get_month_overview(self, year: int, month: int, detailed: bool = False) -> List[dict]:
        import calendar
        num_days = calendar.monthrange(year, month)[1]
        
        rules = self.list_activity_rules()
        reservations = self.list_reservations() # Load once
        overrides = self.list_manual_overrides()
        staff = self.list_staff() if detailed else []
        
        overview = []
        
        # Optimization: Preload Availability Rules
        self.rule_cache = self._load(self.rules_file)
        
        try:
            for day in range(1, num_days + 1):
                date_str = f"{year}-{month:02d}-{day:02d}"
                try:
                    dt = datetime(year, month, day)
                    dow = dt.weekday()
                except: continue
            
                # 1. Check if CLOSED (No rules)
                is_open = False
                active_rules_for_day = []
                for r in rules:
                    if not r.is_active: continue
                    try:
                        s = datetime.strptime(r.valid_from, "%Y-%m-%d")
                        e = datetime.strptime(r.valid_to, "%Y-%m-%d")
                        if s <= dt <= e and dow in r.days_of_week:
                            is_open = True
                            active_rules_for_day.append(r)
                    except: continue
                
                # 2. Reservations count
                day_res = [r for r in reservations if r.date == date_str]
                total_booked = sum(r.pax for r in day_res)
                
                # 3. Status determination (Simplified)
                status = 'A' # Da Caricare
                if not is_open: status = 'C' # Chiuso
                elif total_booked > 0: status = 'D' # Confermato (se c'è gente)
                
                # Check Override
                day_overrides = [o for o in overrides if o.date == date_str]
                if day_overrides and all(o.forced_status == 'C' for o in day_overrides):
                    status = 'C'
                
                # Color map matching Frontend
                hex_map = {"A": "#4CAF50", "B": "#FFC107", "C": "#F44336", "D": "#2196F3"}
                
                day_data = {
                    "date": date_str,
                    "status": status,
                    "color": hex_map.get(status, "#ddd"),
                    "total_booked": total_booked,
                    "is_closed": not is_open
                }

                if detailed and is_open:
                    slots_data = []
                    # Determine active times from rules
                    active_times = []
                    for r in active_rules_for_day:
                         for t in r.start_times: active_times.append((t, r.activity_type))
                    active_times = list(set(active_times))
                    
                    for time_str, type_act in active_times:
                        # Filter Reservations
                        slot_res = [r for r in day_res if r.time == time_str and r.activity_type == type_act]
                        slot_booked = sum(r.pax for r in slot_res)
                        
                        # Calculate Available Guides & Capacity
                        start_h = self._parse_hour(time_str)
                        
                        slot_guides = []
                        for s in staff:
                            if s.is_guide and self._is_available(s.id, date_str, start_h):
                                display_name = s.name
                                if s.first_name:
                                    display_name = f"{s.first_name} {s.last_name[0]}." if s.last_name else s.first_name
                                slot_guides.append(display_name)
                                
                        slot_drivers = []
                        for s in staff:
                            if s.is_driver and self._is_available(s.id, date_str, start_h):
                                display_name = s.name
                                if s.first_name:
                                    display_name = f"{s.first_name} {s.last_name[0]}." if s.last_name else s.first_name
                                slot_drivers.append(display_name)

                        # Determine Capacity (simplified logic: 8 pax per guide)
                        config = self._load(self.config_file)
                        RAFT_CAP = config.get("raft_capacity", 8)
                        cap_guides_pax = len(slot_guides) * RAFT_CAP
                        
                        # We don't check rafts here for speed/simplicity unless critical, 
                        # enforcing Guide capacity as primary constraint for overview.
                        slot_capacity = cap_guides_pax

                        # Simple status check for color
                        status_info = self._determine_status(slot_booked, slot_capacity, None)

                        slots_data.append({
                            "time": time_str,
                            "activity_type": type_act,
                            "booked_pax": slot_booked,
                            "capacity": slot_capacity,
                            "avail_guides": len(slot_guides), 
                            "guides": slot_guides,
                            "drivers": slot_drivers,
                            "color_hex": status_info["hex"]
                        })
                    
                    # Sort slots by time
                    slots_data.sort(key=lambda x: self._parse_hour(x['time']))
                    day_data["slots"] = slots_data
                else:
                    day_data["slots"] = []
                    
                overview.append(day_data)
            
        finally:
            self.rule_cache = None

        return overview