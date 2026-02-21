from __future__ import annotations

import base64
import re
import textwrap
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor


# ─── TESTO LEGALE BOILERPLATE ───────────────────────────────────
LEGAL_BOILERPLATE = (
    "Il/La sottoscritto/a dichiara di essere in buone condizioni di salute psico-fisica, "
    "di saper nuotare, di non essere sotto l'effetto di alcol o sostanze stupefacenti "
    "e di essere consapevole dei rischi inerenti alla pratica sportiva fluviale. "
    "Dichiara altresì di aver ricevuto e compreso le istruzioni di sicurezza impartite "
    "dalle guide e di impegnarsi a rispettarle durante tutta la durata dell'attività.\n\n"
    "Ai sensi degli artt. 1341 e 1342 del Codice Civile, il/la sottoscritto/a esonera "
    "l'organizzazione Rafting Republic, le guide, gli istruttori e i collaboratori da ogni responsabilità "
    "per danni derivanti dalla pratica dell'attività sportiva, salvo i casi di dolo o colpa grave.\n\n"
    "Autorizza il trattamento dei propri dati personali ai sensi del Regolamento UE 2016/679 (GDPR) "
    "e del D.Lgs. 196/2003 per le finalità strettamente connesse all'erogazione del servizio, "
    "alla gestione assicurativa e al tesseramento FIRAFT."
)


@dataclass(frozen=True)
class PdfResult:
    filename: str
    pdf_bytes: bytes


