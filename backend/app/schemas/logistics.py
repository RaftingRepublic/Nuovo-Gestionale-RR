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
    category: Optional[str] = "Generale"
    description: Optional[str] = None
    model_config = {"from_attributes": True}

class SystemSettingUpdate(BaseModel):
    value: str

class SystemSettingBulkItem(BaseModel):
    """Singolo setting nell'array di bulk update."""
    key: str
    value: str

class SystemSettingBulkUpdate(BaseModel):
    """Payload per aggiornamento massivo di più settings."""
    settings: List[SystemSettingBulkItem]


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
    capacity: int = 0
    has_tow_hitch: bool = False
    max_rafts: int = 0
    model_config = {"from_attributes": True}

class FleetCreate(BaseModel):
    name: str
    category: str = "RAFT"
    total_quantity: int = 1
    capacity_per_unit: int = 8
    capacity: int = 0
    has_tow_hitch: bool = False
    max_rafts: int = 0

class FleetUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    total_quantity: Optional[int] = None
    capacity_per_unit: Optional[int] = None
    capacity: Optional[int] = None
    has_tow_hitch: Optional[bool] = None
    max_rafts: Optional[int] = None

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
    roles: List[str] = []
    contract_periods: List[dict] = []
    is_active: bool
    model_config = {"from_attributes": True}

class StaffCreate(BaseModel):
    name: str
    contract_type: str = "FISSO"
    is_guide: bool = False
    is_driver: bool = False
    roles: List[str] = []

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    contract_type: Optional[str] = None
    is_guide: Optional[bool] = None
    is_driver: Optional[bool] = None
    roles: Optional[List[str]] = None
    contract_periods: Optional[List[dict]] = None
