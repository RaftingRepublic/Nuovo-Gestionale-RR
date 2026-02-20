from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict, model_validator
from datetime import datetime

CitizenshipChoice = Literal["ITALIANA", "NON_ITALIANA"]

DocType = Literal[
    "CIE",
    "CI_CARTACEA",
    "PATENTE_IT",
    "PASSAPORTO",
    "PERMESSO_SOGGIORNO",
    "ALTRO",
]

class LegalConsents(BaseModel):
    """
    Schema consensi con alias per compatibilità Frontend (camelCase).
    """
    privacy: bool = False
    informed_consent: bool = Field(False, alias="informedConsent")
    responsibility: bool = False
    tesseramento: bool = False
    
    photo: bool = Field(False, alias="photoConsent") 
    newsletter: bool = Field(False, alias="newsletterConsent")

    model_config = ConfigDict(populate_by_name=True)

class PersonData(BaseModel):
    """
    Dati anagrafici con alias per mapping diretto dallo Store Frontend.
    """
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    nome: str = Field(..., min_length=1)
    cognome: str = Field(..., min_length=1)
    data_nascita: str = Field(..., description="dd/mm/yyyy")
    
    # Geografici
    stato_nascita: Optional[str] = None
    comune_nascita: Optional[str] = None
    
    stato_residenza: Optional[str] = None
    comune_residenza: Optional[str] = None
    indirizzo_residenza: Optional[str] = None 

    cittadinanza_scelta: Optional[CitizenshipChoice] = None

    # Documento
    tipo_documento: DocType = Field(..., description="Tipo documento obbligatorio")
    numero_documento: str = Field(..., min_length=2)
    scadenza_documento: str = Field(..., description="dd/mm/yyyy")

    source: Optional[str] = None
    
    # FIRME
    signature_base64: Optional[str] = Field(default=None, alias="signature")
    
    # NUOVO: Dati biometrici forensi (FEA)
    # Riceve la stringa JSON grezza dal frontend
    signature_biometrics: Optional[str] = Field(default=None, alias="signatureBiometrics")

    legal_consents: Optional[LegalConsents] = Field(default=None, alias="legal")

class ContactData(BaseModel):
    email: EmailStr
    telefono: str = Field(..., min_length=5)

class RegistrationPayload(BaseModel):
    """
    Payload registrazione completo.
    """
    model_config = ConfigDict(populate_by_name=True)

    language: str = "it"
    booking_id: Optional[str] = None

    tutor_participates: Optional[bool] = Field(default=None, alias="tutorParticipates")
    has_minors: Optional[bool] = Field(default=None, alias="hasMinors")

    is_minor: bool = False
    participant: PersonData
    guardian: Optional[PersonData] = None

    contact: ContactData
    
    # Legacy root legal, mantenuto per sicurezza
    legal: Optional[LegalConsents] = None

    signature_base64: str = Field(..., alias="signatureBase64")

    @model_validator(mode="after")
    def _validate(self):
        # 1. Validazione Consensi
        consents = self.participant.legal_consents or self.legal
        
        if not consents:
            raise ValueError(f"Consensi mancanti per {self.participant.nome}")

        if not consents.privacy:
            raise ValueError(f"Privacy Policy non accettata per {self.participant.nome}")
        if not consents.informed_consent:
            raise ValueError(f"Consenso informato non accettato per {self.participant.nome}")
        
        # 2. Minore e Guardian
        if self.is_minor and self.guardian is None:
            raise ValueError("Partecipante minorenne: guardian obbligatorio.")

        # 3. Validità Date
        self._check_date_format(self.participant.data_nascita, "Data nascita partecipante")
        self._check_date_format(self.participant.scadenza_documento, "Scadenza documento partecipante")
        
        if self.guardian:
            self._check_date_format(self.guardian.data_nascita, "Data nascita tutore")
            self._check_date_format(self.guardian.scadenza_documento, "Scadenza documento tutore")

        # 4. Firma (Controllo sulla firma root del payload)
        if not self.signature_base64 or len(self.signature_base64.strip()) < 20:
            raise ValueError("Firma principale mancante o non valida.")

        return self

    def _check_date_format(self, date_str: str, field_name: str):
        try:
            datetime.strptime(date_str, "%d/%m/%Y")
        except (ValueError, TypeError):
            raise ValueError(f"{field_name}: formato data non valido (richiesto GG/MM/AAAA)")

class DocumentScanResponse(BaseModel):
    detected_doc_type: DocType
    mrz_nationality: Optional[str] = None
    extracted: dict = Field(default_factory=dict)

class RegistrationSubmitResponse(BaseModel):
    registration_id: str
    timestamp_iso: str
    pdf_filename: str
    emailed_to: Optional[EmailStr] = None