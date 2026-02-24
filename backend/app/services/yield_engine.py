"""
Yield Engine v4 — Motore Matematico per il Calcolo Posti Vendibili.

Calcola i posti vendibili (pax) incrociando le risorse libere (SQLite)
con le allocazioni già assegnate (Supabase ride_allocations) e applicando
i vincoli logistici di acqua (guide + gommoni) e terra (furgoni gancio +
autisti patente C + carrelli).

V4: Variabili Dinamiche dal DB (Pannello Impostazioni)
  - Capienze furgoni lette da system_settings (van_total_seats, van_driver_seats, van_guide_seats)
  - Tempi Navetta Elastica letti da system_settings per tratto (briefing + prep, return_to_base)
  - RIMOSSA costante globale SHUTTLE_MINUTES
  - RIMOSSO divisore hardcodato / 7

Architettura:
  1. Query Supabase REST per scoprire TUTTE le risorse allocate nel GIORNO
  2. Query SQLite per metadati attivita' -> {activity_id: {dur, seg}}
  3. Estrazione settings dal DB (system_settings -> dict piatto)
  4. Calcolo finestre temporali differenziate Acqua vs Terra (tempi dal DB)
  5. Incrocio -> risorse LIBERE
  6. Greedy match con veto logistico -> pax disponibili
"""
import gc
import httpx
from datetime import datetime as dt_datetime, timedelta
from sqlalchemy.orm import Session

from app.models.calendar import StaffDB, FleetDB, ActivityDB, SystemSettingDB
from app.schemas.availability import AvailabilityRequest, AvailabilityResponse

# ── Costanti (solo ruoli e tipi, nessun valore numerico hardcodato) ──
GUIDE_ROLES = frozenset(['RAF4', 'RAF3', 'SK', 'HYD', 'SH', 'CB'])
DEFAULT_DURATION_HOURS = 2.0
WATER_RESOURCE_TYPES = frozenset(['guide', 'raft'])
LAND_RESOURCE_TYPES = frozenset(['driver', 'van', 'trailer'])

# ── Credenziali Supabase (anon key, stesse del frontend) ──
_SUPABASE_URL = "https://tttyeluyutbpczbslgwi.supabase.co"
_SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0dHllbHV5dXRicGN6YnNsZ3dpIiwi"
    "cm9sZSI6ImFub24iLCJpYXQiOjE3NzE3Nzg5NTIsImV4cCI6MjA4NzM1NDk1Mn0."
    "kdcJtU_LHkZv20MFxDQZGkn2iz4ZBuZC3dQjLxWoaTs"
)


# ══════════════════════════════════════════════════════════════
# HELPER: Estrazione Settings dal DB
# ══════════════════════════════════════════════════════════════

def _get_system_settings(db: Session) -> dict:
    """
    Estrae tutte le chiavi dalla tabella system_settings e ritorna
    un dict piatto: {key: float(valore)} dove possibile.

    In caso di eccezione o tabella vuota ritorna un dict vuoto {}.
    """
    try:
        rows = db.query(SystemSettingDB.key, SystemSettingDB.value).all()
        if not rows:
            return {}
        result = {}
        for row in rows:
            k = row.key
            v = row.value
            try:
                result[k] = float(v)
            except (ValueError, TypeError):
                result[k] = v  # Conserva come stringa se non numerico
        return result
    except Exception as e:
        print(f"[YieldEngine] Errore lettura system_settings: {e}")
        return {}


# ══════════════════════════════════════════════════════════════
# HELPERS: Finestre Temporali V4
# ══════════════════════════════════════════════════════════════

def _parse_time(time_str: str) -> dt_datetime:
    """Converte HH:MM o HH:MM:SS in datetime (solo componente oraria)."""
    try:
        clean = str(time_str).strip()[:5]
        return dt_datetime.strptime(clean, "%H:%M")
    except (ValueError, TypeError):
        return dt_datetime.strptime("00:00", "%H:%M")


def _detect_segment_prefix(segments: str) -> str:
    """
    Determina il prefisso per le chiavi settings in base al tratto fiume.

    Se contiene 'B' -> 'b_'
    Se contiene 'C' (e non B) -> 'c_'
    Altrimenti -> 'a_' (default)
    """
    seg_upper = str(segments or "").upper().strip()
    if "B" in seg_upper:
        return "b_"
    if "C" in seg_upper:
        return "c_"
    return "a_"


