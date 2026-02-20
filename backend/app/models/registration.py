"""
Modello SQL per l'indice registrazioni.

Questo modello funge da INDICE veloce per le registrazioni salvate su filesystem.
I dati completi (payload.json, signed.pdf, firma, biometrici) restano su disco
per compliance GDPR e per non appesantire il DB con BLOB binari.

La tabella `registrations` contiene solo i campi necessari per:
  - Lista / ricerca rapida
  - Ordinamento per data
  - Filtro per tipologia (minore/adulto)
  - Lock/unlock
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text
from app.db.database import Base


class RegistrationDB(Base):
    __tablename__ = "registrations"

    id = Column(String(36), primary_key=True, index=True, comment="UUID registrazione")
    created_at = Column(DateTime, nullable=False, index=True, comment="Timestamp creazione")
    updated_at = Column(DateTime, nullable=True, comment="Timestamp ultima modifica")

    # Dati anagrafici partecipante (indice per ricerca)
    nome = Column(String(100), nullable=False, default="")
    cognome = Column(String(100), nullable=False, default="")

    # Contatti
    email = Column(String(255), nullable=True, default="")
    telefono = Column(String(50), nullable=True, default="")

    # Stato
    is_minor = Column(Boolean, default=False, comment="True se partecipante minorenne")
    locked = Column(Boolean, default=True, comment="True = registrazione bloccata (non modificabile)")

    # Percorso al PDF firmato (relativo a storage/)
    pdf_path = Column(Text, nullable=True, comment="Path relativo al PDF firmato")

    def __repr__(self):
        return f"<Registration {self.id}: {self.cognome} {self.nome}>"

    def to_list_dict(self) -> dict:
        """Converte il record nel formato JSON atteso dal frontend (q-table)."""
        return {
            "registration_id": self.id,
            "timestamp_iso": self.created_at.isoformat() if self.created_at else None,
            "participant_nome": self.nome,
            "participant_cognome": self.cognome,
            "email": self.email or "",
            "telefono": self.telefono or "",
            "is_minor": self.is_minor,
            "locked": self.locked,
        }
