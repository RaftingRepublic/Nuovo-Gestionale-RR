from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


@dataclass(frozen=True)
class PdfResult:
    filename: str
    pdf_bytes: bytes


class PdfService:
    def __init__(self, legal_text: Optional[str] = None):
        """
        Inizializza il servizio PDF.
        :param legal_text: Testo legale opzionale da includere (non ancora utilizzato nel layout, ma predisposto).
        """
        self.legal_text = legal_text

    def decode_signature_png(self, signature_base64: str) -> bytes:
        """
        Accetta sia base64 puro sia dataURL: data:image/png;base64,...
        """
        s = signature_base64.strip()
        m = re.match(r"^data:image\/png;base64,(.*)$", s)
        if m:
            s = m.group(1)
        return base64.b64decode(s)

    def generate(
        self,
        registration_id: str,
        timestamp: datetime,
        participant_block: str,
        guardian_block: Optional[str],
        consents_block: str,
        signature_png_bytes: bytes,
        signature_label: str,
    ) -> PdfResult:
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4

        y = h - 20 * mm
        c.setFont("Helvetica-Bold", 16)
        c.drawString(20 * mm, y, "Rafting Republic - Registrazione")
        y -= 8 * mm

        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, f"ID: {registration_id}")
        y -= 5 * mm
        c.drawString(20 * mm, y, f"Data/Ora: {timestamp.isoformat()}")
        y -= 10 * mm

        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, y, "Dati partecipante")
        y -= 6 * mm

        c.setFont("Helvetica", 10)
        for line in participant_block.splitlines():
            c.drawString(20 * mm, y, line[:120])
            y -= 4.5 * mm

        if guardian_block:
            y -= 4 * mm
            c.setFont("Helvetica-Bold", 12)
            c.drawString(20 * mm, y, "Dati genitore/tutore")
            y -= 6 * mm

            c.setFont("Helvetica", 10)
            for line in guardian_block.splitlines():
                c.drawString(20 * mm, y, line[:120])
                y -= 4.5 * mm

        y -= 4 * mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, y, "Consensi")
        y -= 6 * mm

        c.setFont("Helvetica", 10)
        for line in consents_block.splitlines():
            c.drawString(20 * mm, y, line[:120])
            y -= 4.5 * mm

        y -= 6 * mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, y, signature_label)
        y -= 6 * mm

        # firma
        try:
            img = ImageReader(BytesIO(signature_png_bytes))
            c.rect(20 * mm, y - 30 * mm, 80 * mm, 30 * mm)
            c.drawImage(img, 20 * mm, y - 30 * mm, width=80 * mm, height=30 * mm, preserveAspectRatio=True, mask='auto')
        except Exception:
            # Fallback se l'immagine non è valida
            c.drawString(20 * mm, y - 10 * mm, "[Firma non valida]")

        c.showPage()
        c.save()

        pdf_bytes = buf.getvalue()
        filename = f"registrazione_{registration_id}.pdf"
        return PdfResult(filename=filename, pdf_bytes=pdf_bytes)