def _get_resource_windows(
    start_time: dt_datetime,
    duration_hours: float,
    segments: str,
    is_water: bool,
    settings: dict,
) -> list:
    """
    Genera la lista di finestre temporali [(start, end), ...] per una risorsa.

    V4: Tempi letti dal DB (settings dict) in base al tratto fiume.

    Acqua: sempre blocco unico [start, end].
    Terra:
      - Tratto A presente (o nessun tratto, o durata <= 1h): Ammiraglia -> blocco unico.
      - Solo Tratti B/C: Navetta Elastica -> due finestre calcolate:
        * Drop-off (Andata): [start, start + briefing + prep_ti_im]
        * Pick-up  (Ritorno): [end - return_to_base, end]
    """
    dur = float(duration_hours or DEFAULT_DURATION_HOURS)
    end_time = start_time + timedelta(hours=dur)

    # Acqua: sempre blocco continuo
    if is_water:
        return [(start_time, end_time)]

    # Terra: controlla i tratti fiume
    seg_upper = str(segments or "").upper().strip()

    # Ammiraglia: Tratto A presente, nessun tratto specificato, o durata troppo corta
    if not seg_upper or "A" in seg_upper or dur <= 1.0:
        return [(start_time, end_time)]

    # ── Navetta Elastica: solo Tratti B/C ──
    # Determina prefisso per lookup settings
    prefix = _detect_segment_prefix(segments)

    # Finestra Drop-off (Andata): briefing + preparazione TI + imbarco
    briefing_min = float(settings.get('briefing_duration_min', 30.0))
    prep_ti_im_min = float(settings.get(f'{prefix}prep_ti_im_min', 20.0))
    dropoff_duration = briefing_min + prep_ti_im_min
    dropoff_end = start_time + timedelta(minutes=dropoff_duration)

    # Finestra Pick-up (Ritorno): ritorno in base
    pickup_min = float(settings.get(f'{prefix}return_to_base_min', 20.0))
    pickup_start = end_time - timedelta(minutes=pickup_min)

    # Safety Fallback: se dropoff >= pickup, blocco unico continuo
    if dropoff_end >= pickup_start:
        return [(start_time, end_time)]

    return [(start_time, dropoff_end), (pickup_start, end_time)]


def _has_overlap(windows1: list, windows2: list) -> bool:
    """Verifica se almeno una coppia di finestre si sovrappone."""
    for s1, e1 in windows1:
        for s2, e2 in windows2:
            if max(s1, s2) < min(e1, e2):
                return True
    return False


# ══════════════════════════════════════════════════════════════
# SUPABASE: Fetch allocazioni giornaliere
# ══════════════════════════════════════════════════════════════

