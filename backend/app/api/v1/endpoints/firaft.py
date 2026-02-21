"""
FiRaft API — Gestione Tesseramento Partecipanti.

Espone l'endpoint per aggiornare in bulk lo stato di tesseramento
dei partecipanti registrati al kiosk.

In futuro, il passaggio "DA_TESSERARE" → "TESSERATO" includerà
una chiamata HTTP all'API esterna FiRaft.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.registration import RegistrationDB

router = APIRouter()


# ─── SCHEMA DI INPUT ──────────────────────────────────────

class FiRaftBulkRequest(BaseModel):
    """Lista di ID registrazioni da tesserare."""
    registration_ids: List[str]


# ─── SCHEMA DI OUTPUT ─────────────────────────────────────

class FiRaftBulkResponse(BaseModel):
    message: str
    updated_count: int
    skipped_count: int
    details: List[str] = []


# ──────────────────────────────────────────────────────────
# POST /register-bulk — Tessera Selezionati
# ──────────────────────────────────────────────────────────
@router.post("/register-bulk", response_model=FiRaftBulkResponse)
def register_bulk(payload: FiRaftBulkRequest, db: Session = Depends(get_db)):
    """
    Aggiorna lo stato FiRaft di uno o più partecipanti.

    Transizioni valide:
      - "DA_TESSERARE" → "TESSERATO"  (il tesseramento viene registrato)
      - "TESSERATO"    → skip (già tesserato, non fare nulla)
      - "NON_RICHIESTO"→ skip (l'attività non richiede tesseramento)

    Ritorna un conteggio di quanti sono stati aggiornati e quanti saltati.
    """
    if not payload.registration_ids:
        raise HTTPException(
            status_code=422,
            detail="Devi fornire almeno un registration_id."
        )

    try:
        registrations = (
            db.query(RegistrationDB)
            .filter(RegistrationDB.id.in_(payload.registration_ids))
            .all()
        )

        # Verifica che tutti gli ID esistano
        found_ids = {r.id for r in registrations}
        missing = set(payload.registration_ids) - found_ids
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Registrazioni non trovate: {list(missing)}"
            )

        updated_count = 0
        skipped_count = 0
        details: List[str] = []

        for reg in registrations:
            if reg.firaft_status == "DA_TESSERARE":
                # TODO: In futuro, qui ci sarà la chiamata HTTP verso l'API
                # esterna FiRaft per effettuare il tesseramento reale.
                # Esempio futuro:
                #   response = httpx.post("https://api.firaft.it/tessera", json={...})
                #   if response.status_code != 200:
                #       raise HTTPException(500, "Errore FiRaft esterno")
                #
                # Per ora, registriamo solo lo stato nel nostro DB interno.

                reg.firaft_status = "TESSERATO"
                updated_count += 1
                details.append(f"✅ {reg.cognome} {reg.nome}: DA_TESSERARE → TESSERATO")

            elif reg.firaft_status == "TESSERATO":
                skipped_count += 1
                details.append(f"⏭️ {reg.cognome} {reg.nome}: già TESSERATO")

            elif reg.firaft_status == "NON_RICHIESTO":
                skipped_count += 1
                details.append(f"⏭️ {reg.cognome} {reg.nome}: NON_RICHIESTO (attività senza obbligo)")

            else:
                skipped_count += 1
                details.append(f"⚠️ {reg.cognome} {reg.nome}: stato '{reg.firaft_status}' non gestito")

        db.commit()

        return FiRaftBulkResponse(
            message="Tesseramento registrato nel sistema",
            updated_count=updated_count,
            skipped_count=skipped_count,
            details=details,
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Errore interno durante il tesseramento: {str(e)}"
        )
