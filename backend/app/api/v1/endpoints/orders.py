"""
Orders API — Pricing Engine, Logica Tetris, Ponte d'Oro, Semafori e Segreteria.

Orchestrazione completa in transazione SQL atomica:
1. Validazione attività
2. Logica Tetris (trova o crea DailyRide)
3. Pricing engine incorruttibile (calcolo server-side)
4. Creazione ordine (Fantasma o Confermato)
5. Ponte d'Oro (collega registrazioni kiosk)
6. Logica FiRaft (tesseramento)
7. Ricalcolo semaforo (con exclusive raft)
"""

import math
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.calendar import ActivityDB, DailyRideDB, OrderDB
from app.models.registration import RegistrationDB
from app.schemas.orders import OrderCreate, OrderResponse

router = APIRouter()

# ─── Capacità fittizia per barca (sarà dinamica in futuro) ─
DEFAULT_CAPACITY = 16
RAFT_SIZE = 8

# Stati che "occupano posti" nel calcolo del semaforo.
COUNTING_STATUSES = {"CONFERMATO", "COMPLETATO"}


# ──────────────────────────────────────────────────────────
# FUNZIONE CENTRALIZZATA: Conteggio posti e semaforo
# ──────────────────────────────────────────────────────────
def recalculate_ride_status(ride: DailyRideDB, db: Session) -> int:
    """
    Ricalcola booked_pax e aggiorna il semaforo del ride.

    REGOLA ESCLUSIVA: se un ordine ha `is_exclusive_raft=True`,
    il conteggio posti è `ceil(total_pax / 8) * 8` (interi gommoni),
    non il numero reale di persone.

    Ritorna il booked_pax calcolato (utile per i test).
    """
    booked_pax = 0
    for o in ride.orders:
        if o.order_status not in COUNTING_STATUSES:
            continue
        if o.is_exclusive_raft:
            # Gommone privato: prenota interi gommoni da 8
            booked_pax += math.ceil(o.total_pax / RAFT_SIZE) * RAFT_SIZE
        else:
            booked_pax += o.total_pax

    # Aggiorna semaforo SOLO se non forzato manualmente
    if not ride.is_overridden:
        if booked_pax >= DEFAULT_CAPACITY:
            ride.status = "C"    # Rosso - Sold Out
        elif booked_pax >= 14:
            ride.status = "B"    # Giallo - Ultimi posti
        elif booked_pax >= 4:
            ride.status = "D"    # Blu - Confermato
        else:
            ride.status = "A"    # Verde - Da caricare

    return booked_pax


def calculate_booked_pax(ride: DailyRideDB) -> int:
    """Calcola booked_pax senza modificare il ride (per le GET)."""
    booked_pax = 0
    for o in ride.orders:
        if o.order_status not in COUNTING_STATUSES:
            continue
        if o.is_exclusive_raft:
            booked_pax += math.ceil(o.total_pax / RAFT_SIZE) * RAFT_SIZE
        else:
            booked_pax += o.total_pax
    return booked_pax


# ──────────────────────────────────────────────────────────
# PRICING ENGINE (incorruttibile — ignora il prezzo frontend)
# ──────────────────────────────────────────────────────────
def _calculate_pricing(activity: ActivityDB, total_pax: int, is_exclusive: bool):
    """
    Calcola prezzo e sconto server-side.

    Esclusiva: ceil(pax/8) * 8 * prezzo_unitario, nessuno sconto.
    Normale:   pax * prezzo con sconto progressivo:
               11-20 pax -10%, 21-40 pax -15%, >40 pax -20%.

    Returns: (price_total, discount_applied)
    """
    unit_price = activity.price

    if is_exclusive:
        rafts = math.ceil(total_pax / RAFT_SIZE)
        return rafts * RAFT_SIZE * unit_price, 0.0

    base = total_pax * unit_price
    if total_pax > 40:
        discount = 0.20
    elif total_pax >= 21:
        discount = 0.15
    elif total_pax >= 11:
        discount = 0.10
    else:
        discount = 0.0

    return base * (1 - discount), discount


