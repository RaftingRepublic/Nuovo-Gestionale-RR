"""
wipe_supabase.py — Tabula Rasa: Svuota tabelle operative su Supabase.

Elimina TUTTI i dati operativi dal DB cloud rispettando l'ordine
delle Foreign Key per evitare errori di vincolo.

Ordine di cancellazione:
  1. ride_allocations  (FK -> rides, resources)
  2. participants      (FK -> orders)
  3. orders            (FK -> rides)
  4. rides             (FK -> activities)

USO: python tools/wipe_supabase.py
"""
import httpx
import sys

# ── Credenziali Supabase (anon key, stesse del frontend e yield_engine) ──
SUPABASE_URL = "https://tttyeluyutbpczbslgwi.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0dHllbHV5dXRicGN6YnNsZ3dpIiwi"
    "cm9sZSI6ImFub24iLCJpYXQiOjE3NzE3Nzg5NTIsImV4cCI6MjA4NzM1NDk1Mn0."
    "kdcJtU_LHkZv20MFxDQZGkn2iz4ZBuZC3dQjLxWoaTs"
)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

# Ordine rigoroso per rispettare i vincoli FK
TABLES = [
    "ride_allocations",
    "participants",
    "orders",
    "rides",
]


def wipe_table(client: httpx.Client, table: str) -> bool:
    """Svuota una tabella Supabase con DELETE WHERE id IS NOT NULL."""
    url = f"{SUPABASE_URL}/rest/v1/{table}?id=not.is.null"
    try:
        resp = client.delete(url, headers=HEADERS)
        if resp.status_code in (200, 204):
            print(f"  ✅ {table:25s} → SVUOTATA (HTTP {resp.status_code})")
            return True
        else:
            print(f"  ❌ {table:25s} → ERRORE HTTP {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"  ❌ {table:25s} → ECCEZIONE: {e}")
        return False


def main():
    print("=" * 60)
    print("  TABULA RASA — Pulizia Dati Operativi Supabase")
    print("=" * 60)
    print(f"  Target: {SUPABASE_URL}")
    print(f"  Tabelle: {', '.join(TABLES)}")
    print()

    # Conferma di sicurezza
    confirm = input("  ⚠️  Sei sicuro? Questo cancellerà TUTTI i dati operativi. [s/N]: ")
    if confirm.strip().lower() not in ('s', 'si', 'sì', 'y', 'yes'):
        print("\n  Operazione annullata.")
        sys.exit(0)

    print()
    results = []
    with httpx.Client(timeout=30.0) as client:
        for table in TABLES:
            ok = wipe_table(client, table)
            results.append((table, ok))

    print()
    print("-" * 60)
    success = all(ok for _, ok in results)
    if success:
        print("  🎉 Pulizia completata con successo! Tutte le tabelle svuotate.")
    else:
        failed = [t for t, ok in results if not ok]
        print(f"  ⚠️  Pulizia parziale. Tabelle con errore: {', '.join(failed)}")
    print("-" * 60)


if __name__ == "__main__":
    main()
