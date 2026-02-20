from __future__ import annotations

import json
import os
import shutil
import time
import hashlib
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class RegistrationPaths:
    root: str
    json_path: str
    pdf_path: str
    signature_path: str
    biometrics_path: str # NUOVO
    audit_path: str
    history_dir: str

class StorageService:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def create_registration_dir(self, registration_id: str) -> RegistrationPaths:
        reg_dir = os.path.join(self.storage_dir, registration_id)
        if not os.path.exists(reg_dir):
            os.makedirs(reg_dir, exist_ok=True)
        
        return RegistrationPaths(
            root=reg_dir,
            json_path=os.path.join(reg_dir, "payload.json"),
            pdf_path=os.path.join(reg_dir, "signed.pdf"),
            signature_path=os.path.join(reg_dir, "signature.png"),
            biometrics_path=os.path.join(reg_dir, "biometrics.json"), # NUOVO
            audit_path=os.path.join(reg_dir, "audit.json"),
            history_dir=os.path.join(reg_dir, "history")
        )

    def exists(self, registration_id: str) -> bool:
        path = os.path.join(self.storage_dir, registration_id, "payload.json")
        return os.path.exists(path)

    def archive_current_version(self, registration_id: str) -> None:
        """
        Sposta i file correnti in una cartella history/v_{timestamp}.
        Include anche i dati biometrici se presenti.
        """
        paths = self.create_registration_dir(registration_id)
        if not os.path.exists(paths.json_path): return

        if not os.path.exists(paths.history_dir):
            os.makedirs(paths.history_dir, exist_ok=True)

        version_name = f"v_{int(time.time())}"
        version_dir = os.path.join(paths.history_dir, version_name)
        os.makedirs(version_dir, exist_ok=True)

        try:
            # Copia file standard
            if os.path.exists(paths.json_path):
                shutil.copy2(paths.json_path, os.path.join(version_dir, "payload.json"))
            if os.path.exists(paths.pdf_path):
                shutil.copy2(paths.pdf_path, os.path.join(version_dir, "signed.pdf"))
            if os.path.exists(paths.signature_path):
                shutil.copy2(paths.signature_path, os.path.join(version_dir, "signature.png"))
            
            # Copia file biometrico (NUOVO)
            if os.path.exists(paths.biometrics_path):
                shutil.copy2(paths.biometrics_path, os.path.join(version_dir, "biometrics.json"))
                
        except Exception as e:
            print(f"Errore archiviazione storico {registration_id}: {e}")

    def append_audit_log(self, registration_id: str, action: str, details: str = ""):
        paths = self.create_registration_dir(registration_id)
        
        previous_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        logs = []

        if os.path.exists(paths.audit_path):
            try:
                with open(paths.audit_path, "r", encoding="utf-8") as f:
                    logs = json.load(f)
                    if logs and isinstance(logs, list) and len(logs) > 0:
                        last_entry = logs[-1]
                        previous_hash = last_entry.get("hash", previous_hash)
            except Exception:
                logs = []

        entry = {
            "timestamp": time.time(),
            "iso_date": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "action": action,
            "details": details,
            "previous_hash": previous_hash
        }
        
        entry_string = json.dumps(entry, sort_keys=True)
        current_hash = hashlib.sha256(entry_string.encode("utf-8")).hexdigest()
        entry["hash"] = current_hash
        
        logs.append(entry)
        
        temp_path = f"{paths.audit_path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        
        os.replace(temp_path, paths.audit_path)

    def save_bytes(self, path: str, data: bytes):
        with open(path, "wb") as f:
            f.write(data)

    def save_json(self, path: str, data: dict):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_json(self, path: str) -> dict | None:
        if not os.path.exists(path): return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None