import os
import httpx
import uuid
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.calendar import ActivityDB, DailyRideDB
from app.schemas.desk import (
    DeskOrderCreate, DeskOrderResponse, DeskOrderUpdate,
    TransactionCreate, TransactionResponse
)

router = APIRouter()

# ── Supabase Auth da .env (mai più hardcode) ──
_raw_url = os.getenv("SUPABASE_URL", "")
_raw_key = os.getenv("SUPABASE_KEY", "")
_SUPABASE_URL = _raw_url.strip().strip("\"'")
_SUPABASE_KEY = _raw_key.strip().strip("\"'")

def _get_headers(is_write=False):
    headers = {
        "apikey": _SUPABASE_KEY,
        "Authorization": f"Bearer {_SUPABASE_KEY}",
        "Accept": "application/json",
    }
    if is_write:
        headers["Content-Type"] = "application/json"
        headers["Prefer"] = "return=representation"
    return headers

def _serialize_desk_order(order: dict) -> DeskOrderResponse:
    txs = order.get("transactions", []) or []
    regs = order.get("registrations", []) or []
    total_paid = sum(float(tx.get("amount", 0.0)) for tx in txs)
    price_total = float(order.get("price_total", 0.0))
    remaining = max(price_total - total_paid, 0.0)

    return DeskOrderResponse(
        id=str(order.get("id")),
        ride_id=str(order.get("ride_id")),
        booker_name=order.get("booker_name") or order.get("customer_name"),
        booker_phone=order.get("booker_phone") or order.get("customer_phone"),
        booker_email=order.get("booker_email") or order.get("customer_email"),
        total_pax=int(order.get("pax", 1)),
        price_total=price_total,
        adjustments=float(order.get("adjustments", 0.0)),
        extras=order.get("extras", []),
        order_status=order.get("order_status", "IN_ATTESA"),
        source=order.get("source", "DESK"),
        notes=order.get("notes"),
        customer_name=order.get("customer_name"),
        transactions=txs,
        registrations=regs,
        total_paid=round(total_paid, 2),
        remaining=round(remaining, 2)
    )

