"""
Modelli SQL per il Motore Calendario (Tetris), Ordini, Transazioni e Logistica.
Sostituisce i file JSON e si aggancia al modello esistente RegistrationDB.

Cantiere 2: aggiunto TransactionDB (ledger multi-pagamento) e campi desk su OrderDB.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Date, Time, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

# Importiamo la Base dalla VOSTRA configurazione esistente
from app.db.database import Base
from sqlalchemy import Table

def generate_uuid():
    return str(uuid.uuid4())

# ==========================================
# 1. CATALOGO ATTIVITÀ (Ex "Seasons")
# ==========================================
class ActivityDB(Base):
    __tablename__ = "activities"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    code = Column(String(20), unique=True, index=True, comment="Es: FAMILY, CLASSICA")
    name = Column(String(100), nullable=False)
    price = Column(Float, default=0.0)
    duration_hours = Column(Float, default=2.0)
    color_hex = Column(String(7), default="#4CAF50")
    river_segments = Column(String(100), nullable=True, comment="Tratti fiume: es. T1,T2")

    # ── GESTIONE STAGIONE ──
    manager = Column(String(50), default="Grape", comment="Grape=no FiRaft, Anatre=sì FiRaft")
    season_start = Column(Date, nullable=True, comment="Inizio stagione")
    season_end = Column(Date, nullable=True, comment="Fine stagione")
    default_times = Column(JSON, default=list, comment='Orari base es ["09:00","14:00"]')
    allow_intersections = Column(Boolean, default=False, comment="True = consenti incroci fiume (ARR)")

    # ── YIELD MANAGEMENT ──
    activity_class = Column(String(20), default="RAFTING", comment="RAFTING, HYDRO, KAYAK")
    yellow_threshold = Column(Integer, default=8, comment="Posti residui per giallo")
    overbooking_limit = Column(Integer, default=0, comment="Posti extra vendibili")

    # ── WORKFLOW BPMN (Lego Blocks) ──
    workflow_schema = Column(JSON, default=dict, comment='Schema flussi operativi {"flows":[...]}')

    is_active = Column(Boolean, default=True)

    rides = relationship("DailyRideDB", back_populates="activity")
    sub_periods = relationship("ActivitySubPeriodDB", back_populates="activity",
                               cascade="all, delete-orphan", lazy="joined")


# ==========================================
# 1b. SOTTOPERIODI / ECCEZIONI STAGIONALI
# ==========================================
class ActivitySubPeriodDB(Base):
    """Sovrascrittura prezzo/orari per un sottoperiodo dell'attività."""
    __tablename__ = "activity_sub_periods"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    activity_id = Column(String(36), ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=True, comment="Es. Weekend Settembre")
    dates = Column(JSON, default=list, comment='Lista piatta ["2026-08-01","2026-08-02",...]')
    override_price = Column(Float, nullable=True, comment="Prezzo sovrascr. per questo periodo")
    override_times = Column(JSON, default=list, comment='Orari sovrascr. es ["09:30","15:00"]')
    is_closed = Column(Boolean, default=False, comment="True = attività chiusa in queste date")
    allow_intersections = Column(Boolean, nullable=True, comment="Sovrascrive ARR per queste date")
    yellow_threshold = Column(Integer, nullable=True, comment="Override soglia giallo")
    overbooking_limit = Column(Integer, nullable=True, comment="Override overbooking")

    activity = relationship("ActivityDB", back_populates="sub_periods")

# ==========================================
# 2a. TABELLE ASSOCIATIVE M2M (Cantiere 5)
# ==========================================
ride_staff_link = Table(
    "ride_staff_link", Base.metadata,
    Column("ride_id", String(36), ForeignKey("daily_rides.id", ondelete="CASCADE"), primary_key=True),
    Column("staff_id", String(36), ForeignKey("staff.id", ondelete="CASCADE"), primary_key=True),
)

