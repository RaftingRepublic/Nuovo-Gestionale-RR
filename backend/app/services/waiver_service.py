from __future__ import annotations

import base64
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Literal, Optional, Dict, Any

from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, model_validator

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
)
from reportlab.lib import colors

from .waiver_mailer import WaiverMailer


TZ_ROME = ZoneInfo("Europe/Rome")


def _parse_ddmmyyyy(value: str) -> date:
    # accetta "DD/MM/YYYY"
    dd, mm_, yyyy = value.strip().split("/")
    return date(int(yyyy), int(mm_), int(dd))


def _calc_age(birth: date, on: date) -> int:
    years = on.year - birth.year
    if (on.month, on.day) < (birth.month, birth.day):
        years -= 1
    return years


class PersonaItalia(BaseModel):
    cittadinanza: Literal["ITA"] = "ITA"

    nome: str
    cognome: str
    comune_nascita: str
    data_nascita: str  # DD/MM/YYYY
    comune_residenza: str
    codice_fiscale: str

    tipo_documento: str
    numero_documento: str
    scadenza_documento: str  # DD/MM/YYYY

    email: str
    telefono: str


class PersonaEstera(BaseModel):
    cittadinanza: Literal["NON_ITA"] = "NON_ITA"

    nome: str
    cognome: str
    stato_nascita: str
    data_nascita: str  # DD/MM/YYYY
    stato_residenza: str

    tipo_documento: str
    numero_documento: str
    scadenza_documento: str  # DD/MM/YYYY

    email: str
    telefono: str


Persona = PersonaItalia | PersonaEstera


class WaiverDraftRequest(BaseModel):
    # dati del minore SEMPRE presenti se stiamo facendo la pratica “minore”
    minore: Persona

    # richiesti SOLO se minore < 18 (validiamo server-side)
    genitore: Optional[Persona] = None

    # testo legale: in questa fase lo teniamo lato server, ma puoi anche passarlo dal client se vuoi.
    # qui lo lasciamo opzionale per poterlo aggiornare facilmente in futuro.
    waiver_title: str = "Modulo di scarico responsabilità / privacy / consenso informato"
    waiver_body: Optional[str] = None

    @model_validator(mode="after")
    def _validate_minor_guardian(self) -> "WaiverDraftRequest":
        today = datetime.now(TZ_ROME).date()
        dn = _parse_ddmmyyyy(self.minore.data_nascita)
        eta = _calc_age(dn, today)
        if eta < 18 and self.genitore is None:
            raise ValueError("Minore < 18: il campo 'genitore' è obbligatorio.")
        return self


class WaiverDraftResponse(BaseModel):
    waiver_id: str
    created_at_iso: str
    is_minor: bool
    draft_pdf_path: str  # path su server (per debug / log)
    draft_pdf_url: str   # endpoint per scaricarlo


class WaiverFinalizeRequest(BaseModel):
    # firma SOLO genitore/tutore (PNG base64). Obbligatoria se minore < 18.
    signature_png_base64: Optional[str] = None

    # opzionale: se vuoi mandare anche a un indirizzo specifico (altrimenti usiamo email genitore)
    send_to_email: Optional[str] = None


class WaiverFinalizeResponse(BaseModel):
    waiver_id: str
    finalized_at_iso: str
    final_pdf_path: str
    final_pdf_url: str
    emailed_to: Optional[str] = None


@dataclass(frozen=True)
class WaiverPaths:
    root: Path
    meta_json: Path
    draft_pdf: Path
    final_pdf: Path
    signature_png: Path


