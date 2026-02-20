from fastapi import APIRouter, Query, HTTPException
from typing import List
from app.schemas.resources import (
    StaffMember, StaffCreate, 
    FleetResource, FleetCreate,
    ActivityRule, ActivityRuleCreate, DailySlotView,
    AvailabilityRule, AvailabilityCreate, 
    PriorityResponse
)
from app.services.resources.priority_engine import PriorityEngine

router = APIRouter()
engine = PriorityEngine()

# --- STAFF ---
@router.get("/staff", response_model=List[StaffMember])
def list_staff(): return engine.list_staff()

@router.post("/staff", response_model=StaffMember)
def create_staff(payload: StaffCreate): return engine.add_staff(payload)

@router.delete("/staff/{id}")
def delete_staff(id: str): return engine.delete_staff(id)

# --- FLEET ---
@router.get("/fleet", response_model=List[FleetResource])
def list_fleet(): return engine.list_fleet()

@router.post("/fleet", response_model=FleetResource)
def create_fleet(payload: FleetCreate): return engine.add_fleet(payload)

@router.delete("/fleet/{id}")
def delete_fleet(id: str): return engine.delete_fleet(id)

# --- ACTIVITY RULES ---
@router.get("/activity-rules", response_model=List[ActivityRule])
def list_activity_rules(): return engine.list_activity_rules()

@router.post("/activity-rules", response_model=ActivityRule)
def create_activity_rule(payload: ActivityRuleCreate): return engine.add_activity_rule(payload)

@router.delete("/activity-rules/{id}")
def delete_activity_rule(id: str): return engine.delete_activity_rule(id)

@router.get("/daily-schedule", response_model=List[DailySlotView])
def get_daily_schedule(date: str = Query(..., regex=r"^\d{4}-\d{2}-\d{2}$")):
    return engine.get_daily_schedule(date)

@router.get("/month-overview")
def get_month_overview(year: int = Query(...), month: int = Query(...), detailed: bool = Query(False)):
    return engine.get_month_overview(year, month, detailed)

# --- AVAILABILITY ---
@router.get("/availability/{resource_id}", response_model=List[AvailabilityRule])
def get_availability(resource_id: str):
    return engine.get_availability_rules(resource_id)

@router.post("/availability", response_model=List[AvailabilityRule])
def set_availability(payload: AvailabilityCreate): return engine.add_availability(payload)

# --- CORE ---
@router.get("/priority", response_model=PriorityResponse)
def calculate_priority(
    date: str = Query(...), 
    hour: int = Query(...), 
    current_pax: int = Query(0), 
    request_pax: int = Query(1),
    activity_type: str = Query("CLASSICA")
):
    return engine.calculate_priority(date, hour, current_pax, request_pax, activity_type)