ride_fleet_link = Table(
    "ride_fleet_link", Base.metadata,
    Column("ride_id", String(36), ForeignKey("daily_rides.id", ondelete="CASCADE"), primary_key=True),
    Column("fleet_id", String(36), ForeignKey("fleet.id", ondelete="CASCADE"), primary_key=True),
)

# ==========================================
# 2. LA DISCESA FISICA (Il "Quadratino" sul Tetris)
# ==========================================
class DailyRideDB(Base):
    __tablename__ = "daily_rides"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    activity_id = Column(String(36), ForeignKey("activities.id"), nullable=False)
    
    ride_date = Column(Date, nullable=False, index=True)
    ride_time = Column(Time, nullable=False, index=True)
    
    # Semafori: "A" (Verde), "B" (Giallo), "C" (Rosso), "D" (Blu)
    status = Column(String(1), default="A") 
    is_overridden = Column(Boolean, default=False, comment="True se semaforo forzato a mano")
    notes = Column(Text, nullable=True)

    activity = relationship("ActivityDB", back_populates="rides")
    orders = relationship("OrderDB", back_populates="ride")
    crew_assignments = relationship("CrewAssignmentDB", back_populates="ride")

    # ── Cantiere 5: Assegnazione diretta Staff e Mezzi (M2M) ──
    assigned_staff = relationship("StaffDB", secondary=ride_staff_link, lazy="joined")
    assigned_fleet = relationship("FleetDB", secondary=ride_fleet_link, lazy="joined")

# ==========================================
# 3. PRENOTAZIONE COMMERCIALE (Il "Carrello")
# ==========================================
class OrderDB(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    ride_id = Column(String(36), ForeignKey("daily_rides.id"), nullable=False)
    
    order_status = Column(String(20), default="IN_ATTESA") # IN_ATTESA, CONFERMATO, COMPLETATO, PAGATO
    total_pax = Column(Integer, default=1)
    
    price_total = Column(Float, default=0.0)
    price_paid = Column(Float, default=0.0)
    payment_type = Column(String(50), nullable=True)
    
    is_exclusive_raft = Column(Boolean, default=False, comment="True se il gruppo vuole gommone privato")
    discount_applied = Column(Float, default=0.0, comment="Percentuale sconto applicata (es. 0.10 = 10%)")
    
    # Chi ha prenotato online (non per forza chi scende in acqua)
    customer_name = Column(String(100), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # ── CAMPI DESK / SEGRETERIA (Cantiere 2) ──
    booker_name = Column(String(100), nullable=True, comment="Referente gruppo")
    booker_phone = Column(String(50), nullable=True)
    booker_email = Column(String(255), nullable=True)
    adjustments = Column(Float, default=0.0, comment="Penali no-show (+) o sconti (-)")
    extras = Column(JSON, default=list, comment='Es. [{"name":"Foto","price":15}]')
    source = Column(String(20), default="WEB", comment="WEB, DESK, PARTNER")

    ride = relationship("DailyRideDB", back_populates="orders")
    
    # ---> IL PONTE D'ORO: 1 Ordine contiene N Registrazioni Fisiche (Kiosk)
    registrations = relationship("RegistrationDB", back_populates="order", cascade="all, delete-orphan")
    # ---> LIBRO MASTRO: 1 Ordine ha N Transazioni (multi-pagamento)
    transactions = relationship("TransactionDB", back_populates="order", cascade="all, delete-orphan")

# ==========================================
# 3b. TRANSAZIONE (Libro Mastro Multi-Pagamento)
# ==========================================
class TransactionDB(Base):
    """Singolo movimento contabile associato a un ordine."""
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False, comment="Importo del pagamento")
    method = Column(String(20), nullable=False, comment="CASH, SUMUP, BONIFICO, PARTNERS")
    type = Column(String(20), default="SALDO", comment="CAPARRA, SALDO")
    note = Column(String(255), nullable=True, comment='Es. "Voucher Smartbox"')
    timestamp = Column(DateTime, default=datetime.utcnow)

    order = relationship("OrderDB", back_populates="transactions")

# ==========================================
# 4. LOGISTICA E ASSEGNAZIONI (Guide e Gommoni reali)
# ==========================================
class StaffDB(Base):
    __tablename__ = "staff"
    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(100), nullable=False)
    contract_type = Column(String(20), default="FISSO", comment="FISSO o EXTRA")
    is_guide = Column(Boolean, default=False)
    is_driver = Column(Boolean, default=False, comment="Patente navetta")
    roles = Column(JSON, default=list, comment='Multi-ruolo: ["RAF4","SK","NC"]')
    contract_periods = Column(JSON, default=list, comment='[{"start":"2026-05-01","end":"2026-09-30"}]')
    is_active = Column(Boolean, default=True)
    
    crew_assignments = relationship("CrewAssignmentDB", back_populates="guide")

