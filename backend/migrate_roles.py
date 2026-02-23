"""Migrazione: aggiunge colonna 'roles' alla tabella staff e migra dati da is_guide/is_driver."""
import sqlite3
import json

DB_PATH = "rafting.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 1. Verifica se la colonna esiste già
cols = [row[1] for row in c.execute("PRAGMA table_info(staff)")]
if "roles" in cols:
    print("Colonna 'roles' già presente, skip ALTER.")
else:
    c.execute("ALTER TABLE staff ADD COLUMN roles TEXT DEFAULT '[]'")
    print("Colonna 'roles' aggiunta.")

# 2. Migra dati: is_guide -> RAF4, is_driver -> NC
rows = c.execute("SELECT id, name, is_guide, is_driver FROM staff").fetchall()
for row in rows:
    sid, name, ig, dr = row
    roles = []
    if ig:
        roles.append("RAF4")
    if dr:
        roles.append("NC")
    c.execute("UPDATE staff SET roles = ? WHERE id = ?", (json.dumps(roles), sid))
    print(f"  {name}: {roles}")

conn.commit()

# 3. Verifica finale
print("\n--- Verifica ---")
for r in c.execute("SELECT id, name, roles FROM staff").fetchall():
    print(f"  {r[1]}: {r[2]}")

conn.close()
print("\nMigrazione completata!")
