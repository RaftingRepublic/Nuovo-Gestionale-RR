from app.db.database import SessionLocal
from app.models.calendar import StaffDB, FleetDB

db = SessionLocal()
print("--- TEST STAFF (Primi 3) ---")
guides = db.query(StaffDB).filter(StaffDB.is_guide == True).limit(3).all()
for g in guides:
    print(f"Nome: {g.name}, Attivo: {g.is_active}, Contratti: {g.contract_periods}")

print("--- TEST FLOTTA (Primi 3 Raft, Primi 3 Van) ---")
rafts = db.query(FleetDB).filter(FleetDB.category == 'RAFT').limit(3).all()
for r in rafts:
    print(f"Raft: {r.name}, Qty: {r.total_quantity}, CapLegacy: {r.capacity_per_unit}, CapV5: {r.capacity}, Attivo: {r.is_active}")

vans = db.query(FleetDB).filter(FleetDB.category == 'VAN').limit(3).all()
for v in vans:
    print(f"Van: {v.name}, Qty: {v.total_quantity}, CapLegacy: {v.capacity_per_unit}, CapV5: {v.capacity}, Attivo: {v.is_active}")

db.close()
