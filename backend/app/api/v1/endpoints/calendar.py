"""
Calendar API — Endpoint BFF per il Calendario Operativo.

Espone i dati SQL (Attività, Discese) al Frontend con query ottimizzate.
Sostituisce le vecchie logiche basate su file JSON.
"""

import httpx
from collections import defaultdict
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.calendar import (
    ActivityDB, DailyRideDB, OrderDB, ActivitySubPeriodDB,
    StaffDB, FleetDB,
)
from app.schemas.calendar import (
    ActivityResponse, ActivityCreate, DailyRideResponse,
    ActivitySeasonUpdate, DailyScheduleResponse, RideAllocationUpdate,
    AssignedResource,
)
from app.schemas.orders import DailyRideDetailResponse, RideOverrideRequest
from app.api.v1.endpoints.orders import calculate_booked_pax, recalculate_ride_status
from app.services.availability_engine import AvailabilityEngine

router = APIRouter()


# ──────────────────────────────────────────────────────────
# GET /activities — Lista attività attive
# ──────────────────────────────────────────────────────────
@router.get("/activities", response_model=List[ActivityResponse])
def list_activities(db: Session = Depends(get_db)):
    """
    Ritorna tutte le attività con `is_active == True`.
    Usato dal Frontend per popolare dropdown, filtri e legenda colori.
    """
    return (
        db.query(ActivityDB)
        .options(joinedload(ActivityDB.sub_periods))
        .filter(ActivityDB.is_active == True)  # noqa: E712
        .order_by(ActivityDB.name)
        .all()
    )


