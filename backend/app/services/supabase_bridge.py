"""
supabase_bridge.py — Modulo Radio centralizzato per chiamate HTTPX a Supabase.

Fase 9.B (27/02/2026): Cablaggio Walkie-Talkie.
Centralizza tutte le chiamate RESTful verso Supabase, evitando codice duplicato
nei router. Ogni funzione è difensiva: nessun crash permesso se Francoforte ha
un singhiozzo. Restituisce dati vuoti in caso di errore di rete.

Pattern:
  - httpx.AsyncClient con timeout=10.0
  - Header standard PostgREST (apikey + Bearer)
  - Logging strutturato, mai crash
"""

import os
import logging
import httpx

logger = logging.getLogger("supabase_bridge")

# ── Supabase Auth da .env (mai più hardcode) ──
_raw_url = os.getenv("SUPABASE_URL", "")
_raw_key = os.getenv("SUPABASE_KEY", "")
SUPABASE_URL = _raw_url.strip().strip("\"'")
SUPABASE_KEY = _raw_key.strip().strip("\"'")

_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Accept": "application/json",
}

_TIMEOUT = 10.0


async def fetch_orders_by_ride(ride_id: str) -> list:
    """
    Recupera tutti gli ordini associati a un ride_id da Supabase.
    Include registrations e transactions annidate.
    Restituisce [] in caso di errore di rete.
    """
    url = (
        f"{SUPABASE_URL}/rest/v1/orders"
        f"?ride_id=eq.{ride_id}"
        f"&select=*,transactions(*),registrations(*)"
        f"&order=created_at.asc"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers=_HEADERS)
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.error(f"⚠️ fetch_orders_by_ride({ride_id}): HTTP {resp.status_code} - {resp.text[:200]}")
                return []
    except Exception as e:
        logger.error(f"🔥 fetch_orders_by_ride({ride_id}): NETWORK ERROR - {e}")
        return []


async def fetch_order_by_id(order_id: str) -> dict | None:
    """
    Recupera un singolo ordine per ID da Supabase.
    Include ride (con activity_id), registrations e transactions.
    Restituisce None se l'ordine non esiste o in caso di errore di rete.
    """
    url = (
        f"{SUPABASE_URL}/rest/v1/orders"
        f"?id=eq.{order_id}"
        f"&select=*,transactions(*),registrations(*),rides(id,date,time,activity_id)"
        f"&limit=1"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers=_HEADERS)
            if resp.status_code == 200:
                data = resp.json()
                return data[0] if data else None
            else:
                logger.error(f"⚠️ fetch_order_by_id({order_id}): HTTP {resp.status_code} - {resp.text[:200]}")
                return None
    except Exception as e:
        logger.error(f"🔥 fetch_order_by_id({order_id}): NETWORK ERROR - {e}")
        return None


async def fetch_pax_by_rides(ride_ids: list[str]) -> dict:
    """
    Recupera la somma dei pax per una lista di ride_id da Supabase.
    Restituisce {ride_id: total_pax} per ogni ride con ordini.
    Usata dal daily-schedule per popolare i mattoncini del calendario.
    """
    if not ride_ids:
        return {}

    ids_str = ",".join(ride_ids)
    url = (
        f"{SUPABASE_URL}/rest/v1/orders"
        f"?ride_id=in.({ids_str})"
        f"&select=ride_id,pax"
    )
    pax_map: dict[str, int] = {}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers=_HEADERS)
            if resp.status_code == 200:
                for row in resp.json():
                    rid = str(row.get("ride_id", ""))
                    if not rid:
                        continue
                    raw_pax = row.get("pax")
                    pax_map[rid] = pax_map.get(rid, 0) + (int(raw_pax) if raw_pax is not None else 0)
            else:
                logger.error(f"⚠️ fetch_pax_by_rides: HTTP {resp.status_code} - {resp.text[:200]}")
    except Exception as e:
        logger.error(f"🔥 fetch_pax_by_rides: NETWORK ERROR - {e}")

    return pax_map
