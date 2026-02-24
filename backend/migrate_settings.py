"""
migrate_settings.py — Migrazione per il Pannello Variabili Logistiche.

Aggiunge le colonne 'category' e 'description' alla tabella system_settings
e popola i valori di default per capienze e tempi.

Eseguire con:  venv\\Scripts\\python.exe migrate_settings.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from app.db.database import engine, SessionLocal
from app.models.calendar import SystemSettingDB

# ─── VALORI DI DEFAULT ────────────────────────────────────
DEFAULT_SETTINGS = [
    # Capienze Mezzi
    {"key": "van_total_seats",       "value": "9",  "category": "Capienze Mezzi",       "description": "Posti totali per furgone (inclusi autista e guida)"},
    {"key": "van_driver_seats",      "value": "1",  "category": "Capienze Mezzi",       "description": "Posti riservati all'autista per furgone"},
    {"key": "van_guide_seats",       "value": "1",  "category": "Capienze Mezzi",       "description": "Posti riservati alla guida per furgone"},

    # Tempi Base
    {"key": "briefing_duration_min", "value": "30", "category": "Tempi Base (min)",      "description": "Durata del briefing pre-discesa"},

    # Tempi Tratto A — Bomb
    {"key": "a_prep_ti_im_min",           "value": "20", "category": "Tempi Tratto A (min)",  "description": "Preparazione TI + Imbarco IM"},
    {"key": "a_river_min",                "value": "35", "category": "Tempi Tratto A (min)",  "description": "Discesa A → Bomb (fiume)"},
    {"key": "a_transfer_sb_to_imb_min",   "value": "15", "category": "Tempi Tratto A (min)",  "description": "Transfer sbarco A → imbarco B"},
    {"key": "a_return_to_base_min",       "value": "20", "category": "Tempi Tratto A (min)",  "description": "Ritorno in base da imbarco B"},

    # Tempi Tratto B
    {"key": "b_prep_ti_im_min",           "value": "20", "category": "Tempi Tratto B (min)",  "description": "Preparazione TI + Imbarco IM tratto B"},
    {"key": "b_river_min",                "value": "35", "category": "Tempi Tratto B (min)",  "description": "Discesa tratto B (fiume)"},
    {"key": "b_return_to_base_min",       "value": "20", "category": "Tempi Tratto B (min)",  "description": "Ritorno in base da sbarco B"},

    # Tempi Tratto C
    {"key": "c_prep_ti_im_min",           "value": "25", "category": "Tempi Tratto C (min)",  "description": "Preparazione TI + Imbarco IM tratto C"},
    {"key": "c_river_min",                "value": "50", "category": "Tempi Tratto C (min)",  "description": "Discesa tratto C (fiume)"},
    {"key": "c_return_to_base_min",       "value": "25", "category": "Tempi Tratto C (min)",  "description": "Ritorno in base da sbarco C"},
]


def migrate():
    # ── STEP 1: Aggiungi colonne mancanti (ALTER TABLE) ──
    print("🔧 Controllo schema tabella system_settings...")
    inspector = inspect(engine)
    existing_cols = [col["name"] for col in inspector.get_columns("system_settings")]

    with engine.connect() as conn:
        if "category" not in existing_cols:
            conn.execute(text("ALTER TABLE system_settings ADD COLUMN category VARCHAR(50) DEFAULT 'Generale'"))
            conn.commit()
            print("   ✅ Colonna 'category' aggiunta")
        else:
            print("   ⏩ Colonna 'category' già presente")

        if "description" not in existing_cols:
            conn.execute(text("ALTER TABLE system_settings ADD COLUMN description VARCHAR(255)"))
            conn.commit()
            print("   ✅ Colonna 'description' aggiunta")
        else:
            print("   ⏩ Colonna 'description' già presente")

    # ── STEP 2: Inserisci valori di default (UPSERT) ──
    print("\n📦 Inserimento valori di default...")
    db = SessionLocal()
    try:
        inserted = 0
        updated = 0
        for s in DEFAULT_SETTINGS:
            existing = db.query(SystemSettingDB).filter(SystemSettingDB.key == s["key"]).first()
            if existing:
                # Aggiorna category/description se mancanti
                changed = False
                if not existing.category or existing.category == "Generale":
                    existing.category = s["category"]
                    changed = True
                if not existing.description:
                    existing.description = s["description"]
                    changed = True
                if changed:
                    updated += 1
                print(f"   ⏩ {s['key']} = {existing.value} (già presente)")
            else:
                db.add(SystemSettingDB(
                    key=s["key"],
                    value=s["value"],
                    category=s["category"],
                    description=s["description"],
                ))
                inserted += 1
                print(f"   ✅ {s['key']} = {s['value']}")

        db.commit()
        print(f"\n{'='*55}")
        print(f"✅ MIGRAZIONE COMPLETATA!")
        print(f"   Nuovi: {inserted} | Aggiornati: {updated} | Totali: {len(DEFAULT_SETTINGS)}")
        print(f"{'='*55}")
    except Exception as e:
        print(f"❌ Errore: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
