"""
Schemi Pydantic per il modulo Logistica:
- Impostazioni di Sistema
- Risorse Unificate (Fleet + ResourceException)
- Staff con dati logistici + contract_periods
"""

from pydantic import BaseModel
from typing import Optional, List


# ══════════════════════════════════════════
# SYSTEM SETTINGS
# ══════════════════════════════════════════
class SystemSettingResponse(BaseModel):
    key: str
    value: str
    model_config = {"from_attributes": True}

class SystemSettingUpdate(BaseModel):
    value: str


# ══════════════════════════════════════════
# FLEET (Flotta Mezzi)
# ══════════════════════════════════════════
class FleetResponse(BaseModel):
    id: str
    name: str
    category: str
    total_quantity: int
    capacity_per_unit: int
    is_active: bool
    model_config = {"from_attributes": True}

class FleetCreate(BaseModel):
    name: str
    category: str = "RAFT"
    total_quantity: int = 1
    capacity_per_unit: int = 8


# ══════════════════════════════════════════
# RESOURCE EXCEPTION (Diario Unificato)
# ══════════════════════════════════════════
class ResourceExceptionCreate(BaseModel):
    resource_id: str
    resource_type: str
    name: Optional[str] = None
    is_available: bool
    dates: List[str] = []

class ResourceExceptionResponse(BaseModel):
    id: str
    resource_id: str
    resource_type: str
    name: Optional[str] = None
    is_available: bool
    dates: List[str] = []
    model_config = {"from_attributes": True}

class ResourceExceptionUpdate(BaseModel):
    name: Optional[str] = None
    is_available: Optional[bool] = None
    dates: Optional[List[str]] = None


# ══════════════════════════════════════════
# STAFF
# ══════════════════════════════════════════
class StaffResponse(BaseModel):
    id: str
    name: str
    contract_type: str
    is_guide: bool
    is_driver: bool
    contract_periods: List[dict] = []
    is_active: bool
    model_config = {"from_attributes": True}

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    contract_type: Optional[str] = None
    is_guide: Optional[bool] = None
    is_driver: Optional[bool] = None
    contract_periods: Optional[List[dict]] = None
