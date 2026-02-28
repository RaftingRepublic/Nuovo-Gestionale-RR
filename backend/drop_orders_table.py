"""
drop_orders_table.py — Script di demolizione tabella orders (SQLite).

Fase 9.A: Amputazione ORM OrderDB completata.
Questo script esegue il DROP TABLE IF EXISTS orders sul database rafting.db.

Uso:
    cd backend
    python drop_orders_table.py
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rafting.db")


def drop_orders():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database non trovato: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verifica se la tabella esiste prima del drop
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
    exists = cursor.fetchone()

    if exists:
        cursor.execute("DROP TABLE IF EXISTS orders")
        conn.commit()
        print(f"💀 Tabella 'orders' ELIMINATA da {DB_PATH}")
    else:
        print(f"ℹ️  Tabella 'orders' non presente in {DB_PATH} (già eliminata?)")

    # Verifica finale
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n📋 Tabelle rimaste nel DB: {', '.join(tables)}")

    conn.close()
    print("\n✅ Script drop_orders_table.py completato.")


if __name__ == "__main__":
    drop_orders()
