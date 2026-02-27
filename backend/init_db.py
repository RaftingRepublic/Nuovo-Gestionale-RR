"""
init_db.py — Script di inizializzazione Database.
Eseguire con:  venv\\Scripts\\python.exe init_db.py
"""
import sys, os
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine, Base, SessionLocal
from app.models.registration import RegistrationDB
from app.models.calendar import (
    ActivityDB, DailyRideDB, StaffDB, FleetDB,
    ResourceExceptionDB, SystemSettingDB, ActivitySubPeriodDB,
    # OrderDB, TransactionDB, CustomerDB: INCENERITE Fase 8
)


def init_database():
    print("💣 Eliminazione tabelle esistenti...")
    Base.metadata.drop_all(bind=engine)
    print("🔧 Ricostruzione tabelle da zero...")
    Base.metadata.create_all(bind=engine)
    print(f"✅ {len(Base.metadata.tables)} tabelle create!")

    db = SessionLocal()
    try:
        # ─── ATTIVITÀ ────────────────────────────────────
        print("\n📦 Inserimento Attività...")
        fa = ActivityDB(
            code="FA", name="Rafting Family", price=45.0,
            duration_hours=2.5, color_hex="#4682dc",
            manager="Anatre", river_segments="T3",
            season_start=date(2026, 5, 1), season_end=date(2026, 10, 31),
            default_times=["09:00", "11:30", "14:00", "16:30"],
            allow_intersections=False,
            activity_class="RAFTING", yellow_threshold=8, overbooking_limit=0,
        )
        h1 = ActivityDB(
            code="H1", name="Hydrospeed Base", price=55.0,
            duration_hours=2.0, color_hex="#e74c3c",
            manager="Grape", river_segments="T1",
            default_times=["10:00", "14:00"],
            allow_intersections=False,
            activity_class="HYDRO", yellow_threshold=2, overbooking_limit=0,
        )
        cl = ActivityDB(
            code="CL", name="Rafting Classic", price=60.0,
            duration_hours=3.0, color_hex="#2196F3",
            manager="Grape", river_segments="T2",
            season_start=date(2026, 4, 15), season_end=date(2026, 9, 30),
            default_times=["09:00", "14:00"],
            allow_intersections=False,
            activity_class="RAFTING", yellow_threshold=8, overbooking_limit=0,
        )
        ad = ActivityDB(
            code="AD", name="Rafting Advanced", price=70.0,
            duration_hours=3.0, color_hex="#9C27B0",
            manager="Anatre", river_segments="T1,T2",
            season_start=date(2026, 6, 1), season_end=date(2026, 9, 15),
            default_times=["09:00"],
            allow_intersections=True,
            activity_class="RAFTING", yellow_threshold=8, overbooking_limit=4,
        )
        sl = ActivityDB(
            code="SL", name="Rafting Selection", price=55.0,
            duration_hours=3.0, color_hex="#1976D2",
            manager="Grape", river_segments="T2",
            season_start=date(2026, 5, 1), season_end=date(2026, 9, 30),
            default_times=["10:00", "14:00"],
            allow_intersections=False,
            activity_class="RAFTING", yellow_threshold=8, overbooking_limit=0,
        )
        db.add_all([fa, h1, cl, ad, sl])
        db.flush()
        print(f"   ✅ FA  RAFTING  soglia=8  over=0   id={fa.id}")
        print(f"   ✅ H1  HYDRO    soglia=2  over=0   id={h1.id}")
        print(f"   ✅ CL  RAFTING  soglia=8  over=0   id={cl.id}")
        print(f"   ✅ AD  RAFTING  soglia=8  over=4   ARR=ON  id={ad.id}")
        print(f"   ✅ SL  RAFTING  soglia=8  over=0   id={sl.id}")

        # ─── STAFF ───────────────────────────────────────
        print("\n👷 Inserimento Staff...")
        g1 = StaffDB(
            name="Miriam", contract_type="FISSO", is_guide=True, is_driver=False,
            contract_periods=[{"start": "2026-05-01", "end": "2026-09-30"}],
        )
        g2 = StaffDB(
            name="Tony", contract_type="FISSO", is_guide=True, is_driver=False,
            contract_periods=[{"start": "2026-04-15", "end": "2026-10-15"}],
        )
        g3 = StaffDB(name="Stefano", contract_type="EXTRA", is_guide=True, is_driver=True)
        db.add_all([g1, g2, g3])
        db.flush()
        print(f"   ✅ Miriam  (FISSO, Guida, Mag-Set)")
        print(f"   ✅ Tony    (FISSO, Guida, Apr-Ott)")
        print(f"   ✅ Stefano (EXTRA, Guida+Autista)")

        # ─── FLEET ──────────────────────────────────────
        print("\n🚢 Inserimento Flotta...")
        raft_fleet = FleetDB(name="Flotta Gommoni", category="RAFT", total_quantity=10, capacity_per_unit=8)
        van_fleet = FleetDB(name="Flotta Furgoni", category="VAN", total_quantity=2, capacity_per_unit=9)
        db.add_all([raft_fleet, van_fleet])
        db.flush()
        print(f"   ✅ Gommoni: 10 x 8 posti")
        print(f"   ✅ Furgoni: 2 x 9 posti")

        # ─── ECCEZIONI RISORSE ───────────────────────────
        print("\n📅 Inserimento Eccezioni...")
        db.add_all([
            ResourceExceptionDB(
                resource_id=g3.id, resource_type="STAFF",
                name="Turno febbraio", is_available=True, dates=["2026-02-21"],
            ),
            ResourceExceptionDB(
                resource_id=raft_fleet.id, resource_type="FLEET",
                name="Guasto Ferragosto", is_available=False, dates=["2026-08-15"],
            ),
        ])

        # ─── REGISTRAZIONI ──────────────────────────────
        print("🎫 Inserimento Registrazioni...")
        db.add_all([
            RegistrationDB(
                id="reg-test-1", nome="Mario", cognome="Rossi",
                email="mario@test.it", telefono="333-1111111",
                is_minor=False, locked=True, created_at=datetime.utcnow(),
                firaft_status="NON_RICHIESTO",
            ),
            RegistrationDB(
                id="reg-test-2", nome="Luigi", cognome="Verdi",
                email="luigi@test.it", telefono="333-2222222",
                is_minor=False, locked=True, created_at=datetime.utcnow(),
                firaft_status="NON_RICHIESTO",
            ),
        ])

        db.commit()
        print("\n" + "=" * 55)
        print("✅ DATABASE INIZIALIZZATO CON SUCCESSO!")
        print("=" * 55)
        print(f"\n📋 Riepilogo Yield Management:")
        print(f"   FA  RAFTING  🟡=8  📈=0")
        print(f"   H1  HYDRO   🟡=2  📈=0")
        print(f"   CL  RAFTING  🟡=8  📈=0")
        print(f"   AD  RAFTING  🟡=8  📈=4  ARR=✅")

    except Exception as e:
        print(f"❌ Errore: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
