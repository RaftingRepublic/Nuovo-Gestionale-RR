from __future__ import annotations

import os
import uuid
import json
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.schemas.registration import RegistrationPayload
from app.services.registration.email_service import EmailService
from app.services.registration.pdf_service import PdfService
from app.services.registration.storage_service import StorageService


def _parse_ddmmyyyy(s: str) -> datetime:
    """Helper per parsare date DD/MM/YYYY."""
    try:
        return datetime.strptime(s, "%d/%m/%Y")
    except ValueError:
        return datetime(2000, 1, 1)


def _calculate_age(birth_ddmmyyyy: str, now: datetime) -> int:
    b = _parse_ddmmyyyy(birth_ddmmyyyy).date()
    t = now.date()
    years = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
    return years


def _safe_get(obj, key, default=None):
    """Helper universale per proprietà Oggetti o chiavi Dizionari."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _fmt_consents_block(payload: RegistrationPayload) -> str:
    legal = _safe_get(payload, "legal")
    privacy = _safe_get(legal, "privacy")
    informed = _safe_get(legal, "informed_consent")
    resp = _safe_get(legal, "responsibility")
    tess = _safe_get(legal, "tesseramento")
    photo = _safe_get(legal, "photo")
    newsletter = _safe_get(legal, "newsletter")

    return "\n".join([
        f"Lingua: {_safe_get(payload, 'language')}",
        f"Privacy: {'SI' if privacy else 'NO'}",
        f"Consenso Inf.: {'SI' if informed else 'NO'}",
        f"Responsabilità: {'SI' if resp else 'NO'}",
        f"Tesseramento: {'SI' if tess else 'NO'}",
        f"Foto: {'SI' if photo else 'NO'}",
        f"Newsletter: {'SI' if newsletter else 'NO'}",
    ])


def _fmt_person_block(p) -> str:
    if not p:
        return ""
    
    nome = _safe_get(p, "nome", "")
    cognome = _safe_get(p, "cognome", "")
    nascita = _safe_get(p, "data_nascita", "")
    
    lines = [
        f"Nome: {nome}",
        f"Cognome: {cognome}",
        f"Nascita: {nascita}",
    ]
    
    cittadinanza = _safe_get(p, "cittadinanza_scelta")
    
    if cittadinanza == "ITALIANA":
        cf = _safe_get(p, "codice_fiscale") or _safe_get(_safe_get(p, "italian"), "codice_fiscale")
        if cf: lines.append(f"CF: {cf}")
            
    doc_type = _safe_get(p, "tipo_documento")
    doc_num = _safe_get(p, "numero_documento")
    
    if doc_type: lines.append(f"Doc: {doc_type}")
    if doc_num: lines.append(f"Num: {doc_num}")

    return "\n".join(lines)


def _fmt_full_participant_block(payload: RegistrationPayload, age: int) -> str:
    p = _safe_get(payload, "participant")
    base_info = _fmt_person_block(p)
    
    contact = _safe_get(payload, "contact")
    email = _safe_get(contact, "email")
    tel = _safe_get(contact, "telefono")

    contacts = []
    if email: contacts.append(f"Email: {email}")
    if tel: contacts.append(f"Tel: {tel}")
        
    consents = _fmt_consents_block(payload)
    
    return f"{base_info}\nEtà: {age}\n" + "\n".join(contacts) + "\n\n=== CONSENSI ===\n" + consents


@dataclass(frozen=True)
class SubmitResult:
    registration_id: str
    timestamp_iso: str
    pdf_filename: str
    emailed_to: str | None


class RegistrationService:
    def __init__(self):
        tz = os.getenv("APP_TZ", "Europe/Rome")
        self.tz = ZoneInfo(tz)
        
        storage_dir = os.getenv("REGISTRATION_STORAGE_DIR", os.path.join("storage", "registrations"))
        self.storage = StorageService(storage_dir)
        
        self.pdf = PdfService(legal_text=os.getenv("LEGAL_TEXT", None))
        self.email = EmailService()

    def get_registration_details(self, registration_id: str) -> dict:
        if not self.storage.exists(registration_id):
            raise FileNotFoundError("Registrazione non trovata")
        
        paths = self.storage.create_registration_dir(registration_id)
        data = self.storage.load_json(paths.json_path)
        if not data:
            raise ValueError("Dati registrazione corrotti o vuoti")
        
        audit_logs = self.storage.load_json(paths.audit_path) or []
        data["audit_log"] = audit_logs

        return data

    def submit(self, payload: RegistrationPayload, registration_id: str | None = None) -> SubmitResult:
        now = datetime.now(self.tz)
        
        p = _safe_get(payload, "participant")
        data_nascita = _safe_get(p, "data_nascita", "01/01/2000")
        
        age = _calculate_age(data_nascita, now)
        is_minor = age < 18
        
        guardian = _safe_get(payload, "guardian")
    
        if is_minor and not guardian:
            raise ValueError("Partecipante minorenne: dati tutore mancanti.")

        # LOGICA UPDATE vs CREATE
        is_update = False
        if registration_id:
            if not self.storage.exists(registration_id):
                raise FileNotFoundError(f"Impossibile aggiornare: ID {registration_id} non esiste.")
            # ARCHIVIAZIONE VERSIONE PRECEDENTE (Snapshot)
            self.storage.archive_current_version(registration_id)
            is_update = True
        else:
            registration_id = str(uuid.uuid4())

        paths = self.storage.create_registration_dir(registration_id)

        # 1. SALVATAGGIO FIRMA GRAFICA (Immagine)
        sig_base64 = _safe_get(payload, "signature_base64", "")
        signature_png = self.pdf.decode_signature_png(sig_base64)
        self.storage.save_bytes(paths.signature_path, signature_png)

        # 2. SALVATAGGIO FIRMA BIOMETRICA (Vettoriale FEA) - NUOVO
        # Estraiamo i dati grezzi dal payload
        sig_bio_str = _safe_get(payload, "signature_biometrics")
        if sig_bio_str:
            try:
                # Se è una stringa JSON, proviamo a parsare per validare, poi salviamo
                if isinstance(sig_bio_str, str):
                    bio_data = json.loads(sig_bio_str)
                    self.storage.save_json(paths.biometrics_path, bio_data)
                else:
                    # Se è già oggetto
                    self.storage.save_json(paths.biometrics_path, sig_bio_str)
            except Exception as e:
                print(f"Errore salvataggio biometrici: {e}")
                # Non blocchiamo il flusso, ma logghiamo
                self.storage.append_audit_log(registration_id, "BIO_ERROR", str(e))

        # 3. GENERAZIONE PDF
        participant_block = _fmt_full_participant_block(payload, age)
        guardian_block = _fmt_person_block(guardian) if is_minor and guardian else None
        consents_block = _fmt_consents_block(payload)
        signature_label = "Firma genitore/tutore" if is_minor else "Firma partecipante"

        pdf_result = self.pdf.generate(
            registration_id=registration_id,
            timestamp=now,
            participant_block=participant_block,
            guardian_block=guardian_block,
            consents_block=consents_block, 
            signature_png_bytes=signature_png,
            signature_label=signature_label,
        )
        self.storage.save_bytes(paths.pdf_path, pdf_result.pdf_bytes)

        # 4. SALVATAGGIO DATI JSON
        if hasattr(payload, 'model_dump'):
            payload_dict = payload.model_dump()
        else:
            payload_dict = dict(payload)

        payload_dict.update({
            "registration_id": registration_id,
            "timestamp_iso": now.isoformat(),
            "computed_age": age,
            "is_minor": is_minor,
            "locked": True
        })
        self.storage.save_json(paths.json_path, payload_dict)

        # 5. AUDIT LOG
        action_type = "UPDATE" if is_update else "CREATE"
        details = "Preferenze aggiornate" if is_update else "Nuova registrazione"
        self.storage.append_audit_log(registration_id, action_type, details)

        # 6. INVIO EMAIL
        emailed_to = None
        contact = _safe_get(payload, "contact")
        recipient = _safe_get(contact, "email")
        
        if recipient:
            try:
                subject_text = "Rafting Republic - Registrazione Aggiornata" if is_update else "Rafting Republic - Registrazione"
                body_text = "In allegato il documento aggiornato." if is_update else "In allegato il documento firmato."
                
                self.email.send_pdf(
                    to_email=str(recipient),
                    subject=subject_text,
                    body=body_text,
                    pdf_bytes=pdf_result.pdf_bytes,
                    filename=pdf_result.filename,
                )
                emailed_to = str(recipient)
                self.storage.append_audit_log(registration_id, "EMAIL_SENT", f"To: {emailed_to}")
            except Exception as e:
                self.storage.append_audit_log(registration_id, "EMAIL_ERROR", str(e))

        return SubmitResult(
            registration_id=registration_id,
            timestamp_iso=now.isoformat(),
            pdf_filename=pdf_result.filename,
            emailed_to=emailed_to,
        )

    def list_registrations(self, limit: int = 200, offset: int = 0, query: str | None = None) -> list[dict]:
        root = self.storage.storage_dir
        if not os.path.exists(root):
            return []

        q = (query or "").strip().lower()
        items = []

        try:
            entries = os.listdir(root)
        except OSError:
            return []

        for entry in entries:
            reg_dir = os.path.join(root, entry)
            if not os.path.isdir(reg_dir):
                continue
            
            payload_path = os.path.join(reg_dir, "payload.json")
            data = self.storage.load_json(payload_path)
            
            if not data:
                continue

            p = _safe_get(data, "participant", {})
            contact = _safe_get(data, "contact", {})
            
            reg_id = _safe_get(data, "registration_id", entry)
            nome = _safe_get(p, "nome", "")
            cognome = _safe_get(p, "cognome", "")
            email = _safe_get(contact, "email", "")
            
            searchable_text = f"{reg_id} {nome} {cognome} {email}".lower()
            if q and q not in searchable_text:
                continue

            items.append({
                "registration_id": reg_id,
                "timestamp_iso": _safe_get(data, "timestamp_iso"),
                "participant_nome": nome,
                "participant_cognome": cognome,
                "email": email,
                "is_minor": _safe_get(data, "is_minor", False),
                "locked": _safe_get(data, "locked", False),
            })

        items.sort(key=lambda x: x.get("timestamp_iso") or "", reverse=True)
        return items[offset : offset + limit]

    def set_locked(self, registration_id: str, locked: bool) -> dict:
        paths = self.storage.create_registration_dir(registration_id)
        data = self.storage.load_json(paths.json_path)
        
        if not data:
            raise FileNotFoundError("Registrazione non trovata")
        
        data["locked"] = locked
        self.storage.save_json(paths.json_path, data)
        
        self.storage.append_audit_log(registration_id, "LOCK_CHANGE", f"Locked: {locked}")
        
        return {"registration_id": registration_id, "locked": locked}

    def find_pdf_path(self, registration_id: str) -> str:
        paths = self.storage.create_registration_dir(registration_id)
        if os.path.exists(paths.pdf_path):
            return paths.pdf_path
        raise FileNotFoundError("PDF non trovato")