@router.post("/desk", response_model=DeskOrderResponse, status_code=201)
def create_desk_order(payload: DeskOrderCreate, db: Session = Depends(get_db)):
    try:
        # 1. Fetch Activity (Prezzo e Regole) da LOCAL SQLite (Architettura Ibrida)
        activity = db.query(ActivityDB).filter(ActivityDB.id == payload.activity_id).first()
        if not activity:
            raise HTTPException(status_code=404, detail=f"Attività '{payload.activity_id}' non trovata nel Catalogo locale (SQLite).")
        
        unit_price = float(activity.price) if activity.price else 0.0
        manager = activity.manager or ""
        is_anatre = manager.upper() == "ANATRE"
        firaft_default = "DA_TESSERARE" if is_anatre else "NON_RICHIESTO"

        # 2. Dual-Write: Trova o Crea Ride in SQLite LOCALE
        local_ride = db.query(DailyRideDB).filter(
            DailyRideDB.activity_id == payload.activity_id,
            DailyRideDB.ride_date == payload.date,
            DailyRideDB.ride_time == payload.time,
        ).first()

        if not local_ride:
            local_ride = DailyRideDB(
                id=str(uuid.uuid4()),
                activity_id=payload.activity_id,
                ride_date=payload.date,
                ride_time=payload.time,
                status="A",
            )
            db.add(local_ride)
            db.commit()
            db.refresh(local_ride)

        ride_id_str = str(local_ride.id)

        with httpx.Client(timeout=10.0) as client:
            read_headers = _get_headers(is_write=False)
            write_headers = _get_headers(is_write=True)

            # 3. Sincronizzazione Ride su Supabase CON LO STESSO UUID
            r_resp = client.get(f"{_SUPABASE_URL}/rest/v1/rides?id=eq.{ride_id_str}&select=id", headers=read_headers)
            if r_resp.status_code == 200 and not r_resp.json():
                sb_ride = {
                    "id": ride_id_str,
                    "activity_id": payload.activity_id,
                    "date": payload.date.isoformat(),
                    "time": payload.time.strftime("%H:%M:%S"),
                    "status": "A"
                }
                c_ride = client.post(f"{_SUPABASE_URL}/rest/v1/rides", json=sb_ride, headers=write_headers)
                if c_ride.status_code not in (200, 201):
                    raise HTTPException(status_code=500, detail="Errore sync Turno (Ride) su Supabase.")

            # 4. CRM Silente su Supabase
            customer_id = None
            if payload.booker_email or payload.booker_phone:
                conds = []
                if payload.booker_email: conds.append(f"email.eq.{payload.booker_email}")
                if payload.booker_phone: conds.append(f"phone.eq.{payload.booker_phone}")
                or_cond = ",".join(conds)
                cust_resp = client.get(f"{_SUPABASE_URL}/rest/v1/customers?or=({or_cond})&select=*", headers=read_headers)
                if cust_resp.status_code == 200 and cust_resp.json():
                    customer_id = cust_resp.json()[0]["id"]

            if not customer_id and (payload.booker_name or payload.booker_email or payload.booker_phone):
                new_cust = {
                    "id": str(uuid.uuid4()),
                    "full_name": payload.booker_name,
                    "email": payload.booker_email,
                    "phone": payload.booker_phone
                }
                c_cust_resp = client.post(f"{_SUPABASE_URL}/rest/v1/customers", json=new_cust, headers=write_headers)
                if c_cust_resp.status_code in (200, 201):
                    customer_id = c_cust_resp.json()[0]["id"]

            # 5. Pricing Incorruttibile calcolato da listino SQLite locale
            base_price = payload.pax * unit_price
            extras_total = sum(float(ex.get("price", 0)) for ex in payload.extras)
            total_amount = base_price + extras_total + payload.adjustments
            total_paid = sum(tx.amount for tx in payload.transactions)
            
            if total_paid >= total_amount:
                order_status = "PAGATO"
            elif total_paid > 0:
                order_status = "CONFERMATO"
            else:
                order_status = "IN_ATTESA"

            # 6. Scrittura Ordine puro cloud su Supabase
            order_id = str(uuid.uuid4())
            new_order = {
                "id": order_id,
                "ride_id": ride_id_str,
                "pax": payload.pax,
                "booker_name": payload.booker_name,
                "booker_phone": payload.booker_phone,
                "booker_email": payload.booker_email,
                "customer_name": payload.booker_name,
                "customer_phone": payload.booker_phone,
                "customer_email": payload.booker_email,
                "price_total": round(total_amount, 2),
                "price_paid": round(total_paid, 2),
                "adjustments": payload.adjustments,
                "extras": payload.extras,
                "source": "DESK",
                "notes": payload.notes,
                "order_status": order_status,
                "customer_id": customer_id
            }
            c_ord_resp = client.post(f"{_SUPABASE_URL}/rest/v1/orders", json=new_order, headers=write_headers)
            if c_ord_resp.status_code not in (200, 201):
                raise HTTPException(status_code=500, detail=f"Errore scrittura Ordine su Supabase: {c_ord_resp.text}")

            # 7. Transazioni
            if payload.transactions:
                txs_data = []
                for tx in payload.transactions:
                    txs_data.append({
                        "id": str(uuid.uuid4()),
                        "order_id": order_id,
                        "amount": tx.amount,
                        "method": tx.method,
                        "type": tx.type,
                        "note": tx.note
                    })
                client.post(f"{_SUPABASE_URL}/rest/v1/transactions", json=txs_data, headers=write_headers)

            # 8. Registrazioni (Slot Fantasma)
            regs_data = []
            for i in range(payload.pax):
                regs_data.append({
                    "id": f"{order_id}-slot-{i}",
                    "order_id": order_id,
                    "daily_ride_id": ride_id_str,
                    "nome": "Slot Vuoto",
                    "cognome": f"#{i + 1}",
                    "email": "",
                    "telefono": "",
                    "is_lead": (i == 0),
                    "status": "EMPTY",
                    "locked": False,
                    "firaft_status": firaft_default
                })
            if regs_data:
                client.post(f"{_SUPABASE_URL}/rest/v1/registrations", json=regs_data, headers=write_headers)

            # 9. Ritorno per la UI
            final_resp = client.get(f"{_SUPABASE_URL}/rest/v1/orders?id=eq.{order_id}&select=*,transactions(*),registrations(*)&limit=1", headers=read_headers)
            if final_resp.status_code == 200 and final_resp.json():
                return _serialize_desk_order(final_resp.json()[0])
            else:
                raise HTTPException(status_code=500, detail="Errore recupero ordine creato da Supabase.")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore critico in Desk POST: {str(e)}")

@router.get("/by-ride/{ride_id}", response_model=List[DeskOrderResponse])
def get_orders_by_ride(ride_id: str):
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(f"{_SUPABASE_URL}/rest/v1/orders?ride_id=eq.{ride_id}&select=*,transactions(*),registrations(*)&order=created_at.asc", headers=_get_headers())
        if resp.status_code != 200:
            return []
        return [_serialize_desk_order(o) for o in resp.json()]

@router.post("/{order_id}/transactions", response_model=TransactionResponse, status_code=201)
def add_transaction(order_id: str, payload: TransactionCreate):
    with httpx.Client(timeout=10.0) as client:
        read_headers = _get_headers()
        write_headers = _get_headers(is_write=True)

        o_resp = client.get(f"{_SUPABASE_URL}/rest/v1/orders?id=eq.{order_id}&select=*,transactions(*)", headers=read_headers)
        if o_resp.status_code != 200 or not o_resp.json():
            raise HTTPException(status_code=404, detail="Ordine non trovato in Supabase.")
        order = o_resp.json()[0]

        new_tx = {
            "id": str(uuid.uuid4()),
            "order_id": order_id,
            "amount": payload.amount,
            "method": payload.method,
            "type": payload.type,
            "note": payload.note
        }
        tx_resp = client.post(f"{_SUPABASE_URL}/rest/v1/transactions", json=new_tx, headers=write_headers)
        if tx_resp.status_code not in (200, 201):
            raise HTTPException(status_code=500, detail="Errore aggiunta transazione in Supabase.")
        created_tx = tx_resp.json()[0] if isinstance(tx_resp.json(), list) else tx_resp.json()

        total_paid = sum(float(t.get("amount", 0.0)) for t in order.get("transactions", [])) + payload.amount
        price_total = float(order.get("price_total", 0.0))
        new_status = "PAGATO" if total_paid >= price_total else "CONFERMATO"

        patch_data = {"price_paid": round(total_paid, 2), "order_status": new_status}
        client.patch(f"{_SUPABASE_URL}/rest/v1/orders?id=eq.{order_id}", json=patch_data, headers=write_headers)

        return TransactionResponse(**created_tx)