class PdfService:
    # Colore brand
    BRAND_COLOR = HexColor("#1565C0")  # Blu Rafting Republic

    def __init__(self, legal_text: Optional[str] = None):
        """
        Inizializza il servizio PDF.
        :param legal_text: Testo legale personalizzato (sovrascrive il boilerplate).
        """
        self.legal_text = legal_text or LEGAL_BOILERPLATE

    def decode_signature_png(self, signature_base64: str) -> bytes:
        """
        Accetta sia base64 puro sia dataURL: data:image/png;base64,...
        """
        s = signature_base64.strip()
        m = re.match(r"^data:image\/png;base64,(.*)$", s)
        if m:
            s = m.group(1)
        return base64.b64decode(s)

    def _draw_wrapped_text(self, c: canvas.Canvas, text: str, x: float, y: float,
                           max_width: float, font: str = "Helvetica",
                           font_size: int = 9, leading: float = 4 * mm) -> float:
        """Disegna testo con word-wrap. Ritorna la nuova posizione Y."""
        c.setFont(font, font_size)
        # Calcola il numero approssimativo di caratteri per riga
        char_width = c.stringWidth("x", font, font_size)
        chars_per_line = int(max_width / char_width) if char_width > 0 else 80

        for paragraph in text.split("\n"):
            if not paragraph.strip():
                y -= leading * 0.6
                continue
            wrapped = textwrap.wrap(paragraph, width=chars_per_line)
            for line in wrapped:
                if y < 25 * mm:
                    c.showPage()
                    y = A4[1] - 20 * mm
                    c.setFont(font, font_size)
                c.drawString(x, y, line)
                y -= leading
        return y

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
        margin = 20 * mm
        content_width = w - 2 * margin

        # ═══════════════════════════════════════════════════
        # HEADER — Riga blu con titolo centrato
        # ═══════════════════════════════════════════════════
        y = h - 15 * mm
        c.setFillColor(self.BRAND_COLOR)
        c.rect(0, y - 2 * mm, w, 12 * mm, fill=True, stroke=False)
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", 13)
        title = "MODULO DI ASSUNZIONE RISCHIO E SCARICO RESPONSABILITÀ"
        c.drawCentredString(w / 2, y + 1 * mm, title)

        # Sub-header
        c.setFillColor(HexColor("#333333"))
        y -= 12 * mm
        c.setFont("Helvetica", 8)
        c.drawCentredString(w / 2, y, f"Rafting Republic — ID: {registration_id[:18]}...")
        c.drawRightString(w - margin, y, f"Data: {timestamp.strftime('%d/%m/%Y %H:%M')}")

        y -= 10 * mm

        # ═══════════════════════════════════════════════════
        # SEZIONE 1 — DATI PARTECIPANTE
        # ═══════════════════════════════════════════════════
        c.setFillColor(self.BRAND_COLOR)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "▸ DATI PARTECIPANTE")
        y -= 2 * mm
        c.setStrokeColor(self.BRAND_COLOR)
        c.setLineWidth(0.5)
        c.line(margin, y, w - margin, y)
        y -= 5 * mm

        c.setFillColor(HexColor("#222222"))
        y = self._draw_wrapped_text(c, participant_block, margin, y, content_width)
        y -= 4 * mm

        # ═══════════════════════════════════════════════════
        # SEZIONE 2 — DATI TUTORE (solo minorenni)
        # ═══════════════════════════════════════════════════
        if guardian_block:
            c.setFillColor(self.BRAND_COLOR)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(margin, y, "▸ DATI GENITORE / TUTORE")
            y -= 2 * mm
            c.line(margin, y, w - margin, y)
            y -= 5 * mm
            c.setFillColor(HexColor("#222222"))
            y = self._draw_wrapped_text(c, guardian_block, margin, y, content_width)
            y -= 4 * mm

        # ═══════════════════════════════════════════════════
        # SEZIONE 3 — CLAUSOLA LEGALE
        # ═══════════════════════════════════════════════════
        c.setFillColor(self.BRAND_COLOR)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "▸ CLAUSOLA DI ASSUNZIONE RISCHIO")
        y -= 2 * mm
        c.line(margin, y, w - margin, y)
        y -= 5 * mm

        c.setFillColor(HexColor("#333333"))
        y = self._draw_wrapped_text(c, self.legal_text, margin, y, content_width,
                                     font="Helvetica", font_size=8, leading=3.5 * mm)
        y -= 6 * mm

        # ═══════════════════════════════════════════════════
        # SEZIONE 4 — CONSENSI
        # ═══════════════════════════════════════════════════
        c.setFillColor(self.BRAND_COLOR)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "▸ CONSENSI")
        y -= 2 * mm
        c.line(margin, y, w - margin, y)
        y -= 5 * mm

        c.setFillColor(HexColor("#222222"))
        y = self._draw_wrapped_text(c, consents_block, margin, y, content_width,
                                     font="Helvetica", font_size=9)
        y -= 8 * mm

        # ═══════════════════════════════════════════════════
        # SEZIONE 5 — FIRMA
        # ═══════════════════════════════════════════════════
        # Verifica che ci sia abbastanza spazio; altrimenti nuova pagina
        if y < 55 * mm:
            c.showPage()
            y = h - 25 * mm

        c.setFillColor(self.BRAND_COLOR)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, f"▸ {signature_label.upper()}")
        y -= 2 * mm
        c.line(margin, y, w - margin, y)
        y -= 5 * mm

        # Box firma posizionato a destra
        sig_width = 70 * mm
        sig_height = 25 * mm
        sig_x = w - margin - sig_width  # Allineato a destra

        # Etichetta luogo/data a sinistra
        c.setFillColor(HexColor("#555555"))
        c.setFont("Helvetica", 9)
        c.drawString(margin, y - 5 * mm, f"Luogo e data: Trentino, {timestamp.strftime('%d/%m/%Y')}")
        c.drawString(margin, y - 10 * mm, f"Ora: {timestamp.strftime('%H:%M:%S')}")

        # Rettangolo firma + immagine
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.setLineWidth(0.8)
        c.rect(sig_x, y - sig_height, sig_width, sig_height, stroke=True, fill=False)

        try:
            img = ImageReader(BytesIO(signature_png_bytes))
            c.drawImage(img, sig_x + 2 * mm, y - sig_height + 2 * mm,
                        width=sig_width - 4 * mm, height=sig_height - 4 * mm,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            c.setFillColor(HexColor("#CC0000"))
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(sig_x + 5 * mm, y - 15 * mm, "[Firma non leggibile]")

        # Etichetta sotto la firma
        c.setFillColor(HexColor("#999999"))
        c.setFont("Helvetica", 7)
        c.drawCentredString(sig_x + sig_width / 2, y - sig_height - 4 * mm,
                             signature_label)

        # ═══════════════════════════════════════════════════
        # FOOTER
        # ═══════════════════════════════════════════════════
        c.setFillColor(HexColor("#BBBBBB"))
        c.setFont("Helvetica", 6)
        c.drawCentredString(w / 2, 10 * mm,
                             f"Documento generato automaticamente — Rafting Republic © {timestamp.year} — Non valido senza firma")

        c.showPage()
        c.save()

        pdf_bytes = buf.getvalue()
        filename = f"registrazione_{registration_id}.pdf"
        return PdfResult(filename=filename, pdf_bytes=pdf_bytes)