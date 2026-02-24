"""
Yield Engine v5 — Motore Matematico BPMN per il Calcolo Posti Vendibili.

Calcola i posti vendibili (pax) incrociando le risorse libere (SQLite)
con le allocazioni gia' assegnate (Supabase ride_allocations) e applicando
i vincoli logistici di acqua (guide + gommoni) e terra (furgoni gancio +
autisti patente C + carrelli).

V5: Parser Temporale BPMN (Workflow Schema)
  - I tempi di occupazione di ogni risorsa sono calcolati dai "mattoncini"
    (blocchi operativi) definiti nel workflow_schema di ogni attivita'.
  - RIMOSSA _get_system_settings (tabella system_settings non piu' usata)
  - RIMOSSA _detect_segment_prefix (tratti ora gestiti dal workflow)
  - RIMOSSA _parse_time (sostituita da parsing interi minuti)
  - Overlap bidimensionale: finestre target vs finestre allocazione

Architettura:
  1. Query Supabase REST per scoprire TUTTE le risorse allocate nel GIORNO
  2. Query SQLite per metadati attivita' -> {activity_id: {dur, seg, workflow_schema}}
  3. Parser BPMN: workflow_schema -> finestre temporali per tipo risorsa
  4. Incrocio -> risorse LIBERE
  5. Greedy match con veto logistico -> pax disponibili
"""
import gc
import httpx
from sqlalchemy.orm import Session

from app.models.calendar import StaffDB, FleetDB, ActivityDB
from app.schemas.availability import AvailabilityRequest, AvailabilityResponse

# ── Costanti (solo ruoli e tipi, nessun valore numerico hardcodato) ──
GUIDE_ROLES = frozenset(['RAF4', 'RAF3', 'SK', 'HYD', 'SH', 'CB'])
DRIVER_ROLES = frozenset(['N', 'C'])
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
# HELPER V5: Matching Ruoli Risorse ↔ Blocchi Workflow
# ══════════════════════════════════════════════════════════════

def _matches_resource_type(block_resources: list, alloc_type: str) -> bool:
    """
    Verifica se un blocco workflow richiede un dato tipo di risorsa.

    Mappa i tag del blocco (es. 'RAF4', 'N', 'VAN') ai tipi Supabase
    (guide, driver, van, raft, trailer).
    """
    if alloc_type == 'guide':
        return any(r in GUIDE_ROLES for r in block_resources)
    if alloc_type == 'driver':
        return any(r in DRIVER_ROLES for r in block_resources)
    if alloc_type == 'van':
        return 'VAN' in block_resources
    if alloc_type == 'raft':
        return 'RAFT' in block_resources
    if alloc_type == 'trailer':
        return 'TRAILER' in block_resources
    return False


# ══════════════════════════════════════════════════════════════
# HELPER V5: Parser Temporale BPMN (Cuore Matematico)
# ══════════════════════════════════════════════════════════════