@router.patch("/{order_id}", response_model=DeskOrderResponse)
def update_desk_order(order_id: str, payload: DeskOrderUpdate, db: Session = Depends(get_db)):
    try:
        with httpx.Client(timeout=10.0) as client:
            read_headers = _get_headers()
            write_headers = _get_headers(is_write=True)

            url = f"{_SUPABASE_URL}/rest/v1/orders?id=eq.{order_id}&select=*,transactions(*),registrations(*),rides!inner(activity_id)"
            o_resp = client.get(url, headers=read_headers)
            if o_resp.status_code != 200 or not o_resp.json():
                raise HTTPException(status_code=404, detail="Ordine non trovato in Supabase.")
            
            order = o_resp.json()[0]
            regs = order.get("registrations", [])
            
            # Gestione sicura per via di PostgREST inner join (potrebbe tornare lista o dict)
            rides_data = order.get("rides")
            if isinstance(rides_data, dict):
                activity_id = rides_data.get("activity_id")
            elif isinstance(rides_data, list) and len(rides_data) > 0:
                activity_id = rides_data[0].get("activity_id")
            else:
                activity_id = None

            unit_price = 0.0
            firaft_default = "NON_RICHIESTO"
            
            # Estrazione IBRIDA: Listino Prezzi da SQLite locale
            if activity_id:
                activity = db.query(ActivityDB).filter(ActivityDB.id == activity_id).first()
                if activity:
                    unit_price = float(activity.price) if activity.price else 0.0
                    manager = activity.manager or ""
                    if manager.upper() == "ANATRE":
                        firaft_default = "DA_TESSERARE"

            old_pax = int(order.get("pax", 0))
            new_pax = payload.pax if payload.pax is not None else old_pax

            if new_pax > old_pax:
                new_regs = []
                for i in range(old_pax, new_pax):
                    rand_suffix = str(uuid.uuid4())[:6]
                    new_regs.append({
                        "id": f"{order_id}-slot-{i}-{rand_suffix}",
                        "order_id": order_id,
                        "daily_ride_id": order.get("ride_id"),
                        "nome": "Slot Vuoto",
                        "cognome": f"#{i + 1}",
                        "email": "",
                        "telefono": "",
                        "is_lead": False,
                        "status": "EMPTY",
                        "locked": False,
                        "firaft_status": firaft_default
                    })
                client.post(f"{_SUPABASE_URL}/rest/v1/registrations", json=new_regs, headers=write_headers)
                    
            elif new_pax < old_pax:
                empty_slots = [r for r in regs if r.get("status") == "EMPTY" and not r.get("is_lead")]
                to_remove = empty_slots[-(old_pax - new_pax):]
                if to_remove:
                    ids_to_del = ",".join(f'"{r["id"]}"' for r in to_remove)
                    client.delete(f"{_SUPABASE_URL}/rest/v1/registrations?id=in.({ids_to_del})", headers=read_headers)

            adjustments = payload.adjustments if payload.adjustments is not None else float(order.get("adjustments", 0.0))
            notes = payload.notes if payload.notes is not None else order.get("notes")
            
            extras_total = sum(float(ex.get("price", 0.0)) for ex in order.get("extras", []))
            price_total = round((new_pax * unit_price) + extras_total + adjustments, 2)
            total_paid = sum(float(t.get("amount", 0.0)) for t in order.get("transactions", []))

            if total_paid >= price_total:
                new_status = "PAGATO"
            elif total_paid > 0:
                new_status = "CONFERMATO"
            else:
                new_status = "IN_ATTESA"

            patch_data = {
                "pax": new_pax,
                "adjustments": adjustments,
                "notes": notes,
                "price_total": price_total,
                "price_paid": total_paid,
                "order_status": new_status
            }
            client.patch(f"{_SUPABASE_URL}/rest/v1/orders?id=eq.{order_id}", json=patch_data, headers=write_headers)
            
            final_resp = client.get(f"{_SUPABASE_URL}/rest/v1/orders?id=eq.{order_id}&select=*,transactions(*),registrations(*)&limit=1", headers=read_headers)
            if final_resp.status_code == 200 and final_resp.json():
                return _serialize_desk_order(final_resp.json()[0])
            else:
                raise HTTPException(status_code=500, detail="Errore recupero ordine aggiornato da Supabase.")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore in update_desk_order: {str(e)}")
