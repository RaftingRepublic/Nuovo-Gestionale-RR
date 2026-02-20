"""
Azure Document Intelligence – ID Document Scanner
==================================================
Servizio per l'estrazione OCR di documenti d'identità tramite Azure AI.

* Usa il modello **prebuilt-idDocument** (CIE, Passaporti, Patenti, ecc.)
* Lazy-loading del client (Cloud-Linux friendly, max 1 GB RAM)
* Output normalizzato nel formato atteso dal frontend Vue (registration-store.js)
* GDPR: nessuna immagine salvata su disco – tutto in-memory
"""

from __future__ import annotations

import gc
import os
import re
import traceback
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Carica .env (sicuro se già caricato)
load_dotenv()


# ---------------------------------------------------------------------------
#  LAZY-LOADED CLIENT (pattern imposto dall'infra Ergonet – max 1 GB RAM)
# ---------------------------------------------------------------------------
_client = None


def _get_client():
    """Restituisce (o crea) il DocumentIntelligenceClient singleton."""
    global _client
    if _client is not None:
        return _client

    endpoint = os.getenv("AZURE_DOCUMENT_ENDPOINT")
    key = os.getenv("AZURE_DOCUMENT_KEY")

    if not endpoint or not key:
        raise RuntimeError(
            "Variabili ambiente AZURE_DOCUMENT_ENDPOINT e/o AZURE_DOCUMENT_KEY mancanti. "
            "Configura il file backend/.env."
        )

    from azure.core.credentials import AzureKeyCredential
    from azure.ai.documentintelligence import DocumentIntelligenceClient

    _client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
    )
    return _client


# ---------------------------------------------------------------------------
#  HELPER – formattazione date
# ---------------------------------------------------------------------------
def _format_date(value: Any) -> str:
    """
    Converte un valore data Azure (stringa ISO, datetime, date) in GG/MM/AAAA.
    Se il valore è già nel formato giusto o non parsabile, lo restituisce "as-is".
    """
    if value is None:
        return ""

    # Se è un oggetto datetime / date
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")

    s: str = str(value).strip()
    if not s:
        return ""

    # Prova ISO 8601 (YYYY-MM-DD) – prendi solo i primi 10 caratteri
    # Nota: usiamo str() esplicito per evitare bug Pyre2 con slicing in Python 3.14
    date_part: str = s if len(s) <= 10 else str(s[0]) + str(s[1]) + str(s[2]) + str(s[3]) + str(s[4]) + str(s[5]) + str(s[6]) + str(s[7]) + str(s[8]) + str(s[9])  # noqa: E501
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_part, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue

    # Se è già GG/MM/AAAA accettalo
    if re.match(r"^\d{2}/\d{2}/\d{4}$", s):
        return s

    return s


# ---------------------------------------------------------------------------
#  MAPPATURA Azure → Frontend
# ---------------------------------------------------------------------------
# Il modello prebuilt-idDocument restituisce campi come:
#   FirstName, LastName, DateOfBirth, PlaceOfBirth, DocumentNumber,
#   DateOfExpiration, CountryRegion, Nationality, DocumentType (idCard, passport, driverLicense)
#
# Il frontend Vue si aspetta:
#   nome, cognome, data_nascita, comune_nascita, stato_nascita,
#   numero_documento, scadenza_documento, tipo_documento, codice_fiscale,
#   cittadinanza, source

_DOC_TYPE_MAP: Dict[str, str] = {
    "idCard":          "CIE",
    "driverLicense":   "PATENTE_IT",
    "passport":        "PASSAPORTO",
    "residencePermit": "PERMESSO_SOGGIORNO",
}


def _map_azure_doc_type(azure_type: Optional[str], hint: str = "AUTO") -> str:
    """Mappa il documentType Azure nel tipo documento del frontend."""
    if azure_type:
        mapped = _DOC_TYPE_MAP.get(azure_type)
        if mapped:
            return mapped
    # Fallback: usa l'hint che è arrivato dal frontend
    if hint and hint != "AUTO":
        return hint
    return "ALTRO"


def _safe_field(fields: dict, key: str, attr: str = "value_string") -> str:
    """Estrae in modo sicuro un campo dal dizionario dei fields Azure."""
    field = fields.get(key)
    if field is None:
        return ""

    # content è il testo grezzo rilevato
    # value_string è il testo normalizzato
    # value_date è la data parsata

    if attr == "value_date":
        val = getattr(field, "value_date", None) or getattr(field, "content", "")
    elif attr == "value_string":
        val = getattr(field, "value_string", None) or getattr(field, "content", "")
    else:
        val = getattr(field, attr, None) or getattr(field, "content", "")

    if val is None:
        return ""
    return str(val).strip()