async def _fetch_day_allocations(date: str) -> list:
    """
    Interroga Supabase REST API per ottenere TUTTE le allocazioni
    del giorno, comprensive di orario turno e activity_id.

    Tabella: rides -> ride_allocations -> resources
    Risultato: lista di dict con ride_id, ride_time, activity_id, resource_name, resource_type
    """
    allocations = []
    headers = {
        "apikey": _SUPABASE_KEY,
        "Authorization": f"Bearer {_SUPABASE_KEY}",
        "Accept": "application/json",
    }

    # Query REST Supabase: TUTTI i turni del giorno con allocazioni
    url = (
        f"{_SUPABASE_URL}/rest/v1/rides"
        f"?select=id,time,activity_id,ride_allocations(resource_id,resources(name,type))"
        f"&date=eq.{date}"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                print(f"[YieldEngine] Supabase query error {resp.status_code}: {resp.text[:200]}")
                return allocations

            rides = resp.json()
            if not isinstance(rides, list):
                return allocations

            for ride in rides:
                ride_id = ride.get("id")
                ride_time = ride.get("time", "00:00")
                activity_id = ride.get("activity_id")
                ride_allocs = ride.get("ride_allocations") or []
                for alloc in ride_allocs:
                    resource = alloc.get("resources")
                    if resource and isinstance(resource, dict) and resource.get("name"):
                        allocations.append({
                            "ride_id": ride_id,
                            "ride_time": ride_time,
                            "activity_id": activity_id,
                            "resource_name": resource["name"].strip().lower(),
                            "resource_type": resource.get("type", ""),
                        })
    except httpx.ConnectError as e:
        print(f"[YieldEngine] Supabase non raggiungibile: {e}")
    except httpx.TimeoutException as e:
        print(f"[YieldEngine] Timeout connessione Supabase: {e}")
    except Exception as e:
        print(f"[YieldEngine] Errore connessione Supabase: {e}")

    return allocations


# ══════════════════════════════════════════════════════════════
# SQLITE: Mappa metadati attivita'
# ══════════════════════════════════════════════════════════════

def _build_activities_meta_map(db: Session) -> dict:
    """
    Costruisce una mappa {activity_id_str: {dur, seg}} da SQLite.
    Contiene durata e tratti fiume per ogni attivita'.
    """
    activities = db.query(
        ActivityDB.id,
        ActivityDB.duration_hours,
        ActivityDB.river_segments,
    ).all()
    return {
        str(a.id): {
            "dur": float(a.duration_hours or DEFAULT_DURATION_HOURS),
            "seg": str(a.river_segments or "").upper(),
        }
        for a in activities
    }


# ══════════════════════════════════════════════════════════════
# OVERLAP V4: Calcolo risorse occupate con Logistica Elastica
# ══════════════════════════════════════════════════════════════

def _compute_busy_names_with_overlap(
    day_allocations: list,
    target_time: str,
    target_activity_id: str,
    target_ride_id: str,
    meta_map: dict,
    settings: dict,
) -> set:
    """
    Calcola il set di nomi risorse OCCUPATE con Logistica Elastica V4.

    Per ogni allocazione del giorno:
      1. Determina se la risorsa e' Acqua o Terra
      2. Genera le finestre temporali appropriate (tempi dal DB):
         - Acqua: blocco unico [start, end]
         - Terra con Tratto A: blocco unico (Ammiraglia)
         - Terra solo B/C: due finestre drop-off + pick-up (Navetta Elastica)
      3. Confronta con le finestre del turno target
    """
    busy = set()

    # Metadati del turno target
    target_meta = meta_map.get(str(target_activity_id), {"dur": DEFAULT_DURATION_HOURS, "seg": ""})
    target_start = _parse_time(target_time)

    for alloc in day_allocations:
        # Salta il turno che stiamo calcolando (non compete con se stesso)
        if target_ride_id and str(alloc.get("ride_id", "")) == str(target_ride_id):
            continue

        name = alloc.get("resource_name")
        if not name:
            continue

        resource_type = str(alloc.get("resource_type", "")).lower()
        is_water = resource_type in WATER_RESOURCE_TYPES

        # Metadati del turno allocato
        alloc_act_id = alloc.get("activity_id", "")
        alloc_meta = meta_map.get(str(alloc_act_id), {"dur": DEFAULT_DURATION_HOURS, "seg": ""})
        alloc_start = _parse_time(alloc.get("ride_time", "00:00"))

        # Finestre target (dipendono dal tipo di risorsa che stiamo valutando)
        target_windows = _get_resource_windows(
            target_start, target_meta["dur"], target_meta["seg"], is_water, settings
        )
        # Finestre allocazione (dipendono dal tipo di risorsa e dai tratti)
        alloc_windows = _get_resource_windows(
            alloc_start, alloc_meta["dur"], alloc_meta["seg"], is_water, settings
        )

        # Check sovrapposizione
        if _has_overlap(target_windows, alloc_windows):
            busy.add(name)

    return busy


# ══════════════════════════════════════════════════════════════
# MOTORE PRINCIPALE V4
# ══════════════════════════════════════════════════════════════

async def calculate_slot_availability(
    request: AvailabilityRequest,
    db: Session,
) -> AvailabilityResponse:
    """
    Motore V4: calcola i pax vendibili per un dato slot con
    disaccoppiamento Acqua/Terra, Logistica Elastica e
    variabili dinamiche dal DB (Pannello Impostazioni).

    Flusso:
      Fase 0:  Recupera TUTTE le allocazioni del giorno (Supabase)
      Fase 0b: Costruisci mappa metadati attivita' (SQLite: durata + tratti)
      Fase 0c: Estrai settings dal DB (system_settings)
      Fase 0d: Calcola risorse occupate con overlap V4 (Acqua/Terra split, tempi dal DB)
      Fase 1:  Recupera risorse totali attive (SQLite), filtra libere
      Fase A:  Potenziale Acqua (guide x gommoni)
      Fase B:  Veto Logistico Terra (furgoni gancio x autisti C x carrelli)
      Fase C:  Risoluzione limite
      Fase D:  Calcolo PAX finale
    """

    # ── Fase 0: Allocazioni giornaliere (Supabase) ──
    try:
        day_allocations = await _fetch_day_allocations(request.date)
    except Exception as e:
        print(f"[YieldEngine] Errore fase 0 (Supabase): {e}")
        day_allocations = []  # Graceful degradation: assume tutto libero

    # ── Fase 0b: Mappa metadati attivita' da SQLite (durata + tratti fiume) ──
    meta_map = _build_activities_meta_map(db)

    # ── Fase 0c: Settings dal DB (system_settings -> dict piatto) ──
    settings = _get_system_settings(db)

    # ── Fase 0d: Risorse occupate con overlap temporale V4 (Acqua/Terra split, tempi dal DB) ──
    busy_names = _compute_busy_names_with_overlap(
        day_allocations=day_allocations,
        target_time=request.time,
        target_activity_id="",  # TODO: aggiungere activity_id al request quando necessario
        target_ride_id="",
        meta_map=meta_map,
        settings=settings,
    )

    # ── Fase 1: Risorse attive da SQLite ──
    all_staff = db.query(StaffDB).filter(StaffDB.is_active == True).all()  # noqa: E712
    all_fleet = db.query(FleetDB).filter(FleetDB.is_active == True).all()  # noqa: E712

    def is_free(name) -> bool:
        """Controlla se una risorsa e' libera (null-safe)."""
        if not name:
            return False
        return str(name).strip().lower() not in busy_names

    # Guide libere: staff con almeno un ruolo nautico e non occupato
    free_guides = [
        s for s in all_staff
        if s.name and is_free(s.name)
        and any(r in GUIDE_ROLES for r in (s.roles or []))
    ]

    # Autisti con patente carrello: staff libero con ruolo 'C'
    free_drivers_c = [
        s for s in all_staff
        if s.name and is_free(s.name)
        and 'C' in (s.roles or [])
    ]

    # Gommoni liberi, ordinati per capienza decrescente (prima i piu' grandi)
    free_rafts = sorted(
        [f for f in all_fleet if f.category == 'RAFT' and f.name and is_free(f.name)],
        key=lambda r: (r.capacity or 0),
        reverse=True,
    )

    # Furgoni liberi con gancio traino
    free_vans_hitch = [
        f for f in all_fleet
        if f.category == 'VAN' and f.has_tow_hitch and f.name and is_free(f.name)
    ]

    # Carrelli liberi, ordinati per max_rafts decrescente
    free_trailers = sorted(
        [f for f in all_fleet if f.category == 'TRAILER' and f.name and is_free(f.name)],
        key=lambda t: (t.max_rafts or 0),
        reverse=True,
    )

    # ── Fase A: Potenziale Acqua ──
    # I gommoni teorici mettibili in acqua: limitati da guide E gommoni
    rafts_to_deploy = min(len(free_guides), len(free_rafts))

    # ── Fase B: Veto Logistico Terra (La Trinita' del Trasporto) ──
    # Un "Convoglio" richiede: 1 Furgone Gancio + 1 Autista Pat.C + 1 Carrello
    max_convoys = min(
        len(free_vans_hitch),
        len(free_drivers_c),
        len(free_trailers),
    )

    if max_convoys > 0:
        selected_trailers = free_trailers[:max_convoys]
        transport_capacity = sum(t.max_rafts or 0 for t in selected_trailers)
    else:
        selected_trailers = []
        transport_capacity = 0

    # ── Fase C: Risoluzione del Limite ──
    # I gommoni che realmente possono partire = min(acqua, terra)
    actual_rafts = min(rafts_to_deploy, transport_capacity)

    # ── Fase D: Calcolo PAX Finale ──
    selected_rafts = free_rafts[:actual_rafts]
    available_pax = sum(r.capacity or 0 for r in selected_rafts)

    # ── Bottleneck Detection (V4: capienza furgoni dal DB) ──
    bottleneck = _detect_bottleneck(
        n_guides=len(free_guides),
        n_rafts=len(free_rafts),
        n_vans_hitch=len(free_vans_hitch),
        n_drivers_c=len(free_drivers_c),
        n_trailers=len(free_trailers),
        transport_cap=transport_capacity,
        water_potential=rafts_to_deploy,
        settings=settings,
    )

    # ── Debug Info (V4: Acqua/Terra split + Logistica Elastica + Settings DB) ──
    # Capienza netta furgone dal DB
    van_net_cap = (
        float(settings.get('van_total_seats', 9.0))
        - float(settings.get('van_driver_seats', 1.0))
        - float(settings.get('van_guide_seats', 0.0))
    )
    if van_net_cap <= 0:
        van_net_cap = 7.0

    target_meta = meta_map.get("", {"dur": DEFAULT_DURATION_HOURS, "seg": ""})
    target_s = _parse_time(request.time)
    target_e = target_s + timedelta(hours=target_meta["dur"])
    debug_info = {
        "slot": f"{request.date} {request.time}",
        "engine_version": "V4-dynamic",
        "target_window": f"{target_s.strftime('%H:%M')}-{target_e.strftime('%H:%M')}",
        "day_allocations_total": len(day_allocations),
        "busy_resources_overlap": sorted(busy_names),
        "settings_loaded": len(settings),
        "van_net_capacity": van_net_cap,
        "free_guides": [s.name for s in free_guides],
        "free_drivers_c": [s.name for s in free_drivers_c],
        "free_rafts": [
            {"name": r.name, "capacity": r.capacity or 0} for r in free_rafts
        ],
        "free_vans_hitch": [v.name for v in free_vans_hitch],
        "free_trailers": [
            {"name": t.name, "max_rafts": t.max_rafts or 0} for t in free_trailers
        ],
        "phase_a_rafts_to_deploy": rafts_to_deploy,
        "phase_b_max_convoys": max_convoys,
        "phase_b_transport_capacity": transport_capacity,
        "phase_c_actual_rafts": actual_rafts,
        "phase_d_available_pax": available_pax,
        "selected_rafts": [r.name for r in selected_rafts],
        "selected_trailers": [t.name for t in selected_trailers],
    }

    # ── Lazy cleanup (regola Ergonet: gc.collect dopo inferenza pesante) ──
    gc.collect()

    return AvailabilityResponse(
        available_pax=available_pax,
        bottleneck=bottleneck,
        debug_info=debug_info,
    )


# ══════════════════════════════════════════════════════════════
# BOTTLENECK DETECTION (V4: capienza furgoni dal DB)
# ══════════════════════════════════════════════════════════════

def _detect_bottleneck(
    n_guides: int,
    n_rafts: int,
    n_vans_hitch: int,
    n_drivers_c: int,
    n_trailers: int,
    transport_cap: int,
    water_potential: int,
    settings: dict,
) -> str:
    """
    Identifica la risorsa che limita la capacita' complessiva.

    V4: Usa capienza netta furgone dal DB per calcolo 'Mezzi In Difetto'.
    """

    # Capienza netta furgone dal DB
    van_net_cap = (
        float(settings.get('van_total_seats', 9.0))
        - float(settings.get('van_driver_seats', 1.0))
        - float(settings.get('van_guide_seats', 0.0))
    )
    if van_net_cap <= 0:
        van_net_cap = 7.0  # Fallback safety

    # Nessuna risorsa
    if n_guides == 0 and n_rafts == 0:
        return "Nessuna guida e nessun gommone disponibile"
    if n_guides == 0:
        return "Nessuna guida disponibile"
    if n_rafts == 0:
        return "Nessun gommone disponibile"

    # Vincoli terra mancanti
    if n_vans_hitch == 0:
        return "Nessun furgone con gancio traino disponibile"
    if n_drivers_c == 0:
        return "Nessun autista con patente carrello disponibile"
    if n_trailers == 0:
        return "Nessun carrello disponibile"

    # Terra e' il collo di bottiglia?
    if transport_cap < water_potential:
        min_terra = min(n_vans_hitch, n_drivers_c, n_trailers)
        if n_vans_hitch == min_terra:
            return f"Furgoni con gancio insufficienti per i convogli (cap. netta: {van_net_cap:.0f} pax)"
        if n_drivers_c == min_terra:
            return "Autisti patente carrello insufficienti per i convogli"
        return "Carrelli insufficienti per i convogli"

    # Acqua e' il collo di bottiglia
    if n_guides <= n_rafts:
        return "Guide insufficienti (acqua ok, terra ok)"

    return "Gommoni insufficienti (guide disponibili, terra ok)"