# ──────────────────────────────────────────────────────────
# POST / — Crea ordine
# ──────────────────────────────────────────────────────────
@router.post("/", response_model=OrderResponse)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    """
    Crea un nuovo ordine commerciale con pricing engine server-side.

    Orchestrazione in singola transazione SQL:
    Tetris → Pricing → Ordine → Ponte d'Oro → FiRaft → Semaforo → Commit.
    """
    try:
        # ─── 1. VALIDAZIONE ATTIVITÀ ─────────────────────
        activity = db.query(ActivityDB).filter(
            ActivityDB.id == payload.activity_id
        ).first()

        if not activity:
            raise HTTPException(
                status_code=404,
                detail=f"Attività con id '{payload.activity_id}' non trovata. "
                       f"Usa GET /calendar/activities per vedere gli ID validi."
            )

        # ─── 2. LOGICA TETRIS: trova o crea il DailyRide ─
        ride = db.query(DailyRideDB).filter(
            DailyRideDB.activity_id == payload.activity_id,
            DailyRideDB.ride_date == payload.ride_date,
            DailyRideDB.ride_time == payload.ride_time,
        ).first()

        if not ride:
            ride = DailyRideDB(
                activity_id=payload.activity_id,
                ride_date=payload.ride_date,
                ride_time=payload.ride_time,
                status="A",
            )
            db.add(ride)
            db.flush()

        # ─── 3. PRICING ENGINE ───────────────────────────
        price_total, discount = _calculate_pricing(
            activity, payload.total_pax, payload.is_exclusive_raft
        )

        # ─── 4. CREAZIONE ORDINE ─────────────────────────
        effective_status = "CONFERMATO" if payload.payment_type != "BONIFICO" else "IN_ATTESA"

        new_order = OrderDB(
            ride_id=ride.id,
            total_pax=payload.total_pax,
            customer_name=payload.customer_name,
            customer_email=payload.customer_email,
            price_total=price_total,
            discount_applied=discount,
            payment_type=payload.payment_type,
            is_exclusive_raft=payload.is_exclusive_raft,
            order_status=effective_status,
        )
        db.add(new_order)
        db.flush()

        # ─── 5. PONTE D'ORO: collega registrazioni kiosk ─
        linked_count = 0
        if payload.registration_ids:
            registrations = (
                db.query(RegistrationDB)
                .filter(RegistrationDB.id.in_(payload.registration_ids))
                .all()
            )

            found_ids = {r.id for r in registrations}
            missing = set(payload.registration_ids) - found_ids
            if missing:
                raise HTTPException(
                    status_code=404,
                    detail=f"Registrazioni non trovate: {list(missing)}. "
                           f"Verifica gli ID con GET /registration/list."
                )

            for reg in registrations:
                reg.order_id = new_order.id
                if activity.manager and activity.manager.upper() == "ANATRE":
                    reg.firaft_status = "DA_TESSERARE"
                else:
                    reg.firaft_status = "NON_RICHIESTO"

            linked_count = len(registrations)

        # ─── 6. RICALCOLO SEMAFORO ───────────────────────
        db.refresh(ride, ["orders"])
        recalculate_ride_status(ride, db)

        # ─── 7. COMMIT ATOMICO ───────────────────────────
        db.commit()
        db.refresh(new_order)
        db.refresh(ride)

        return OrderResponse(
            id=new_order.id,
            ride_id=new_order.ride_id,
            total_pax=new_order.total_pax,
            order_status=new_order.order_status,
            customer_name=new_order.customer_name,
            customer_email=new_order.customer_email,
            price_total=new_order.price_total,
            is_exclusive_raft=new_order.is_exclusive_raft,
            discount_applied=new_order.discount_applied,
            ride_status=ride.status,
            linked_registrations=linked_count,
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Errore interno durante la creazione dell'ordine: {str(e)}"
        )


# ──────────────────────────────────────────────────────────
# PATCH /{order_id}/confirm — Conferma Bonifico
# ──────────────────────────────────────────────────────────
@router.patch("/{order_id}/confirm", response_model=OrderResponse)
def confirm_order(order_id: str, db: Session = Depends(get_db)):
    """
    Conferma un ordine in attesa (es. bonifico ricevuto).

    Cambia order_status → CONFERMATO, poi ricalcola il semaforo
    del ride perché i posti dell'ordine ora pesano.
    """
    try:
        order = (
            db.query(OrderDB)
            .options(joinedload(OrderDB.ride).joinedload(DailyRideDB.orders))
            .filter(OrderDB.id == order_id)
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail=f"Ordine '{order_id}' non trovato.")

        if order.order_status == "CONFERMATO":
            raise HTTPException(status_code=400, detail="Ordine già confermato.")

        if order.order_status == "CANCELLATO":
            raise HTTPException(status_code=400, detail="Impossibile confermare un ordine cancellato.")

        order.order_status = "CONFERMATO"
        ride = order.ride

        # Ricalcola il semaforo: il fantasma si è svegliato
        recalculate_ride_status(ride, db)

        db.commit()
        db.refresh(order)
        db.refresh(ride)

        return OrderResponse(
            id=order.id,
            ride_id=order.ride_id,
            total_pax=order.total_pax,
            order_status=order.order_status,
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            price_total=order.price_total,
            is_exclusive_raft=order.is_exclusive_raft,
            discount_applied=order.discount_applied,
            ride_status=ride.status,
            linked_registrations=len(order.registrations) if order.registrations else 0,
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore nella conferma: {str(e)}")
