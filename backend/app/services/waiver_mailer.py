from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class WaiverMailer:
    enabled: bool
    host: str
    port: int
    username: Optional[str]
    password: Optional[str]
    use_tls: bool
    mail_from: str

    @staticmethod
    def from_env() -> "WaiverMailer":
        enabled = os.getenv("SMTP_ENABLED", "false").lower() == "true"
        host = os.getenv("SMTP_HOST", "localhost")
        port = int(os.getenv("SMTP_PORT", "25"))
        username = os.getenv("SMTP_USER") or None
        password = os.getenv("SMTP_PASS") or None
        use_tls = os.getenv("SMTP_TLS", "false").lower() == "true"
        mail_from = os.getenv("SMTP_FROM", "noreply@localhost")
        return WaiverMailer(
            enabled=enabled,
            host=host,
            port=port,
            username=username,
            password=password,
            use_tls=use_tls,
            mail_from=mail_from,
        )

    def send_pdf(self, to_email: str, subject: str, body: str, pdf_path: Path) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.mail_from
        msg["To"] = to_email
        msg.set_content(body)

        data = pdf_path.read_bytes()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="pdf",
            filename=pdf_path.name,
        )

        with smtplib.SMTP(self.host, self.port, timeout=30) as smtp:
            if self.use_tls:
                smtp.starttls()
            if self.username and self.password:
                smtp.login(self.username, self.password)
            smtp.send_message(msg)