class WaiverService:
    """
    Storage 100% locale:
      backend/app/storage/waivers/<waiver_id>/
         meta.json
         draft.pdf
         final.pdf
         signature.png
    """

    def __init__(self, storage_root: Optional[Path] = None, mailer: Optional[WaiverMailer] = None):
        base = storage_root or (Path(__file__).resolve().parents[1] / "storage" / "waivers")
        self.storage_root = base
        self.storage_root.mkdir(parents=True, exist_ok=True)

        self.mailer = mailer or WaiverMailer.from_env()

    def _paths(self, waiver_id: str) -> WaiverPaths:
        root = self.storage_root / waiver_id
        root.mkdir(parents=True, exist_ok=True)
        return WaiverPaths(
            root=root,
            meta_json=root / "meta.json",
            draft_pdf=root / "draft.pdf",
            final_pdf=root / "final.pdf",
            signature_png=root / "signature.png",
        )

    def create_draft(self, req: WaiverDraftRequest, public_base_url: str) -> WaiverDraftResponse:
        waiver_id = str(uuid.uuid4())
        paths = self._paths(waiver_id)

        now = datetime.now(TZ_ROME)
        today = now.date()
        minore_eta = _calc_age(_parse_ddmmyyyy(req.minore.data_nascita), today)
        is_minor = minore_eta < 18

        # testo legale (placeholder “vero” ma breve: poi lo sostituisci con il testo ufficiale)
        waiver_body = req.waiver_body or (
            "DICHIARAZIONE:\n"
            "Il sottoscritto dichiara di aver ricevuto informativa privacy, di aver compreso i rischi "
            "connessi all'attività e di sollevare l'organizzazione da responsabilità nei limiti di legge. "
            "Conferma inoltre la veridicità dei dati inseriti.\n\n"
            "PRIVACY:\n"
            "Autorizzo il trattamento dei dati personali per finalità organizzative e di sicurezza.\n\n"
            "CONSENSO INFORMATO:\n"
            "Dichiaro di aver compreso natura e rischi dell'attività svolta."
        )

        meta: Dict[str, Any] = {
            "waiver_id": waiver_id,
            "created_at_iso": now.isoformat(),
            "is_minor": is_minor,
            "minore": req.minore.model_dump(),
            "genitore": req.genitore.model_dump() if req.genitore else None,
            "waiver_title": req.waiver_title,
            "waiver_body": waiver_body,
        }
        paths.meta_json.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        self._render_pdf(
            out_path=paths.draft_pdf,
            meta=meta,
            signature_path=None,  # draft: niente firma
        )

        return WaiverDraftResponse(
            waiver_id=waiver_id,
            created_at_iso=now.isoformat(),
            is_minor=is_minor,
            draft_pdf_path=str(paths.draft_pdf),
            draft_pdf_url=f"{public_base_url.rstrip('/')}/api/v1/waivers/{waiver_id}/pdf?which=draft",
        )

    def finalize(self, waiver_id: str, req: WaiverFinalizeRequest, public_base_url: str) -> WaiverFinalizeResponse:
        paths = self._paths(waiver_id)
        if not paths.meta_json.exists():
            raise FileNotFoundError("waiver_id non trovato")

        meta = json.loads(paths.meta_json.read_text(encoding="utf-8"))
        is_minor = bool(meta.get("is_minor"))

        # Firma SOLO genitore/tutore: obbligatoria se minore
        if is_minor:
            if not req.signature_png_base64:
                raise ValueError("Minore: la firma del genitore/tutore è obbligatoria (PNG base64).")
            self._save_signature_png(paths.signature_png, req.signature_png_base64)
            signature_path = paths.signature_png
        else:
            # se non è minore, NON chiediamo firma (come da tua richiesta “solo firma genitore”)
            signature_path = None

        finalized_at = datetime.now(TZ_ROME)
        meta["finalized_at_iso"] = finalized_at.isoformat()
        paths.meta_json.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        self._render_pdf(
            out_path=paths.final_pdf,
            meta=meta,
            signature_path=signature_path,
        )

        # invio email (se abilitato)
        emailed_to: Optional[str] = None
        if self.mailer.enabled:
            # preferenza: invia a req.send_to_email, altrimenti all’email genitore (se presente),
            # altrimenti all’email minore (caso adulto o edge).
            to_email = (
                (req.send_to_email or "").strip()
                or ((meta.get("genitore") or {}).get("email") or "").strip()
                or ((meta.get("minore") or {}).get("email") or "").strip()
            )
            if to_email:
                subject = f"Modulo firmato - {waiver_id}"
                body = "In allegato trovi il modulo compilato e firmato."
                self.mailer.send_pdf(to_email=to_email, subject=subject, body=body, pdf_path=paths.final_pdf)
                emailed_to = to_email

        return WaiverFinalizeResponse(
            waiver_id=waiver_id,
            finalized_at_iso=finalized_at.isoformat(),
            final_pdf_path=str(paths.final_pdf),
            final_pdf_url=f"{public_base_url.rstrip('/')}/api/v1/waivers/{waiver_id}/pdf?which=final",
            emailed_to=emailed_to,
        )

    def _save_signature_png(self, out_path: Path, signature_b64: str) -> None:
        # accetta sia base64 “puro” che data URL "data:image/png;base64,..."
        raw = signature_b64.strip()
        if raw.startswith("data:"):
            raw = raw.split(",", 1)[-1]
        data = base64.b64decode(raw)
        out_path.write_bytes(data)

    def _render_pdf(self, out_path: Path, meta: Dict[str, Any], signature_path: Optional[Path]) -> None:
        styles = getSampleStyleSheet()
        style_h = styles["Heading1"]
        style_b = styles["BodyText"]

        doc = SimpleDocTemplate(
            str(out_path),
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            title="Waiver",
            author="Rafting Registration System",
        )

        elems = []

        title = meta.get("waiver_title", "Modulo")
        elems.append(Paragraph(title, style_h))
        elems.append(Spacer(1, 6 * mm))

        created_at_iso = meta.get("created_at_iso", "")
        finalized_at_iso = meta.get("finalized_at_iso", "")
        ts_line = f"Creato il: {created_at_iso}"
        if finalized_at_iso:
            ts_line += f" — Firmato il: {finalized_at_iso}"
        elems.append(Paragraph(ts_line, style_b))
        elems.append(Spacer(1, 6 * mm))

        # Dati minore
        elems.append(Paragraph("<b>Dati partecipante (minore)</b>", styles["Heading3"]))
        elems.append(Spacer(1, 2 * mm))
        elems.extend(self._person_table(meta.get("minore") or {}))
        elems.append(Spacer(1, 6 * mm))

        # Dati genitore/tutore (se presenti)
        if meta.get("genitore"):
            elems.append(Paragraph("<b>Dati genitore/tutore</b>", styles["Heading3"]))
            elems.append(Spacer(1, 2 * mm))
            elems.extend(self._person_table(meta.get("genitore") or {}))
            elems.append(Spacer(1, 6 * mm))

        # Testo legale
        body = meta.get("waiver_body", "")
        for block in body.split("\n\n"):
            block = block.strip()
            if not block:
                continue
            safe = block.replace("\n", "<br/>")
            elems.append(Paragraph(safe, style_b))
            elems.append(Spacer(1, 4 * mm))

        elems.append(Spacer(1, 8 * mm))
        elems.append(Paragraph("<b>Firma genitore/tutore</b>", styles["Heading3"]))
        elems.append(Spacer(1, 2 * mm))

        # Area firma
        if signature_path and signature_path.exists():
            try:
                img = RLImage(str(signature_path), width=60 * mm, height=20 * mm)
            except Exception:
                img = Paragraph("(Firma non leggibile)", style_b)
        else:
            img = Paragraph("__________________________________________", style_b)

        sign_table = Table(
            [[img, Paragraph("Data: ____________________", style_b)]],
            colWidths=[90 * mm, 60 * mm],
        )
        sign_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOX", (0, 0), (0, 0), 0.5, colors.black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elems.append(sign_table)

        doc.build(elems)

    def _person_table(self, p: Dict[str, Any]) -> list:
        styles = getSampleStyleSheet()
        style_b = styles["BodyText"]

        # Normalizziamo campi ITA vs NON_ITA
        rows = []
        def add(label: str, key: str):
            val = (p.get(key) or "").strip() if isinstance(p.get(key), str) else (p.get(key) or "")
            if val:
                rows.append([Paragraph(f"<b>{label}</b>", style_b), Paragraph(str(val), style_b)])

        add("Nome", "nome")
        add("Cognome", "cognome")
        add("Cittadinanza", "cittadinanza")

        if p.get("cittadinanza") == "ITA":
            add("Comune di nascita", "comune_nascita")
            add("Comune di residenza", "comune_residenza")
            add("Codice fiscale", "codice_fiscale")
        else:
            add("Stato di nascita", "stato_nascita")
            add("Stato di residenza", "stato_residenza")

        add("Data di nascita", "data_nascita")
        add("Tipo documento", "tipo_documento")
        add("Numero documento", "numero_documento")
        add("Scadenza documento", "scadenza_documento")
        add("Email", "email")
        add("Telefono", "telefono")

        table = Table(rows, colWidths=[50 * mm, 120 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        return [table]
