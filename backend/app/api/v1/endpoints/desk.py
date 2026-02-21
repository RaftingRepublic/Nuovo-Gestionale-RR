"""
Desk API — Segreteria Operativa (POS, Multi-Pagamento, Slot Fantasma).

Cantiere 2: endpoint dedicati al bancone.
Gestisce ordini con ledger multi-transazione e genera slot vuoti per i partecipanti.

Endpoints:
  POST   /desk              → Crea ordine desk con transazioni inline e slot vuoti
  GET    /by-ride/{ride_id}  → Ordini con transazioni annidate per un turno
  POST   /{order_id}/transactions → Aggiunge transazione a ordine esistente
  PATCH  /{order_id}         → Aggiorna pax (crea/rimuove slot) e adjustments
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.calendar import ActivityDB, DailyRideDB, OrderDB, TransactionDB
from app.models.registration import RegistrationDB
from app.schemas.desk import (
    DeskOrderCreate, DeskOrderResponse, DeskOrderUpdate,
    TransactionCreate, TransactionResponse,
)
from app.api.v1.endpoints.orders import recalculate_ride_status

router = APIRouter()


# ─── HELPER: Serializzzazione Ordine Desk ────────────────
def _serialize_desk_order(order: OrderDB) -> DeskOrderResponse:
    """Serializza un OrderDB nel formato DeskOrderResponse con calcoli."""
    total_paid = sum(tx.amount for tx in order.transactions)
    remaining = order.price_total - total_paid

    return DeskOrderResponse(
        id=order.id,
        ride_id=order.ride_id,
        booker_name=order.booker_name or order.customer_name,
        booker_phone=order.booker_phone or order.customer_phone,
        booker_email=order.booker_email or order.customer_email,
        total_pax=order.total_pax,
        price_total=order.price_total,
        adjustments=order.adjustments or 0.0,
        extras=order.extras or [],
        order_status=order.order_status,
        source=order.source or "WEB",
        notes=order.notes,
        customer_name=order.customer_name,
        transactions=order.transactions,
        registrations=order.registrations,
        total_paid=round(total_paid, 2),
        remaining=round(max(remaining, 0), 2),
    )


# ──────────────────────────────────────────────────────────
# POST /desk — Crea ordine dal bancone con multi-transazione
# ──────────────────────────────────────────────────────────
@router.post("/desk", response_model=DeskOrderResponse, status_code=201)
def create_desk_order(payload: DeskOrderCreate, db: Session = Depends(get_db)):
    """
    Crea un ordine dalla segreteria con:
    1. Pricing engine incorruttibile (pax * prezzo_base + extras + adjustments)
    2. Transazioni inline (ledger multi-pagamento)
    3. Slot Fantasma: 1 Referente + (pax-1) Slot Vuoti
    4. Auto-status PAGATO se sum(transazioni) >= totale
    """
    try:
        # ─── 1. VALIDAZIONE ATTIVITÀ ─────────────────────
        activity = db.query(ActivityDB).filter(
            ActivityDB.id == payload.activity_id
        ).first()

        if not activity:
            raise HTTPException(
                status_code=404,
                detail=f"Attività con id '{payload.activity_id}' non trovata."
            )

        # ─── 2. LOGICA TETRIS: trova o crea DailyRide ────
        ride = db.query(DailyRideDB).filter(
            DailyRideDB.activity_id == payload.activity_id,
            DailyRideDB.ride_date == payload.date,
            DailyRideDB.ride_time == payload.time,
        ).first()

        if not ride:
            ride = DailyRideDB(
                activity_id=payload.activity_id,
                ride_date=payload.date,
                ride_time=payload.time,
                status="A",
            )
            db.add(ride)
            db.flush()

        # ─── 3. PRICING ENGINE ───────────────────────────
        base_price = payload.pax * activity.price
        extras_total = sum(ex.get("price", 0) for ex in payload.extras)
        total_amount = base_price + extras_total + payload.adjustments

        # ─── 4. CREAZIONE ORDINE ─────────────────────────
        new_order = OrderDB(
            ride_id=ride.id,
            total_pax=payload.pax,
            # Desk fields
            booker_name=payload.booker_name,
            booker_phone=payload.booker_phone,
            booker_email=payload.booker_email,
            # Legacy compatibility
            customer_name=payload.booker_name,
            customer_email=payload.booker_email,
            customer_phone=payload.booker_phone,
            # Contabilità
            price_total=round(total_amount, 2),
            adjustments=payload.adjustments,
            extras=payload.extras,
            source="DESK",
            notes=payload.notes,
            order_status="IN_ATTESA",  # Aggiornato sotto se saldato
        )
        db.add(new_order)
        db.flush()

        # ─── 5. TRANSAZIONI (Libro Mastro) ───────────────
        total_paid = 0.0
        for tx_data in payload.transactions:
            tx = TransactionDB(
                order_id=new_order.id,
                amount=tx_data.amount,
                method=tx_data.method,
                type=tx_data.type,
                note=tx_data.note,
            )
            db.add(tx)
            total_paid += tx_data.amount

        # Auto-status
        if total_paid >= total_amount:
            new_order.order_status = "PAGATO"
        new_order.price_paid = round(total_paid, 2)

        # ─── 6. SLOT FANTASMA (Registrazioni) ────────────
        is_anatre = activity.manager and activity.manager.upper() == "ANATRE"
        firaft_default = "DA_TESSERARE" if is_anatre else "NON_RICHIESTO"

        for i in range(payload.pax):
            # Cantiere 3: TUTTI gli slot partono EMPTY.
            # I dati del bancone (booker_name) servono solo per l'ordine,
            # NON pre-compilano le manleve. Ogni partecipante compila da zero.
            reg = RegistrationDB(
                id=f"{new_order.id}-slot-{i}",
                order_id=new_order.id,
                daily_ride_id=ride.id,
                nome="Slot Vuoto",
                cognome=f"#{i + 1}",
                email="",
                telefono="",
                is_lead=(i == 0),
                status="EMPTY",
                locked=False,
                created_at=datetime.utcnow(),
                firaft_status=firaft_default,
            )
            db.add(reg)

        # ─── 7. RICALCOLO SEMAFORO ───────────────────────
        # L'ordine desk conta come CONFERMATO per i semafori
        if new_order.order_status == "PAGATO":
            new_order.order_status = "PAGATO"
        else:
            new_order.order_status = "CONFERMATO" if total_paid > 0 else "IN_ATTESA"

        db.flush()
        db.refresh(ride, ["orders"])
        recalculate_ride_status(ride, db)

        # ─── 8. COMMIT ATOMICO ───────────────────────────
        db.commit()
        db.refresh(new_order, ["transactions", "registrations"])

        return _serialize_desk_order(new_order)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Errore nella creazione ordine desk: {str(e)}"
        )


# ──────────────────────────────────────────────────────────
# GET /by-ride/{ride_id} — Ordini con transazioni per turno
# ──────────────────────────────────────────────────────────
@router.get("/by-ride/{ride_id}", response_model=List[DeskOrderResponse])
def get_orders_by_ride(ride_id: str, db: Session = Depends(get_db)):
    """Ritorna tutti gli ordini di un turno con transazioni e registrazioni annidate."""
    orders = (
        db.query(OrderDB)
        .options(
            joinedload(OrderDB.transactions),
            joinedload(OrderDB.registrations),
        )
        .filter(OrderDB.ride_id == ride_id)
        .order_by(OrderDB.created_at)
        .all()
    )
    return [_serialize_desk_order(o) for o in orders]


# ──────────────────────────────────────────────────────────
# POST /{order_id}/transactions — Aggiunge transazione
# ──────────────────────────────────────────────────────────
@router.post("/{order_id}/transactions", response_model=TransactionResponse, status_code=201)
def add_transaction(order_id: str, payload: TransactionCreate, db: Session = Depends(get_db)):
    """
    Aggiunge una transazione a un ordine esistente.
    Aggiorna automaticamente lo status se l'ordine è saldato.
    """
    try:
        order = (
            db.query(OrderDB)
            .options(joinedload(OrderDB.transactions))
            .filter(OrderDB.id == order_id)
            .first()
        )
        if not order:
            raise HTTPException(status_code=404, detail=f"Ordine '{order_id}' non trovato.")

        tx = TransactionDB(
            order_id=order.id,
            amount=payload.amount,
            method=payload.method,
            type=payload.type,
            note=payload.note,
        )
        db.add(tx)
        db.flush()

        # Ricalcola totale pagato
        total_paid = sum(t.amount for t in order.transactions) + payload.amount
        order.price_paid = round(total_paid, 2)

        if total_paid >= order.price_total:
            order.order_status = "PAGATO"

        db.commit()
        db.refresh(tx)
        return tx

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore aggiunta transazione: {str(e)}")


# ──────────────────────────────────────────────────────────
# PATCH /{order_id} — Aggiorna ordine (drop-outs, penali)
# ──────────────────────────────────────────────────────────
@router.patch("/{order_id}", response_model=DeskOrderResponse)
def update_desk_order(order_id: str, payload: DeskOrderUpdate, db: Session = Depends(get_db)):
    """
    Aggiorna un ordine desk:
    - Se cambia pax: crea/rimuove slot vuoti per allinearsi.
    - Se cambia adjustments: ricalcola total_amount.
    - Ricalcola lo status (PAGATO se il totale pagato copre il nuovo totale).
    """
    try:
        order = (
            db.query(OrderDB)
            .options(
                joinedload(OrderDB.transactions),
                joinedload(OrderDB.registrations),
                joinedload(OrderDB.ride).joinedload(DailyRideDB.activity),
            )
            .filter(OrderDB.id == order_id)
            .first()
        )
        if not order:
            raise HTTPException(status_code=404, detail=f"Ordine '{order_id}' non trovato.")

        activity = order.ride.activity if order.ride else None
        unit_price = activity.price if activity else 0.0
        is_anatre = activity and activity.manager and activity.manager.upper() == "ANATRE"
        firaft_default = "DA_TESSERARE" if is_anatre else "NON_RICHIESTO"

        # ─── AGGIORNAMENTO PAX ───────────────────────────
        if payload.pax is not None and payload.pax != order.total_pax:
            old_pax = order.total_pax
            new_pax = payload.pax
            order.total_pax = new_pax

            if new_pax > old_pax:
                # Aggiungi slot vuoti
                for i in range(old_pax, new_pax):
                    reg = RegistrationDB(
                        id=f"{order.id}-slot-{i}",
                        order_id=order.id,
                        daily_ride_id=order.ride_id,
                        nome="Slot Vuoto",
                        cognome=f"#{i + 1}",
                        email="",
                        telefono="",
                        is_lead=False,
                        status="EMPTY",
                        locked=False,
                        created_at=datetime.utcnow(),
                        firaft_status=firaft_default,
                    )
                    db.add(reg)
            elif new_pax < old_pax:
                # Rimuovi solo gli slot EMPTY (non quelli con manleva compilata)
                empty_slots = [
                    r for r in order.registrations
                    if r.status == "EMPTY" and not r.is_lead
                ]
                # Rimuovi dal fondo
                to_remove = empty_slots[-(old_pax - new_pax):]
                for r in to_remove:
                    db.delete(r)

        # ─── AGGIORNAMENTO ADJUSTMENTS ───────────────────
        if payload.adjustments is not None:
            order.adjustments = payload.adjustments

        if payload.notes is not None:
            order.notes = payload.notes

        # ─── RICALCOLO TOTALE ────────────────────────────
        extras_total = sum(ex.get("price", 0) for ex in (order.extras or []))
        order.price_total = round(
            (order.total_pax * unit_price) + extras_total + (order.adjustments or 0.0),
            2
        )

        # ─── RICALCOLO STATUS ────────────────────────────
        total_paid = sum(tx.amount for tx in order.transactions)
        order.price_paid = round(total_paid, 2)
        if total_paid >= order.price_total:
            order.order_status = "PAGATO"
        elif total_paid > 0:
            order.order_status = "CONFERMATO"
        else:
            order.order_status = "IN_ATTESA"

        # ─── RICALCOLO SEMAFORO ──────────────────────────
        ride = order.ride
        db.flush()
        db.refresh(ride, ["orders"])
        recalculate_ride_status(ride, db)

        db.commit()
        db.refresh(order, ["transactions", "registrations"])

        return _serialize_desk_order(order)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore aggiornamento ordine: {str(e)}")
