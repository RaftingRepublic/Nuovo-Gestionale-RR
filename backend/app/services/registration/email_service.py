from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Optional


class EmailService:
    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASS", "")
        self.use_starttls = os.getenv("SMTP_USE_STARTTLS", "true").lower() in ("1", "true", "yes")
        self.mail_from = os.getenv("SMTP_FROM", self.user)

    def is_configured(self) -> bool:
        return bool(self.host and self.port and self.mail_from)

    def send_pdf(self, to_email: str, subject: str, body: str, pdf_bytes: bytes, filename: str):
        if not self.is_configured():
            return

        msg = EmailMessage()
        msg["From"] = self.mail_from
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)

        with smtplib.SMTP(self.host, self.port, timeout=15) as smtp:
            if self.use_starttls:
                smtp.starttls()
            if self.user and self.password:
                smtp.login(self.user, self.password)
            smtp.send_message(msg)
