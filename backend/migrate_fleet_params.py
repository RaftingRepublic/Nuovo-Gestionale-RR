"""
Migrazione DB: Aggiunge colonne logistiche alla tabella 'fleet'.

Nuove colonne:
  - capacity       INTEGER DEFAULT 0  (capienza passeggeri per gommoni / posti furgone)
  - has_tow_hitch  BOOLEAN DEFAULT 0  (gancio traino solo per furgoni)
  - max_rafts      INTEGER DEFAULT 0  (max gommoni trasportabili su carrello)

Esecuzione:
  cd backend
  venv\\Scripts\\python.exe migrate_fleet_params.py
"""

from sqlalchemy import inspect, text
from app.db.database import engine


def migrate():
    print("🔧 Migrazione Fleet — Parametri Logistici")
    print("=" * 50)

    inspector = inspect(engine)
    existing_cols = [col["name"] for col in inspector.get_columns("fleet")]
    print(f"   Colonne esistenti: {existing_cols}")

    migrations = [
        ("capacity", "ALTER TABLE fleet ADD COLUMN capacity INTEGER DEFAULT 0"),
        ("has_tow_hitch", "ALTER TABLE fleet ADD COLUMN has_tow_hitch BOOLEAN DEFAULT 0"),
        ("max_rafts", "ALTER TABLE fleet ADD COLUMN max_rafts INTEGER DEFAULT 0"),
    ]

    with engine.connect() as conn:
        for col_name, sql in migrations:
            if col_name not in existing_cols:
                conn.execute(text(sql))
                conn.commit()
                print(f"   ✅ Colonna '{col_name}' aggiunta")
            else:
                print(f"   ⏩ Colonna '{col_name}' già presente")

    print(f"\n{'=' * 50}")
    print("✅ MIGRAZIONE FLEET COMPLETATA!")
    print("   I valori di default (0 / False) sono stati applicati.")
    print("   Aggiorna i singoli mezzi tramite l'interfaccia UI.")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    migrate()