# Pattern rigoroso Codice Fiscale italiano:
# 6 lettere + 2 cifre + 1 lettera + 2 cifre + 1 lettera + 3 cifre + 1 lettera (tot 16 char)
_CF_PATTERN = re.compile(r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b")


def _extract_codice_fiscale(fields: dict, raw_text: str = "") -> str:
    """
    Tenta di estrarre il Codice Fiscale italiano con 3 strategie:
      1. Campo PersonalNumber (usato da Azure per la CIE italiana)
      2. Campo MachineReadableZone (MRZ)
      3. Fallback: regex sull'intero testo OCR grezzo (result.content)
    """
    # --- Strategia 1: PersonalNumber ---
    cf = _safe_field(fields, "PersonalNumber")
    if cf and len(cf) == 16 and cf.isalnum():
        return cf.upper()

    # --- Strategia 2: MRZ ---
    mrz = _safe_field(fields, "MachineReadableZone")
    if mrz:
        match = _CF_PATTERN.search(mrz.upper())
        if match:
            return match.group(0)

    # --- Strategia 3: Regex su testo grezzo OCR ---
    if raw_text:
        match = _CF_PATTERN.search(raw_text.upper())
        if match:
            return match.group(0)

    return ""


# ---------------------------------------------------------------------------
#  Pattern per Numero Documento (fallback regex)
# ---------------------------------------------------------------------------
# CIE Italiana: 2 lettere + 5 cifre + 2 lettere (es. CA12345AB)
_CIE_NUM_PATTERN = re.compile(r"\b[A-Z]{2}\d{5}[A-Z]{2}\b")
# Passaporto/Patente generico: 9 caratteri alfanumerici (es. YA1234567)
_GENERIC_DOC_PATTERN = re.compile(r"\b[A-Z0-9]{9}\b")


def _extract_doc_number(fields: dict, raw_text: str = "", codice_fiscale: str = "") -> str:
    """
    Tenta di estrarre il Numero Documento con 3 strategie:
      1. Campo Azure DocumentNumber (standard)
      2. Regex CIE italiana sul testo grezzo (AA00000BB)
      3. Regex generica 9 char alfanumerici sul testo grezzo
    
    Esclude automaticamente il Codice Fiscale dai match per evitare falsi positivi.
    """
    # --- Strategia 1: Campo Azure ---
    doc_num = _safe_field(fields, "DocumentNumber")
    if doc_num:
        return doc_num.upper()

    if not raw_text:
        return ""

    text_upper = raw_text.upper()
    cf_upper = codice_fiscale.upper() if codice_fiscale else ""

    # --- Strategia 2: Regex CIE (AA00000BB) ---
    for m in _CIE_NUM_PATTERN.finditer(text_upper):
        candidate = m.group(0)
        if candidate != cf_upper:  # Non confondere col CF
            return candidate

    # --- Strategia 3: Regex generica 9 char ---
    for m in _GENERIC_DOC_PATTERN.finditer(text_upper):
        candidate = m.group(0)
        # Escludi CF, stringhe troppo "letterali" (solo lettere) e troppo numeriche
        if candidate != cf_upper and not candidate.isalpha() and not candidate.isdigit():
            return candidate

    return ""

# ---------------------------------------------------------------------------
#  Estrazione Comune di Residenza da Address
# ---------------------------------------------------------------------------
# Regex: CAP (5 cifre) + città + eventuale provincia tra parentesi
_CITY_FROM_ADDRESS_PATTERN = re.compile(
    r'\b\d{5}\s+([A-Z][A-Za-z\s/\-\']+?)(?:\s*\([A-Z]{2}\)|\s*$)',
    re.MULTILINE,
)


def _extract_city_from_address(fields: dict, raw_text: str = "") -> str:
    """
    Estrae il Comune di Residenza dal campo Address di Azure con 3 strategie:
      1. Oggetto strutturato (value_address.city / town)
      2. Regex sul testo dell'indirizzo (CAP + CITTA + PROV)
      3. Regex sul testo OCR grezzo (result.content)
    
    Restituisce il nome del comune in MAIUSCOLO, oppure stringa vuota.
    """
    # --- Strategia 1: Oggetto strutturato Azure ---
    address_field = fields.get("Address")
    if address_field:
        # SDK GA: value_address è un oggetto con proprietà city, state, etc.
        value_addr = getattr(address_field, "value_address", None)
        if value_addr:
            city = getattr(value_addr, "city", None) or getattr(value_addr, "town", None)
            if city and isinstance(city, str) and city.strip():
                return city.strip().upper()

        # Alcune versioni SDK restituiscono un dict
        value_dict = getattr(address_field, "value", None)
        if isinstance(value_dict, dict):
            city = value_dict.get("city") or value_dict.get("town") or value_dict.get("City")
            if city and isinstance(city, str) and city.strip():
                return city.strip().upper()

    # --- Strategia 2: Regex sul testo dell'indirizzo ---
    address_text = _safe_field(fields, "Address")
    if address_text:
        match = _CITY_FROM_ADDRESS_PATTERN.search(address_text.upper())
        if match:
            return match.group(1).strip()

    # --- Strategia 3: Regex sul testo OCR grezzo ---
    if raw_text:
        match = _CITY_FROM_ADDRESS_PATTERN.search(raw_text.upper())
        if match:
            return match.group(1).strip()

    return ""


# ---------------------------------------------------------------------------
#  FUNZIONE PRINCIPALE – analyze_with_azure()
# ---------------------------------------------------------------------------
def analyze_with_azure(
    image_bytes: bytes,
    doc_type_hint: str = "AUTO",
) -> Dict[str, Any]:
    """
    Invia l'immagine ad Azure Document Intelligence (prebuilt-idDocument)
    e restituisce un dizionario nel formato identico a quello atteso dal
    frontend Vue (registration-store.mapOcrToForm).

    Args:
        image_bytes: Bytes grezzi dell'immagine (JPEG/PNG).
        doc_type_hint: Hint dal frontend (CIE, PASSAPORTO, PATENTE_IT, ecc.)

    Returns:
        dict con chiavi: nome, cognome, data_nascita, comune_nascita,
        stato_nascita, numero_documento, scadenza_documento, tipo_documento,
        codice_fiscale, cittadinanza, source, _debug_info, etc.
    """
    result_dict: Dict[str, Any] = {
        "error": "Errore sconosciuto nell'analisi Azure.",
        "source": "AZURE_AI",
    }

    try:
        client = _get_client()

        # Invio all'API Azure (sintassi GA SDK 1.0+)
        poller = client.begin_analyze_document(
            model_id="prebuilt-idDocument",
            body=image_bytes,
            content_type="application/octet-stream",
        )
        result = poller.result()

        if not result.documents:
            result_dict = {
                "error": "Azure non ha rilevato alcun documento d'identità nell'immagine.",
                "source": "AZURE_AI",
            }
            return result_dict

        doc = result.documents[0]
        fields = doc.fields or {}

        # --- Estrazione campi principali ---
        first_name = _safe_field(fields, "FirstName")
        last_name = _safe_field(fields, "LastName")
        date_of_birth = _format_date(
            _safe_field(fields, "DateOfBirth", "value_date")
        )
        place_of_birth = _safe_field(fields, "PlaceOfBirth")
        date_of_expiry = _format_date(
            _safe_field(fields, "DateOfExpiration", "value_date")
        )
        country = _safe_field(fields, "CountryRegion")
        nationality = _safe_field(fields, "Nationality")
        address = _safe_field(fields, "Address")
        azure_doc_type = getattr(doc, "doc_type", None) or ""

        # Codice Fiscale (specifico CIE italiana)
        # Passa anche result.content come fallback per regex su testo grezzo
        raw_ocr_text: str = getattr(result, "content", "") or ""
        codice_fiscale = _extract_codice_fiscale(fields, raw_text=raw_ocr_text)

        # Numero Documento con fallback regex (necessario con image stitching)
        doc_number = _extract_doc_number(fields, raw_text=raw_ocr_text, codice_fiscale=codice_fiscale)

        # Comune di Residenza (da Address strutturato o regex)
        comune_residenza = _extract_city_from_address(fields, raw_text=raw_ocr_text)

        # Determinazione tipo documento
        tipo_doc = _map_azure_doc_type(azure_doc_type, doc_type_hint)

        # Determinazione nazionalità / stato nascita
        nat_upper = (nationality or country or "").upper().strip()
        is_italian = not nat_upper or nat_upper in (
            "ITA", "IT", "ITALIA", "ITALY", "ITALIANA",
        )
        stato_nascita = "ITALIA" if is_italian else nat_upper

        # Warning mismatch: il tipo rilevato è diverso dall'hint
        warning_mismatch = False
        if doc_type_hint and doc_type_hint != "AUTO" and tipo_doc != doc_type_hint:
            warning_mismatch = True

        # --- Composizione risposta nel formato FRONTEND ---
        result_dict = {
            "nome": first_name,
            "cognome": last_name,
            "data_nascita": date_of_birth,
            "comune_nascita": place_of_birth,
            "stato_nascita": stato_nascita,
            "stato_residenza": "ITALIA" if is_italian else "",
            "comune_residenza": comune_residenza,
            "codice_fiscale": codice_fiscale,
            "tipo_documento": tipo_doc,
            "numero_documento": doc_number,
            "scadenza_documento": date_of_expiry,
            "cittadinanza": nationality or country or "",
            "source": "AZURE_AI",
            "warning_mismatch": warning_mismatch,
            "_debug_info": {
                "azure_doc_type": azure_doc_type,
                "confidence": getattr(doc, "confidence", None),
                "fields_found": list(fields.keys()),
                "hint_received": doc_type_hint,
                "address_raw": address,
            },
        }

    except Exception as e:
        traceback.print_exc()
        result_dict = {
            "error": f"Errore Azure Document Intelligence: {str(e)}",
            "source": "AZURE_AI",
        }
    finally:
        # Libera memoria dopo ogni inferenza (vincolo Ergonet 1 GB)
        gc.collect()

    return result_dict