# ──────────────────────────────────────────────────────────
# POST /activities — Crea nuova attività
# ──────────────────────────────────────────────────────────
@router.post("/activities", response_model=ActivityResponse, status_code=201)
def create_activity(payload: ActivityCreate, db: Session = Depends(get_db)):
    """Crea una nuova attività nel catalogo."""
    activity = ActivityDB(
        code=payload.code,
        name=payload.name,
        color_hex=payload.color_hex,
        price=payload.price,
        duration_hours=payload.duration_hours,
        river_segments=payload.river_segments,
        manager=payload.manager,
        season_start=payload.season_start,
        season_end=payload.season_end,
        default_times=payload.default_times,
        allow_intersections=payload.allow_intersections,
        activity_class=payload.activity_class,
        yellow_threshold=payload.yellow_threshold,
        overbooking_limit=payload.overbooking_limit,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


# ──────────────────────────────────────────────────────────
# DELETE /activities/{id} — Elimina attività
# ──────────────────────────────────────────────────────────
@router.delete("/activities/{activity_id}", status_code=204)
def delete_activity(activity_id: str, db: Session = Depends(get_db)):
    """Elimina un'attività e tutti i suoi sottoperiodi (cascade)."""
    activity = db.query(ActivityDB).filter(ActivityDB.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Attività non trovata")
    db.delete(activity)
    db.commit()
    return None


from datetime import time as dt_time


# ──────────────────────────────────────────────────────────
# HELPER: Materializza turni teorici per una data
# ──────────────────────────────────────────────────────────
def _ensure_theoretical_rides(db: Session, target_date: date) -> None:
    """
    Per ogni attività attiva in `target_date`, controlla se esistono
    le DailyRideDB corrispondenti. Se mancano, le crea al volo.

    Logica:
    1. Carica tutte le ActivityDB attive con i loro sub_periods.
    2. Per ogni attività, verifica se target_date cade nella stagione
       (season_start..season_end). Se no, skip.
    3. Controlla se un SubPeriod marca la data come `is_closed`. Se sì, skip.
    4. Determina gli orari effettivi: usa `override_times` dal SubPeriod
       attivo, oppure `default_times` dell'attività.
    5. Per ogni orario, cerca se esiste già un DailyRideDB(activity_id, date, time).
       Se non esiste, crealo.
    """
    activities = (
        db.query(ActivityDB)
        .options(joinedload(ActivityDB.sub_periods))
        .filter(ActivityDB.is_active == True)  # noqa: E712
        .all()
    )

    date_str = target_date.strftime("%Y-%m-%d")
    created = 0

    for act in activities:
        # ─── Check stagione ───
        if act.season_start and target_date < act.season_start:
            continue
        if act.season_end and target_date > act.season_end:
            continue

        # ─── Check SubPeriod (chiusure + override orari) ───
        is_closed = False
        effective_times = list(act.default_times or [])

        for sp in (act.sub_periods or []):
            if date_str in (sp.dates or []):
                if sp.is_closed:
                    is_closed = True
                    break
                if sp.override_times:
                    effective_times = list(sp.override_times)

        if is_closed or not effective_times:
            continue

        # ─── Crea ride mancanti ───
        for time_str in effective_times:
            try:
                parts = time_str.strip().split(":")
                ride_time = dt_time(int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                continue

            exists = (
                db.query(DailyRideDB.id)
                .filter(
                    DailyRideDB.activity_id == act.id,
                    DailyRideDB.ride_date == target_date,
                    DailyRideDB.ride_time == ride_time,
                )
                .first()
            )

            if not exists:
                new_ride = DailyRideDB(
                    activity_id=act.id,
                    ride_date=target_date,
                    ride_time=ride_time,
                    status="A",  # Verde di default
                )
                db.add(new_ride)
                created += 1

    if created > 0:
        db.commit()


# ──────────────────────────────────────────────────────────
# GET /daily-rides — Discese con Engine calcolato
_SUPABASE_URL = "https://tttyeluyutbpczbslgwi.supabase.co"
_SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0dHllbHV5dXRicGN6YnNsZ3dpIiwi"
    "cm9sZSI6ImFub24iLCJpYXQiOjE3NzE3Nzg5NTIsImV4cCI6MjA4NzM1NDk1Mn0."
    "kdcJtU_LHkZv20MFxDQZGkn2iz4ZBuZC3dQjLxWoaTs"
)

def _fetch_supabase_pax(dates: set) -> dict:
    """Sonda HTTP sincrona per estrarre i pax reali da Supabase (Split-Brain Fix)."""
    if not dates:
        return {}
    
    headers = {
        "apikey": _SUPABASE_KEY,
        "Authorization": f"Bearer {_SUPABASE_KEY}",
        "Accept": "application/json",
    }
    
    dates_str = ",".join([d.isoformat() for d in dates])
    # Inner Join PostgREST: filtra orders attraverso la relazione rides.date
    url = f"{_SUPABASE_URL}/rest/v1/orders?select=ride_id,pax,rides!inner(date)&rides.date=in.({dates_str})"
    
    pax_map = defaultdict(int)
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                for row in resp.json():
                    rid = str(row.get("ride_id", ""))
                    if not rid:
                        continue
                    raw_pax = row.get("pax")
                    pax_map[rid] += int(raw_pax) if raw_pax is not None else 0
            else:
                print(f"⚠️ Errore Sonda Supabase: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"🔥 FALLIMENTO CRITICO SONDA: {e}")
        
    return dict(pax_map)

# ──────────────────────────────────────────────────────────
@router.get("/daily-rides", response_model=List[DailyRideResponse])
def list_daily_rides(
    ride_date: Optional[date] = Query(
        None,
        alias="date",
        description="Filtra per data singola (YYYY-MM-DD)."
    ),
    start_date: Optional[date] = Query(
        None,
        description="Filtra da questa data (inclusa). Usato dal calendario mensile."
    ),
    end_date: Optional[date] = Query(
        None,
        description="Filtra fino a questa data (inclusa). Usato dal calendario mensile."
    ),
    db: Session = Depends(get_db),
):
    """
    Ritorna le discese con disponibilità calcolate dall'AvailabilityEngine.

    Per date singole: materializza automaticamente i turni teorici
    previsti dalla stagione (solves 'invisible rides' paradox).
    Per range mensili: materializza turni per ogni giorno del range.
    """
    # ─── Auto-generazione turni teorici ───
    if ride_date is not None:
        _ensure_theoretical_rides(db, ride_date)
    elif start_date is not None and end_date is not None:
        # Range mensile: genera per ogni giorno
        from datetime import timedelta
        current = start_date
        while current <= end_date:
            _ensure_theoretical_rides(db, current)
            current += timedelta(days=1)

    # ─── Query ride (ora include anche quelle appena create) ───
    query = (
        db.query(DailyRideDB)
        .options(
            joinedload(DailyRideDB.activity),
            joinedload(DailyRideDB.orders),
            joinedload(DailyRideDB.assigned_staff),
            joinedload(DailyRideDB.assigned_fleet),
        )
        .order_by(DailyRideDB.ride_date, DailyRideDB.ride_time)
    )

    if ride_date is not None:
        query = query.filter(DailyRideDB.ride_date == ride_date)
    elif start_date is not None and end_date is not None:
        query = query.filter(
            DailyRideDB.ride_date >= start_date,
            DailyRideDB.ride_date <= end_date,
        )

    rides = query.all()

    # ─── Calcola availability ───
    dates_seen = set()
    for r in rides:
        dates_seen.add(r.ride_date)

    # 🔴 INIEZIONE DELLA VERITÀ: Sonda Supabase
    real_pax_map = _fetch_supabase_pax(dates_seen)

    availability_map = {}
    for d in dates_seen:
        # Passiamo la mappa all'Engine come external_pax_map
        day_avail = AvailabilityEngine.calculate_availability(db, d, external_pax_map=real_pax_map)
        availability_map.update(day_avail)

    result: List[DailyRideResponse] = []
    for ride in rides:
        booked_pax = calculate_booked_pax(ride)
        avail = availability_map.get(ride.id, {})

        result.append(
            DailyRideResponse(
                id=ride.id,
                activity_id=ride.activity_id,
                ride_date=ride.ride_date,
                ride_time=ride.ride_time,
                status=ride.status,
                is_overridden=ride.is_overridden,
                notes=ride.notes,
                activity_name=ride.activity.name if ride.activity else "Sconosciuta",
                color_hex=ride.activity.color_hex if ride.activity else "#9E9E9E",
                booked_pax=booked_pax,
                total_capacity=avail.get("total_capacity", 0),
                arr_bonus_seats=avail.get("arr_bonus_seats", 0),
                yield_warning=avail.get("debug_yield_warning", False),
                remaining_seats=avail.get("remaining_seats", 0),
                engine_status=avail.get("status", "VERDE"),
                assigned_staff=[AssignedResource(id=s.id, name=s.name) for s in (ride.assigned_staff or [])],
                assigned_fleet=[AssignedResource(id=f.id, name=f.name, category=getattr(f, 'category', None)) for f in (ride.assigned_fleet or [])],
            )
        )

    return result


# ──────────────────────────────────────────────────────────
# GET /daily-rides/export-firaft — Export CSV per FIRAFT
# NOTA: Deve stare PRIMA di /daily-rides/{ride_id} per evitare routing collision
# ──────────────────────────────────────────────────────────
@router.get("/daily-rides/export-firaft")
def export_firaft_csv(
    date: str = Query(..., description="Data in formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    Cantiere 6: Genera un file CSV con tutte le registrazioni COMPLETED
    del giorno, pronte per il tesseramento FIRAFT.
    """
    import csv
    import io
    from datetime import datetime as dt_datetime
    from fastapi.responses import StreamingResponse
    from app.models.registration import RegistrationDB

    try:
        target_date = dt_datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato data non valido. Usa YYYY-MM-DD.")

    # Query: Registrazioni → Ordine → Turno → Attività, filtrando per data e stato COMPLETED
    results = (
        db.query(
            RegistrationDB,
            DailyRideDB.ride_time,
            ActivityDB.name.label("activity_name"),
        )
        .join(OrderDB, RegistrationDB.order_id == OrderDB.id)
        .join(DailyRideDB, OrderDB.ride_id == DailyRideDB.id)
        .join(ActivityDB, DailyRideDB.activity_id == ActivityDB.id)
        .filter(DailyRideDB.ride_date == target_date)
        .filter(RegistrationDB.status == "COMPLETED")
        .order_by(DailyRideDB.ride_time, RegistrationDB.cognome)
        .all()
    )

    # Genera CSV in memoria
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["NOME", "COGNOME", "EMAIL", "TELEFONO", "MINORENNE", "ATTIVITA", "ORARIO_TURNO"])

    for reg, ride_time, activity_name in results:
        writer.writerow([
            reg.nome or "",
            reg.cognome or "",
            reg.email or "",
            reg.telefono or "",
            "SI" if reg.is_minor else "NO",
            activity_name or "",
            str(ride_time)[:5] if ride_time else "",
        ])

    output.seek(0)

    safe_date = date.replace("-", "")
    headers = {
        "Content-Disposition": f'attachment; filename="FIRAFT_Export_{safe_date}.csv"'
    }

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers=headers,
    )


# ──────────────────────────────────────────────────────────
# GET /daily-rides/{ride_id} — Dettaglio "Matrioska"
# ──────────────────────────────────────────────────────────
@router.get("/daily-rides/{ride_id}", response_model=DailyRideDetailResponse)
def get_daily_ride_detail(ride_id: str, db: Session = Depends(get_db)):
    """
    Ritorna il dettaglio completo di una singola discesa (Ride).
    Include: Ride → [Ordini → [Registrazioni]] + campi arricchiti.
    """
    ride = (
        db.query(DailyRideDB)
        .options(
            joinedload(DailyRideDB.activity),
            joinedload(DailyRideDB.orders).joinedload(OrderDB.registrations),
        )
        .filter(DailyRideDB.id == ride_id)
        .first()
    )

    if not ride:
        raise HTTPException(
            status_code=404,
            detail=f"Discesa con id '{ride_id}' non trovata."
        )

    booked_pax = calculate_booked_pax(ride)
    
    # Calcolo availability specifica per questo turno
    avail_map = AvailabilityEngine.calculate_availability(db, ride.ride_date)
    avail = avail_map.get(ride.id, {})

    return DailyRideDetailResponse(
        id=ride.id,
        activity_id=ride.activity_id,
        ride_date=ride.ride_date,
        ride_time=ride.ride_time,
        status=ride.status,
        is_overridden=ride.is_overridden,
        notes=ride.notes,
        activity_name=ride.activity.name if ride.activity else "Sconosciuta",
        color_hex=ride.activity.color_hex if ride.activity else "#9E9E9E",
        booked_pax=booked_pax,
        total_capacity=avail.get("total_capacity", 0),
        arr_bonus_seats=avail.get("arr_bonus_seats", 0),
        yield_warning=avail.get("debug_yield_warning", False),
        remaining_seats=avail.get("remaining_seats", 0),
        engine_status=avail.get("status", "VERDE"),
        orders=ride.orders,
    )


# ──────────────────────────────────────────────────────────
# PATCH /daily-rides/{ride_id}/override — Forzatura Semaforo
# ──────────────────────────────────────────────────────────
@router.patch("/daily-rides/{ride_id}/override", response_model=DailyRideResponse)
def override_ride_status(
    ride_id: str,
    payload: RideOverrideRequest,
    db: Session = Depends(get_db),
):
    """
    Forza o rilascia il semaforo di una discesa.

    Se clear_override=True: rilascia la forzatura e ricalcola automaticamente.
    Altrimenti: forza lo status indicato e blocca il ricalcolo automatico.
    """
    try:
        ride = (
            db.query(DailyRideDB)
            .options(
                joinedload(DailyRideDB.activity),
                joinedload(DailyRideDB.orders),
            )
            .filter(DailyRideDB.id == ride_id)
            .first()
        )

        if not ride:
            raise HTTPException(status_code=404, detail=f"Discesa '{ride_id}' non trovata.")

        if payload.clear_override:
            ride.is_overridden = False
            recalculate_ride_status(ride, db)
        else:
            if payload.forced_status not in ("A", "B", "C", "D"):
                raise HTTPException(
                    status_code=422,
                    detail=f"Status '{payload.forced_status}' non valido. Usa A, B, C o D."
                )
            ride.status = payload.forced_status
            ride.is_overridden = True

        db.commit()
        db.refresh(ride)

        booked_pax = calculate_booked_pax(ride)

        return DailyRideResponse(
            id=ride.id,
            activity_id=ride.activity_id,
            ride_date=ride.ride_date,
            ride_time=ride.ride_time,
            status=ride.status,
            is_overridden=ride.is_overridden,
            notes=ride.notes,
            activity_name=ride.activity.name if ride.activity else "Sconosciuta",
            color_hex=ride.activity.color_hex if ride.activity else "#9E9E9E",
            booked_pax=booked_pax,
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore override: {str(e)}")


# ──────────────────────────────────────────────────────────
# PATCH /activities/{id}/season — Configura Stagione e Sottoperiodi
# ──────────────────────────────────────────────────────────
@router.patch("/activities/{activity_id}/season", response_model=ActivityResponse)
def update_activity_season(
    activity_id: str,
    payload: ActivitySeasonUpdate,
    db: Session = Depends(get_db),
):
    """
    Aggiorna la configurazione stagionale di un'attività:
    - manager (Grape/Anatre)
    - price base
    - season_start / season_end
    - default_times
    - sub_periods (bulk: elimina i vecchi, inserisce i nuovi)
    """
    activity = (
        db.query(ActivityDB)
        .options(joinedload(ActivityDB.sub_periods))
        .filter(ActivityDB.id == activity_id)
        .first()
    )
    if not activity:
        raise HTTPException(status_code=404, detail=f"Attività '{activity_id}' non trovata.")

    # Aggiorna campi scalari (solo se forniti)
    if payload.code is not None:
        activity.code = payload.code
    if payload.color_hex is not None:
        activity.color_hex = payload.color_hex
    if payload.duration_hours is not None:
        activity.duration_hours = payload.duration_hours
    if payload.river_segments is not None:
        activity.river_segments = payload.river_segments
    if payload.manager is not None:
        activity.manager = payload.manager
    if payload.price is not None:
        activity.price = payload.price
    if payload.season_start is not None:
        activity.season_start = payload.season_start
    if payload.season_end is not None:
        activity.season_end = payload.season_end
    if payload.default_times is not None:
        activity.default_times = payload.default_times
    if payload.allow_intersections is not None:
        activity.allow_intersections = payload.allow_intersections
    if payload.activity_class is not None:
        activity.activity_class = payload.activity_class
    if payload.yellow_threshold is not None:
        activity.yellow_threshold = payload.yellow_threshold
    if payload.overbooking_limit is not None:
        activity.overbooking_limit = payload.overbooking_limit
    if payload.workflow_schema is not None:
        activity.workflow_schema = payload.workflow_schema

    # Gestione bulk sub_periods: se il campo è presente, replace all
    if payload.sub_periods is not None:
        # Elimina i vecchi sottoperiodi
        db.query(ActivitySubPeriodDB).filter(
            ActivitySubPeriodDB.activity_id == activity_id
        ).delete(synchronize_session="fetch")

        # Inserisci i nuovi
        for sp in payload.sub_periods:
            new_sp = ActivitySubPeriodDB(
                activity_id=activity_id,
                name=sp.name,
                dates=sp.dates,
                override_price=sp.override_price,
                override_times=sp.override_times,
                is_closed=sp.is_closed,
                allow_intersections=sp.allow_intersections,
                yellow_threshold=sp.yellow_threshold,
                overbooking_limit=sp.overbooking_limit,
            )
            db.add(new_sp)

    db.commit()
    db.refresh(activity)
    return activity


# ──────────────────────────────────────────────────────────
# GET /daily-schedule — Cruscotto Operativo (solo lavoro reale)
# ──────────────────────────────────────────────────────────
COUNTING_ORDER_STATUSES = {"CONFERMATO", "COMPLETATO", "PAGATO", "IN_ATTESA"}


@router.get("/daily-schedule", response_model=List[DailyScheduleResponse])
def get_daily_schedule(
    start_date: date = Query(..., description="Data inizio range (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Data fine range (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Cruscotto Operativo mensile: ritorna SOLO le discese con prenotazioni reali.
    I giorni senza ordini restano con booked_rides=[] (celle bianche nel calendario).
    """
    from app.schemas.calendar import BookedRideSlot

    # Query ride con attività e ordini nel range
    rides = (
        db.query(DailyRideDB)
        .options(
            joinedload(DailyRideDB.activity),
            joinedload(DailyRideDB.orders),
        )
        .filter(
            DailyRideDB.ride_date >= start_date,
            DailyRideDB.ride_date <= end_date,
        )
        .order_by(DailyRideDB.ride_date, DailyRideDB.ride_time)
        .all()
    )

    # Raggruppa per data, includendo SOLO ride con pax reali > 0
    schedule_dict: dict = {}
    for ride in rides:
        # Calcola pax reali da OrderDB
        pax = sum(
            o.total_pax
            for o in (ride.orders or [])
            if o.order_status in COUNTING_ORDER_STATUSES
        )

        if pax == 0:
            continue  # Skip: nessuna prenotazione reale

        d_str = ride.ride_date.isoformat()
        if d_str not in schedule_dict:
            schedule_dict[d_str] = {
                "date": d_str,
                "booked_rides": [],
                "staff_count": 0,
            }

        # Crea il "mattoncino"
        act = ride.activity
        schedule_dict[d_str]["booked_rides"].append(
            BookedRideSlot(
                time=ride.ride_time.strftime("%H:%M"),
                activity_code=act.code if act else "??",
                color_hex=act.color_hex if act else "#9E9E9E",
                pax=pax,
            )
        )

    # Mocka staff_count (in attesa del modulo HR)
    for day in schedule_dict.values():
        if day["booked_rides"]:
            day["staff_count"] = 5  # placeholder

    return list(schedule_dict.values())


# ──────────────────────────────────────────────────────────
# PUT /daily-rides/{ride_id}/allocations — Assegna Staff e Mezzi
# ──────────────────────────────────────────────────────────
@router.put("/daily-rides/{ride_id}/allocations")
def update_ride_allocations(
    ride_id: str,
    payload: RideAllocationUpdate,
    db: Session = Depends(get_db),
):
    """
    Cantiere 5: Aggiorna le assegnazioni Staff e Fleet per una discesa.
    Sostituisce completamente le liste precedenti.
    Se il turno non esiste ancora in DB (ride teorica con 0 pax), lo crea al volo.
    """
    ride = (
        db.query(DailyRideDB)
        .options(
            joinedload(DailyRideDB.assigned_staff),
            joinedload(DailyRideDB.assigned_fleet),
        )
        .filter(DailyRideDB.id == ride_id)
        .first()
    )

    # ── Lazy creation: il turno non esiste ancora, crealo dal payload ──
    if not ride:
        if not payload.date or not payload.time or not payload.activity_id:
            raise HTTPException(
                status_code=404,
                detail="Discesa non trovata e dati insufficienti per crearla."
            )
        from datetime import datetime as dt_datetime
        ride = DailyRideDB(
            id=ride_id,
            activity_id=payload.activity_id,
            ride_date=dt_datetime.strptime(payload.date, "%Y-%m-%d").date(),
            ride_time=dt_datetime.strptime(payload.time, "%H:%M:%S").time()
                if len(payload.time) > 5
                else dt_datetime.strptime(payload.time, "%H:%M").time(),
        )
        db.add(ride)
        db.flush()
        print(f"[CALENDAR] Lazy-created DailyRideDB {ride.id} for {payload.date} {payload.time}")

    try:
        # Svuota assegnazioni precedenti
        ride.assigned_staff.clear()
        ride.assigned_fleet.clear()

        # Assegna nuovo staff
        if payload.staff_ids:
            staff_members = db.query(StaffDB).filter(StaffDB.id.in_(payload.staff_ids)).all()
            ride.assigned_staff.extend(staff_members)

        # Assegna nuovi mezzi
        if payload.fleet_ids:
            fleet_items = db.query(FleetDB).filter(FleetDB.id.in_(payload.fleet_ids)).all()
            ride.assigned_fleet.extend(fleet_items)

        db.commit()
        return {"status": "ok", "message": f"Assegnate {len(ride.assigned_staff)} guide e {len(ride.assigned_fleet)} mezzi."}

    except Exception as e:
        db.rollback()
        print(f"[CALENDAR] CRASH update_ride_allocations: {e}")
        raise HTTPException(status_code=500, detail=f"Errore assegnazione: {str(e)}")