def _get_resource_windows(
    ride_time: str,
    dur_hours: float,
    workflow: dict,
    alloc_type: str,
) -> list:
    """
    Genera le finestre temporali [(min_start, min_end), ...] in cui
    una risorsa di tipo alloc_type e' effettivamente occupata,
    basandosi sui blocchi del workflow_schema.

    V5: Scostamento temporale cumulativo con Forward Pass (start)
        e Backward Pass (end).

    Se il workflow e' vuoto o nessun blocco coinvolge il tipo risorsa,
    ritorna [] (nessuna finestra = risorsa non richiesta da questo workflow).

    Nota: i tempi sono in MINUTI dall'inizio del giorno (0 = 00:00, 540 = 09:00).
    """
    # Parse ride_time -> minuti
    try:
        parts = str(ride_time).strip()[:5].split(':')
        h, m = int(parts[0]), int(parts[1])
        t_start = h * 60 + m
    except (ValueError, TypeError, IndexError):
        t_start = 9 * 60  # Fallback: 09:00

    dur_h = float(dur_hours) if dur_hours else DEFAULT_DURATION_HOURS
    t_end = t_start + int(dur_h * 60)
    windows = []

    for flow in workflow.get("flows", []):
        blocks = flow.get("blocks", [])

        # ── Forward Pass: blocchi ancorati a 'start' ──
        cursor = t_start
        for b in blocks:
            if b.get('anchor', 'start') == 'end':
                continue
            dur = int(b.get('duration_min', 0))
            if _matches_resource_type(b.get('resources', []), alloc_type):
                windows.append((cursor, cursor + dur))
            cursor += dur

        # ── Backward Pass: blocchi ancorati a 'end' ──
        # Preserva l'ordine cronologico dei blocchi finali
        end_blocks = [b for b in blocks if b.get('anchor') == 'end']
        total_end_dur = sum(int(b.get('duration_min', 0)) for b in end_blocks)
        cursor = t_end - total_end_dur
        for b in end_blocks:
            dur = int(b.get('duration_min', 0))
            if _matches_resource_type(b.get('resources', []), alloc_type):
                windows.append((cursor, cursor + dur))
            cursor += dur

    if not windows:
        return []

    # Ordina e fondi finestre adiacenti o sovrapposte
    windows.sort()
    merged = [windows[0]]
    for current in windows[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return merged


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
# SQLITE: Mappa metadati attivita' (V5: include workflow_schema)
# ══════════════════════════════════════════════════════════════

def _build_activities_meta_map(db: Session) -> dict:
    """
    Costruisce una mappa {activity_id_str: {duration_hours, segments, workflow_schema}}
    da SQLite. V5: include il workflow_schema per il parser BPMN.
    """
    activities = db.query(
        ActivityDB.id,
        ActivityDB.duration_hours,
        ActivityDB.river_segments,
        ActivityDB.workflow_schema,
    ).all()
    return {
        str(a.id): {
            "duration_hours": float(a.duration_hours or DEFAULT_DURATION_HOURS),
            "segments": str(a.river_segments or "").upper(),
            "workflow_schema": a.workflow_schema or {"flows": []},
        }
        for a in activities
    }


# ══════════════════════════════════════════════════════════════
# OVERLAP V5: Calcolo risorse occupate con Parser BPMN
# ══════════════════════════════════════════════════════════════

def _compute_busy_names_with_overlap(
    date_allocations: list,
    target_time: str,
    target_dur: float,
    target_workflow: dict,
    activities_meta: dict,
) -> set:
    """
    Calcola il set di nomi risorse OCCUPATE con il Parser BPMN V5.

    Per ogni allocazione del giorno:
      1. Genera le finestre temporali del TARGET per il tipo risorsa
      2. Genera le finestre temporali dell'ALLOCAZIONE per lo stesso tipo
      3. Verifica overlap matematico rigoroso
    """
    busy_names = set()

    # Pre-calcola le finestre temporali richieste dal target per ogni tipo di risorsa
    target_windows_by_type = {}
    for r_type in ['guide', 'driver', 'van', 'raft', 'trailer']:
        target_windows_by_type[r_type] = _get_resource_windows(
            target_time, target_dur, target_workflow, r_type
        )

    for alloc in date_allocations:
        res_name = alloc.get('resource_name')
        res_type = alloc.get('resource_type')
        if not res_name or not res_type:
            continue

        # Se il target non richiede questo tipo di risorsa, salta
        t_windows = target_windows_by_type.get(res_type, [])
        if not t_windows:
            continue

        # Calcola le finestre in cui la risorsa allocata e' effettivamente occupata
        alloc_act_id = str(alloc.get('activity_id', ''))
        alloc_meta = activities_meta.get(alloc_act_id, {})
        alloc_dur = alloc_meta.get('duration_hours', DEFAULT_DURATION_HOURS)
        alloc_workflow = alloc_meta.get('workflow_schema', {"flows": []})

        a_windows = _get_resource_windows(
            alloc.get('ride_time', '00:00'), alloc_dur, alloc_workflow, res_type
        )

        # Overlap Check Matematico Rigoroso
        overlap_found = False
        for tw_start, tw_end in t_windows:
            for aw_start, aw_end in a_windows:
                if max(tw_start, aw_start) < min(tw_end, aw_end):
                    overlap_found = True
                    break
            if overlap_found:
                break

        if overlap_found:
            busy_names.add(res_name)

    return busy_names


# ══════════════════════════════════════════════════════════════
# MOTORE PRINCIPALE V5
# ══════════════════════════════════════════════════════════════

async def calculate_slot_availability(
    request: AvailabilityRequest,
    db: Session,
) -> AvailabilityResponse:
    """
    Motore V5: calcola i pax vendibili per un dato slot con
    Parser Temporale BPMN e workflow_schema dalle attivita'.

    Flusso:
      Fase 0:  Recupera TUTTE le allocazioni del giorno (Supabase)
      Fase 0b: Costruisci mappa metadati attivita' (SQLite: durata + tratti + workflow)
      Fase 0c: Estrai workflow del target e calcola overlap V5
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

    # ── Fase 0b: Mappa metadati attivita' da SQLite (durata + tratti + workflow) ──
    activities_meta = _build_activities_meta_map(db)

    # ── Fase 0c: Workflow target + Overlap V5 (Parser BPMN) ──
    target_meta = activities_meta.get(str(request.activity_id), {})
    duration_hours = target_meta.get('duration_hours', DEFAULT_DURATION_HOURS)
    target_workflow = target_meta.get('workflow_schema', {"flows": []})

    busy_names = _compute_busy_names_with_overlap(
        date_allocations=day_allocations,
        target_time=request.time,
        target_dur=duration_hours,
        target_workflow=target_workflow,
        activities_meta=activities_meta,
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

    # ── Bottleneck Detection V5 ──
    bottleneck = _detect_bottleneck(
        n_guides=len(free_guides),
        n_rafts=len(free_rafts),
        n_vans_hitch=len(free_vans_hitch),
        n_drivers_c=len(free_drivers_c),
        n_trailers=len(free_trailers),
        transport_cap=transport_capacity,
        water_potential=rafts_to_deploy,
    )

    # ── Debug Info V5 ──
    # Finestre temporali BPMN per debug
    target_guide_windows = _get_resource_windows(request.time, duration_hours, target_workflow, 'guide')
    target_driver_windows = _get_resource_windows(request.time, duration_hours, target_workflow, 'driver')

    def _win_str(windows):
        """Converte finestre (minuti) in stringhe HH:MM leggibili."""
        return [f"{s // 60:02d}:{s % 60:02d}-{e // 60:02d}:{e % 60:02d}" for s, e in windows]

    debug_info = {
        "slot": f"{request.date} {request.time}",
        "engine_version": "V5-BPMN",
        "target_workflow_flows": len(target_workflow.get("flows", [])),
        "target_guide_windows": _win_str(target_guide_windows),
        "target_driver_windows": _win_str(target_driver_windows),
        "day_allocations_total": len(day_allocations),
        "busy_resources_overlap": sorted(busy_names),
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
# BOTTLENECK DETECTION V5 (semplificato, senza settings DB)
# ══════════════════════════════════════════════════════════════

def _detect_bottleneck(
    n_guides: int,
    n_rafts: int,
    n_vans_hitch: int,
    n_drivers_c: int,
    n_trailers: int,
    transport_cap: int,
    water_potential: int,
) -> str:
    """
    Identifica la risorsa che limita la capacita' complessiva.
    V5: Rimosso calcolo capienza netta furgoni (gestito dal workflow).
    """

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
            return "Furgoni con gancio insufficienti per i convogli"
        if n_drivers_c == min_terra:
            return "Autisti patente carrello insufficienti per i convogli"
        return "Carrelli insufficienti per i convogli"

    # Acqua e' il collo di bottiglia
    if n_guides <= n_rafts:
        return "Guide insufficienti (acqua ok, terra ok)"

    return "Gommoni insufficienti (guide disponibili, terra ok)"
