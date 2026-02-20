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
    data_nascita: Optional[str] = Field(default=None, description="dd/mm/yyyy")
    
    # Geografici
    stato_nascita: Optional[str] = None
    comune_nascita: Optional[str] = None
    
    stato_residenza: Optional[str] = None
    comune_residenza: Optional[str] = None
    indirizzo_residenza: Optional[str] = None 

    cittadinanza_scelta: Optional[CitizenshipChoice] = None

    # Documento
    tipo_documento: Optional[str] = Field(default=None, description="Tipo documento")
    numero_documento: Optional[str] = Field(default=None, min_length=1)
    scadenza_documento: Optional[str] = Field(default=None, description="dd/mm/yyyy")

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

    # Firma: accetta sia signatureBase64 (camelCase) sia signature_base64 (snake_case)
    signature_base64: Optional[str] = Field(default=None, alias="signatureBase64")
    
    # NUOVO: Dati biometrici firma a livello root (FEA compliance)
    signature_biometrics: Optional[str] = Field(default=None, alias="signatureBiometrics")

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

        # 3. Validazione Campi Obbligatori Partecipante
        p = self.participant
        if not p.data_nascita:
            raise ValueError(f"Data di nascita mancante per {p.nome}")
        if not p.tipo_documento:
            raise ValueError(f"Tipo documento mancante per {p.nome}")
        if not p.numero_documento:
            raise ValueError(f"Numero documento mancante per {p.nome}")
        if not p.scadenza_documento:
            raise ValueError(f"Scadenza documento mancante per {p.nome}")
        
        self._check_date_format(p.data_nascita, "Data nascita partecipante")
        self._check_date_format(p.scadenza_documento, "Scadenza documento partecipante")
        
        if self.guardian:
            if self.guardian.data_nascita:
                self._check_date_format(self.guardian.data_nascita, "Data nascita tutore")
            if self.guardian.scadenza_documento:
                self._check_date_format(self.guardian.scadenza_documento, "Scadenza documento tutore")

        # 4. Firma: controlla prima root, poi dentro participant
        sig = self.signature_base64
        if not sig and self.participant.signature_base64:
            sig = self.participant.signature_base64
            self.signature_base64 = sig  # Normalizza: copia in root
        
        if not sig or len(sig.strip()) < 20:
            raise ValueError("Firma principale mancante o non valida.")
        
        # 5. Biometrici: normalizza da participant a root se necessario
        if not self.signature_biometrics and self.participant.signature_biometrics:
            self.signature_biometrics = self.participant.signature_biometrics

        return self

    def _check_date_format(self, date_str: Optional[str], field_name: str):
        if not date_str:
            return  # Campo opzionale non presente, skip
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