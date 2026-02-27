"""
crew.py — Crew Builder Router (Fase 7.D — Swap & Replace + Diagnostica)
Gestisce la "Busta Stagna" (composizione equipaggio) via Supabase ride_allocations.
Tecnica Swap & Replace: DELETE vecchi + bulk INSERT nuovi. Zero orfani.
Nessun ORM locale — solo httpx verso Supabase PostgREST.

Saldature 27/02/2026:
- Pydantic default resource_type allineato a "crew_manifest"
- Credenziali migrate da hardcode a os.getenv()
- Sensori di pressione: log brutali su errore Supabase
"""
import os
import httpx
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# ── Supabase Auth da .env (mai più hardcode) ──
_raw_url = os.getenv("SUPABASE_URL", "")
_raw_key = os.getenv("SUPABASE_KEY", "")
_SUPABASE_URL = _raw_url.strip().strip("\"'")
_SUPABASE_KEY = _raw_key.strip().strip("\"'")


def _headers(write=False):
    """
    Header Supabase con apikey e Authorization SEMPRE inclusi.
    Il prefisso 'Bearer ' è obbligatorio per il token JWT.
    """
    key = _SUPABASE_KEY
    h = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    if write:
        h["Content-Type"] = "application/json"
        h["Prefer"] = "return=representation"
    return h


# ── Schemi Pydantic (Tetris Umano) ──
class CrewGroup(BaseModel):
    order_id: str
    customer_name: str = ""
    pax: int = 0


class CrewMetadata(BaseModel):
    guide_id: Optional[str] = None
    groups: List[CrewGroup] = []


class CrewAllocationItem(BaseModel):
    resource_id: Optional[str] = None
    resource_type: str = "crew_manifest"  # ← ALLINEATO a Supabase (era "RAFT")
    metadata: CrewMetadata = CrewMetadata()


# ── GET: Leggi Busta Stagna ──
@router.get("/allocations/{ride_id}")
def get_crew_allocations(ride_id: str):
    """
    Legge le righe ride_allocations da Supabase per il ride_id specificato.
    Restituisce { ride_id, allocations: [...] } con l'array piatto di gommoni.
    Se non ci sono righe, restituisce un array vuoto.
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f"{_SUPABASE_URL}/rest/v1/ride_allocations"
                f"?ride_id=eq.{ride_id}"
                f"&resource_type=eq.crew_manifest"
                f"&select=id,ride_id,resource_id,resource_type,metadata",
                headers=_headers(),
            )

            # ── SENSORE DI PRESSIONE (GET) ──
            if resp.status_code != 200:
                print(f"\n{'!'*60}")
                print(f"!!! ESPLOSIONE SUPABASE (GET crew) !!!")
                print(f"!!! Status: {resp.status_code}")
                print(f"!!! Body:   {resp.text}")
                print(f"{'!'*60}\n")
                return {"ride_id": ride_id, "allocations": []}

            rows = resp.json()
            if not rows:
                return {"ride_id": ride_id, "allocations": []}

            # Ricostruisci l'array di allocazioni dal formato DB
            allocations = []
            for row in rows:
                meta = row.get("metadata", {})
                if not isinstance(meta, dict):
                    meta = {}
                allocations.append({
                    "resource_id": row.get("resource_id"),
                    "resource_type": row.get("resource_type", "crew_manifest"),
                    "metadata": {
                        "guide_id": meta.get("guide_id"),
                        "groups": meta.get("groups", []),
                    }
                })

            return {"ride_id": ride_id, "allocations": allocations}

    except Exception as e:
        print(f"[Crew GET] Exception: {e}")
        return {"ride_id": ride_id, "allocations": []}


# ── PUT: Swap & Replace (con Sensori di Pressione) ──
@router.put("/allocations/{ride_id}")
def save_crew_allocations(ride_id: str, payload: List[CrewAllocationItem]):
    """
    Swap & Replace della Busta Stagna su Supabase.
    1. DELETE tutte le righe crew_manifest per ride_id
    2. Bulk INSERT delle nuove righe
    Zero orfani, zero lookup di differenza.

    SENSORI DI PRESSIONE: ogni risposta Supabase non-OK produce un log
    esplosivo nel terminale e solleva HTTPException con il body crudo.
    """
    print(f"\n{'='*60}")
    print(f"[Crew PUT] Swap & Replace per ride_id={ride_id}")
    print(f"[Crew PUT] Payload: {len(payload)} gommoni da scrivere")
    print(f"{'='*60}")

    try:
        with httpx.Client(timeout=15.0) as client:
            # ── STEP 1: Rade al suolo (DELETE per ride_id + resource_type) ──
            del_resp = client.delete(
                f"{_SUPABASE_URL}/rest/v1/ride_allocations"
                f"?ride_id=eq.{ride_id}"
                f"&resource_type=eq.crew_manifest",
                headers=_headers(),
            )

            # 204 No Content = successo DELETE, 200 se c'era Prefer: return
            if del_resp.status_code not in (200, 204):
                print(f"\n{'!'*60}")
                print(f"!!! ESPLOSIONE SUPABASE (DELETE crew) !!!")
                print(f"!!! Status: {del_resp.status_code}")
                print(f"!!! Body:   {del_resp.text}")
                print(f"{'!'*60}\n")
                raise HTTPException(
                    status_code=500,
                    detail=f"Errore DELETE Busta Stagna su Supabase: {del_resp.text}",
                )
            else:
                print(f"[Crew PUT] DELETE OK (status={del_resp.status_code})")

            # ── STEP 2: Bulk INSERT nuovi record ──
            if len(payload) > 0:
                rows_to_insert = []
                for item in payload:
                    row = {
                        "ride_id": ride_id,
                        "resource_id": item.resource_id,
                        "resource_type": "crew_manifest",
                        "metadata": item.metadata.model_dump(),
                    }
                    rows_to_insert.append(row)

                print(f"[Crew PUT] INSERT payload: {rows_to_insert}")

                ins_resp = client.post(
                    f"{_SUPABASE_URL}/rest/v1/ride_allocations",
                    json=rows_to_insert,
                    headers=_headers(write=True),
                )

                if ins_resp.status_code not in (200, 201):
                    print(f"\n{'!'*60}")
                    print(f"!!! ESPLOSIONE SUPABASE (INSERT crew) !!!")
                    print(f"!!! Status: {ins_resp.status_code}")
                    print(f"!!! Body:   {ins_resp.text}")
                    print(f"{'!'*60}\n")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Errore INSERT Busta Stagna su Supabase: {ins_resp.text}",
                    )
                else:
                    print(f"[Crew PUT] INSERT OK (status={ins_resp.status_code})")

            count = len(payload)
            print(f"✅ [Crew PUT] Swap & Replace completato per ride {ride_id}: {count} gommoni\n")
            return {
                "status": "success",
                "ride_id": ride_id,
                "count": count,
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"\n{'!'*60}")
        print(f"!!! ESPLOSIONE CRITICA (Exception) !!!")
        print(f"!!! Tipo:    {type(e).__name__}")
        print(f"!!! Errore:  {e}")
        print(f"{'!'*60}\n")
        raise HTTPException(status_code=500, detail=f"Errore critico Crew Builder: {str(e)}")
