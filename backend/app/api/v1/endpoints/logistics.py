"""
Endpoints Logistica Operativa:
- /settings: Configurazioni globali (ARR kill-switch, ecc.)
- /fleet: Flotta risorse (Gommoni, Furgoni)
- /resource-exceptions: Diario Unificato eccezioni risorse
- /staff: Lista staff
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.calendar import (
    StaffDB, FleetDB, ResourceExceptionDB, SystemSettingDB,
)
from app.schemas.logistics import (
    SystemSettingResponse, SystemSettingUpdate, SystemSettingBulkUpdate,
    FleetResponse, FleetCreate, FleetUpdate,
    ResourceExceptionCreate, ResourceExceptionResponse, ResourceExceptionUpdate,
    StaffResponse, StaffCreate, StaffUpdate,
)

router = APIRouter()


# ══════════════════════════════════════════
# SYSTEM SETTINGS
# ══════════════════════════════════════════
@router.get("/settings", response_model=List[SystemSettingResponse])
def list_settings(db: Session = Depends(get_db)):
    """Ritorna tutte le impostazioni di sistema."""
    return db.query(SystemSettingDB).all()


@router.patch("/settings/{key}", response_model=SystemSettingResponse)
def update_setting(key: str, payload: SystemSettingUpdate, db: Session = Depends(get_db)):
    """Aggiorna il valore di un'impostazione (es. ARR_ENABLED → true/false)."""
    setting = db.query(SystemSettingDB).filter(SystemSettingDB.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' non trovato")
    setting.value = payload.value
    db.commit()
    db.refresh(setting)
    return setting


@router.put("/settings/bulk", response_model=List[SystemSettingResponse])
def bulk_update_settings(payload: SystemSettingBulkUpdate, db: Session = Depends(get_db)):
    """Aggiorna in batch tutte le impostazioni inviate dal pannello di controllo."""
    updated = []
    for item in payload.settings:
        setting = db.query(SystemSettingDB).filter(SystemSettingDB.key == item.key).first()
        if setting:
            setting.value = item.value
            updated.append(setting)
    db.commit()
    for s in updated:
        db.refresh(s)
    return updated


# ══════════════════════════════════════════
# FLEET (Flotta)
# ══════════════════════════════════════════
@router.get("/fleet", response_model=List[FleetResponse])
def list_fleet(db: Session = Depends(get_db)):
    """Ritorna tutti i mezzi attivi."""
    return db.query(FleetDB).filter(FleetDB.is_active == True).all()  # noqa: E712


@router.post("/fleet", response_model=FleetResponse, status_code=201)
def create_fleet(payload: FleetCreate, db: Session = Depends(get_db)):
    """Crea un nuovo mezzo della flotta."""
    new_fleet = FleetDB(
        name=payload.name,
        category=payload.category,
        total_quantity=payload.total_quantity,
        capacity_per_unit=payload.capacity_per_unit,
        capacity=payload.capacity,
        has_tow_hitch=payload.has_tow_hitch,
        max_rafts=payload.max_rafts,
    )
    db.add(new_fleet)
    db.commit()
    db.refresh(new_fleet)
    return new_fleet


@router.delete("/fleet/{fleet_id}", status_code=204)
def delete_fleet(fleet_id: str, db: Session = Depends(get_db)):
    """Archivia (soft-delete) un mezzo della flotta."""
    fleet = db.query(FleetDB).filter(FleetDB.id == fleet_id).first()
    if not fleet:
        raise HTTPException(status_code=404, detail="Mezzo non trovato")
    fleet.is_active = False
    db.commit()
    return None


@router.patch("/fleet/{fleet_id}", response_model=FleetResponse)
def update_fleet(fleet_id: str, payload: FleetUpdate, db: Session = Depends(get_db)):
    """Aggiorna i dati di un mezzo della flotta."""
    fleet = db.query(FleetDB).filter(FleetDB.id == fleet_id).first()
    if not fleet:
        raise HTTPException(status_code=404, detail="Mezzo non trovato")

    for field in ['name', 'category', 'total_quantity', 'capacity_per_unit', 'capacity', 'has_tow_hitch', 'max_rafts']:
        val = getattr(payload, field, None)
        if val is not None:
            setattr(fleet, field, val)

    db.commit()
    db.refresh(fleet)
    return fleet


# ══════════════════════════════════════════
# RESOURCE EXCEPTIONS (Diario Unificato)
# ══════════════════════════════════════════
@router.get("/resource-exceptions", response_model=List[ResourceExceptionResponse])
def list_resource_exceptions(
    resource_type: Optional[str] = Query(None, description="Filtra per STAFF o FLEET"),
    resource_id: Optional[str] = Query(None, description="Filtra per ID risorsa"),
    db: Session = Depends(get_db),
):
    """Lista eccezioni con filtro opzionale per tipo o ID risorsa."""
    q = db.query(ResourceExceptionDB)
    if resource_type:
        q = q.filter(ResourceExceptionDB.resource_type == resource_type)
    if resource_id:
        q = q.filter(ResourceExceptionDB.resource_id == resource_id)
    return q.all()


@router.post("/resource-exceptions", response_model=ResourceExceptionResponse, status_code=201)
def create_resource_exception(payload: ResourceExceptionCreate, db: Session = Depends(get_db)):
    """Crea una nuova eccezione per una risorsa (Staff o Fleet)."""
    new_exc = ResourceExceptionDB(
        resource_id=payload.resource_id,
        resource_type=payload.resource_type,
        name=payload.name,
        is_available=payload.is_available,
        dates=payload.dates,
    )
    db.add(new_exc)
    db.commit()
    db.refresh(new_exc)
    return new_exc


@router.delete("/resource-exceptions/{exception_id}", status_code=204)
def delete_resource_exception(exception_id: str, db: Session = Depends(get_db)):
    """Elimina un'eccezione per ID."""
    exc = db.query(ResourceExceptionDB).filter(ResourceExceptionDB.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Eccezione non trovata")
    db.delete(exc)
    db.commit()
    return None


# ══════════════════════════════════════════
# STAFF
# ══════════════════════════════════════════
@router.get("/staff", response_model=List[StaffResponse])
def list_staff(db: Session = Depends(get_db)):
    """Ritorna tutti gli staff attivi."""
    return db.query(StaffDB).filter(StaffDB.is_active == True).all()  # noqa: E712


@router.post("/staff", response_model=StaffResponse, status_code=201)
def create_staff(payload: StaffCreate, db: Session = Depends(get_db)):
    """Crea un nuovo membro dello staff."""
    new_staff = StaffDB(
        name=payload.name,
        contract_type=payload.contract_type,
        is_guide=payload.is_guide,
        is_driver=payload.is_driver,
        roles=payload.roles,
    )
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    return new_staff


@router.delete("/staff/{staff_id}", status_code=204)
def delete_staff(staff_id: str, db: Session = Depends(get_db)):
    """Elimina (soft-delete) un membro dello staff."""
    staff = db.query(StaffDB).filter(StaffDB.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff non trovato")
    staff.is_active = False
    db.commit()
    return None


@router.patch("/staff/{staff_id}", response_model=StaffResponse)
def update_staff(staff_id: str, payload: StaffUpdate, db: Session = Depends(get_db)):
    """Aggiorna i dati di uno staff (nome, ruoli, contract_periods)."""
    staff = db.query(StaffDB).filter(StaffDB.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff non trovato")

    if payload.name is not None:
        staff.name = payload.name
    if payload.contract_type is not None:
        staff.contract_type = payload.contract_type
    if payload.is_guide is not None:
        staff.is_guide = payload.is_guide
    if payload.is_driver is not None:
        staff.is_driver = payload.is_driver
    if payload.roles is not None:
        staff.roles = payload.roles
    if payload.contract_periods is not None:
        staff.contract_periods = payload.contract_periods

    db.commit()
    db.refresh(staff)
    return staff

