from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# --- ENUMS ---
PriorityColor = Literal["A", "B", "C", "D"]
# A = Green (To Load)
# B = Yellow (Almost Full)
# C = Red (Full)
# D = Blue (Open/Active)

GuideLevel = Literal["3_LIV", "4_LIV", "TRIP_LEADER"]
GuideSkill = Literal["RAFTING", "HYDROSPEED", "SAFETY_KAYAK"]
FleetType = Literal["RAFT", "VAN", "TRAILER"]
ActivityType = Literal["FAMILY", "CLASSICA", "ADVANCED", "SELECTION", "HYDRO_L1", "HYDRO_L2"]
AvailabilityType = Literal["AVAILABLE", "UNAVAILABLE"] # Disponibile / Ferie o Manutenzione

# --- STAFF ---
class StaffMember(BaseModel):
    id: str
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_guide: bool = False
    is_driver: bool = False
    is_photographer: bool = False
    guide_level: Optional[GuideLevel] = None
    guide_skills: List[GuideSkill] = [] 
    is_active: bool = True
    default_max_trips: int = 2 

class StaffCreate(BaseModel):
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_guide: bool = False
    is_driver: bool = False
    is_photographer: bool = False
    guide_level: Optional[GuideLevel] = None
    guide_skills: List[GuideSkill] = []

# --- FLEET ---
class FleetResource(BaseModel):
    id: str
    type: FleetType
    name: str
    capacity: int = 0
    priority: int = 1
    has_tow_hitch: bool = False
    is_active: bool = True

class FleetCreate(BaseModel):
    type: FleetType
    name: str
    capacity: int
    priority: int = 1
    has_tow_hitch: bool = False

# --- ACTIVITY RULES ---
class ActivityRule(BaseModel):
    id: str
    activity_type: ActivityType
    name: str 
    valid_from: str
    valid_to: str
    days_of_week: List[int] = []
    start_times: List[str] = []
    is_active: bool = True

class ActivityRuleCreate(BaseModel):
    activity_type: ActivityType
    name: str
    valid_from: str
    valid_to: str
    days_of_week: List[int]
    start_times: List[str]

# --- AVAILABILITY ---
class AvailabilityRule(BaseModel):
    id: str
    staff_id: str
    day_of_week: Optional[int] = None
    specific_date: Optional[str] = None
    start_hour: int
    end_hour: int
    type: AvailabilityType = "AVAILABLE"
    notes: Optional[str] = None 

class AvailabilityCreate(BaseModel):
    staff_id: str
    mode: Literal["RECURRING", "SPECIFIC"]
    days_of_week: List[int] = [] 
    specific_dates: List[str] = [] 
    start_hour: int
    end_hour: int
    type: AvailabilityType = "AVAILABLE"
    notes: Optional[str] = None

# --- RESERVATIONS (NEW) ---
OrderStatus = Literal["IN_ATTESA", "CONFERMATO", "CANCELLATO", "COMPLETATO"]
PaymentType = Literal["CONTANTI", "CARTA", "BONIFICO", "SATISPAY", "BUONO_REGALO", "ALTRO"]

class Reservation(BaseModel):
    id: str
    date: str # YYYY-MM-DD
    time: str # HH:MM
    activity_type: ActivityType
    pax: int
    # Backward-compat: customer_name kept but optional
    customer_name: Optional[str] = None
    contact_info: Optional[str] = None
    # New fields
    order_status: Optional[str] = "IN_ATTESA"
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    price_total: Optional[float] = 0
    price_paid: Optional[float] = 0
    payment_type: Optional[str] = None
    payment_datetime: Optional[str] = None
    gift_recipient: Optional[str] = None
    gift_code: Optional[str] = None
    language: Optional[str] = "it"
    notes: Optional[str] = None
    created_at: str

class ReservationCreate(BaseModel):
    date: str
    time: str
    activity_type: ActivityType
    pax: int
    customer_name: Optional[str] = None
    contact_info: Optional[str] = None
    order_status: Optional[str] = "IN_ATTESA"
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    price_total: Optional[float] = 0
    price_paid: Optional[float] = 0
    payment_type: Optional[str] = None
    payment_datetime: Optional[str] = None
    gift_recipient: Optional[str] = None
    gift_code: Optional[str] = None
    language: Optional[str] = "it"
    notes: Optional[str] = None

# --- MANUAL OVERRIDES (NEW) ---
class ManualOverride(BaseModel):
    id: str
    date: str
    time: str
    activity_type: ActivityType
    forced_status: PriorityColor
    notes: Optional[str] = None

class ManualOverrideCreate(BaseModel):
    date: str
    time: str
    activity_type: ActivityType
    forced_status: PriorityColor
    notes: Optional[str] = None

# --- PRIORITY & STATUS ---
class PriorityRequest(BaseModel):
    date_iso: str
    hour: int
    activity_type: str
    pax_request: int = 1

class PriorityResponse(BaseModel):
    status: PriorityColor
    color_hex: str
    description: str
    total_capacity: int
    remaining_capacity: int
    elastic_buffer: int
    active_guides: int
 
# --- DAILY VIEW (CALENDARIO) ---
class DailySlotView(BaseModel):
    time: str
    activity_type: ActivityType
    is_active: bool
    
    # Priority & Status (NEW)
    status: PriorityColor = "A"
    color_hex: str = "#4CAF50"
    status_desc: str = "Aperto"
    is_overridden: bool = False
    
    # Contatori Assoluti
    avail_guides: int = 0
    avail_drivers: int = 0
    avail_photographers: int = 0
    avail_vans: int = 0
    avail_rafts: int = 0
    avail_trailers: int = 0
    
    # Contatori Capacità 
    cap_guides_pax: int = 0
    cap_vans_pax: int = 0
    cap_rafts_pax: int = 0
    
    # Prenotazioni
    booked_pax: int = 0 