class FleetDB(Base):
    __tablename__ = "fleet"
    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(20), default="RAFT", comment="RAFT, VAN, TRAILER")
    total_quantity = Column(Integer, default=1, comment="Quanti mezzi di questo tipo")
    capacity_per_unit = Column(Integer, default=8, comment="Posti per singolo mezzo (legacy)")
    is_active = Column(Boolean, default=True)
    # ── Parametri Logistici per Algoritmo Yield ──
    capacity = Column(Integer, default=0, comment="Capienza passeggeri (gommoni) o posti a sedere escluso autista (furgoni)")
    has_tow_hitch = Column(Boolean, default=False, comment="Solo VAN: dotato di gancio traino")
    max_rafts = Column(Integer, default=0, comment="Solo TRAILER: quanti gommoni può trasportare")

    crew_assignments = relationship("CrewAssignmentDB", back_populates="boat")

class CrewAssignmentDB(Base):
    """Assegna un Gommone e una Guida a uno specifico turno/discesa"""
    __tablename__ = "crew_assignments"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    ride_id = Column(String(36), ForeignKey("daily_rides.id"), nullable=False)
    boat_id = Column(String(36), ForeignKey("fleet.id"), nullable=True)
    guide_id = Column(String(36), ForeignKey("staff.id"), nullable=True)

    ride = relationship("DailyRideDB", back_populates="crew_assignments")
    boat = relationship("FleetDB", back_populates="crew_assignments")
    guide = relationship("StaffDB", back_populates="crew_assignments")

# ==========================================
# 5. DIARIO RISORSE UNIFICATO (Eccezioni a Calendario)
# ==========================================
class ResourceExceptionDB(Base):
    """
    Diario unificato per Staff e Fleet.
    - Risorse Fisse (Staff FISSO, Gommoni): di base PRESENTI.
      Le eccezioni registrano le ASSENZE (is_available=False).
    - Risorse Extra (Staff EXTRA): di base ASSENTI.
      Le eccezioni registrano le PRESENZE (is_available=True).
    """
    __tablename__ = "resource_exceptions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    resource_id = Column(String(36), nullable=False, index=True,
        comment="ID dello Staff o del Fleet")
    resource_type = Column(String(20), nullable=False,
        comment="STAFF o FLEET")
    name = Column(String(100), nullable=True,
        comment="Es. Ferie, Turno, Guasto")
    is_available = Column(Boolean, nullable=False,
        comment="False=assenza (Fissi), True=presenza (Extra)")
    dates = Column(JSON, default=list,
        comment='Array piatto ["2026-08-15","2026-08-16"]')

# ==========================================
# 6. IMPOSTAZIONI SISTEMA (Kill Switch, ecc.)
# ==========================================
class SystemSettingDB(Base):
    """Chiave-valore per configurazioni globali del sistema."""
    __tablename__ = "system_settings"

    key = Column(String(50), primary_key=True, index=True)
    value = Column(String(255), nullable=False)
    category = Column(String(50), nullable=True, default="Generale", comment="Gruppo logico: Capienze Mezzi, Tempi Base, ecc.")
    description = Column(String(255), nullable=True, comment="Descrizione leggibile per la UI")