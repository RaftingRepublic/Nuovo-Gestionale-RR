"""
Public API — Check-in Digitale / Auto-Slotting (Magic Link).

Cantiere 3: endpoint PUBBLICI (senza Auth) per il flusso consenso.
Il cliente apre il Magic Link, compila la manleva, e il backend
consuma automaticamente il primo slot vuoto dell'ordine.

Endpoints:
  GET  /public/orders/{order_id}/info       → Info discesa (activity, data, ora)
  POST /public/orders/{order_id}/fill-slot  → Pac-Man: divora il primo slot EMPTY
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.calendar import OrderDB, DailyRideDB, ActivityDB
from app.models.registration import RegistrationDB
from app.schemas.public import PublicOrderInfo, FillSlotPayload

router = APIRouter()


# ──────────────────────────────────────────────────────────
# GET /orders/{order_id}/info — Info discesa per header form
# ──────────────────────────────────────────────────────────
@router.get("/orders/{order_id}/info", response_model=PublicOrderInfo)
def get_order_info(order_id: str, db: Session = Depends(get_db)):
    """Ritorna attività, data e ora della discesa associata all'ordine."""
    try:
        order = (
            db.query(OrderDB)
            .options(
                joinedload(OrderDB.ride).joinedload(DailyRideDB.activity),
            )
            .filter(OrderDB.id == order_id)
            .first()
        )
        if not order:
            raise HTTPException(status_code=404, detail="Ordine non trovato.")

        ride = order.ride
        activity = ride.activity if ride else None

        return PublicOrderInfo(
            activity_name=activity.name if activity else "Attività",
            date=ride.ride_date.strftime("%d/%m/%Y") if ride else "N/D",
            time=ride.ride_time.strftime("%H:%M") if ride else "N/D",
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PUBLIC API] CRASH get_order_info: {e}")
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


# ──────────────────────────────────────────────────────────
# POST /orders/{order_id}/fill-slot — Pac-Man: divora slot vuoto
# ──────────────────────────────────────────────────────────
@router.post("/orders/{order_id}/fill-slot")
def fill_slot(order_id: str, payload: FillSlotPayload, db: Session = Depends(get_db)):
    """
    Trova il primo slot EMPTY dell'ordine e lo riempie coi dati del consenso.
    Se tutti gli slot sono già compilati → 400.

    Auto-Slotting: il backend agisce da "distributore di biglietti",
    assegnando automaticamente il prossimo slot disponibile.
    """
    try:
        # Verifica ordine esiste
        order = (
            db.query(OrderDB)
            .options(joinedload(OrderDB.ride).joinedload(DailyRideDB.activity))
            .filter(OrderDB.id == order_id)
            .first()
        )
        if not order:
            raise HTTPException(status_code=404, detail="Ordine non trovato.")

        # Cerca il primo slot EMPTY (ordinato per ID per garantire FIFO)
        empty_slot = (
            db.query(RegistrationDB)
            .filter(
                RegistrationDB.order_id == order_id,
                RegistrationDB.status == "EMPTY",
            )
            .order_by(RegistrationDB.id)
            .first()
        )

        if not empty_slot:
            raise HTTPException(
                status_code=400,
                detail="Tutti i posti per questa prenotazione sono già stati compilati."
            )

        # Riempi lo slot coi dati del consenso
        empty_slot.nome = payload.first_name
        empty_slot.cognome = payload.last_name
        empty_slot.email = payload.email
        empty_slot.telefono = payload.phone
        empty_slot.is_minor = payload.is_minor
        empty_slot.status = "COMPLETED"
        empty_slot.locked = True
        empty_slot.updated_at = datetime.utcnow()

        # Se l'attività è gestita da "Anatre" → tesseramento
        activity = order.ride.activity if order.ride else None
        if activity and activity.manager and activity.manager.upper() == "ANATRE":
            empty_slot.firaft_status = "DA_TESSERARE"

        # TODO: Generare PDF inserendo i dati della discesa: activity_name, date, time

        db.commit()

        return {"status": "ok", "message": "Consenso registrato con successo!"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[PUBLIC API] CRASH fill_slot: {e}")
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")
