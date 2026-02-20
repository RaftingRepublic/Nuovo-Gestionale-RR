import os
import json
import hashlib
import shutil
from datetime import datetime, date
from pathlib import Path

# Configurazione
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage" / "registrations"
FREEZE_DIR = BASE_DIR / "storage" / "daily_freezes"

def calculate_file_hash(filepath):
    """Calcola SHA-256 di un file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Legge il file a blocchi per non saturare la RAM
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def freeze_day(target_date_str=None):
    """
    Scansiona tutte le registrazioni di una data specifica.
    Calcola gli hash e genera un report di integrità.
    """
    # Se non specificata, usa la data di oggi
    if not target_date_str:
        target_date_str = date.today().isoformat() # YYYY-MM-DD

    print(f"❄️  AVVIO FREEZE GIORNALIERO: {target_date_str}")
    
    if not STORAGE_DIR.exists():
        print("❌ Nessuna cartella storage trovata.")
        return

    # 1. Cerca le registrazioni del giorno
    daily_manifest = {
        "freeze_date": target_date_str,
        "generated_at": datetime.now().isoformat(),
        "registrations": [],
        "total_files": 0,
        "cumulative_hash": ""
    }

    print("🔍 Scansione cartelle...")
    
    all_hashes = []

    for entry in os.listdir(STORAGE_DIR):
        reg_dir = STORAGE_DIR / entry
        json_path = reg_dir / "payload.json"
        
        if not json_path.exists():
            continue

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Estrai la data dal timestamp ISO
            ts = data.get("timestamp_iso", "")
            if not ts.startswith(target_date_str):
                continue # Non è di oggi

            # Trovata registrazione del giorno!
            print(f"   + Processo ID: {entry}")
            
            reg_entry = {
                "id": entry,
                "files": {}
            }

            # Hash dei file critici
            for filename in ["signed.pdf", "audit.json", "biometrics.json", "payload.json"]:
                fpath = reg_dir / filename
                if fpath.exists():
                    fhash = calculate_file_hash(fpath)
                    reg_entry["files"][filename] = fhash
                    all_hashes.append(fhash)
            
            daily_manifest["registrations"].append(reg_entry)
            daily_manifest["total_files"] += len(reg_entry["files"])

        except Exception as e:
            print(f"⚠️ Errore lettura {entry}: {e}")

    if daily_manifest["total_files"] == 0:
        print(f"⚠️ Nessuna registrazione trovata per il {target_date_str}")
        return

    # 2. Calcolo Super-Hash (Hash di tutti gli hash)
    # Ordiniamo per garantire riproducibilità
    all_hashes.sort()
    mega_string = "".join(all_hashes)
    super_hash = hashlib.sha256(mega_string.encode('utf-8')).hexdigest()
    
    daily_manifest["cumulative_hash"] = super_hash

    # 3. Salvataggio Report
    FREEZE_DIR.mkdir(parents=True, exist_ok=True)
    report_filename = f"freeze_report_{target_date_str}.json"
    report_path = FREEZE_DIR / report_filename

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(daily_manifest, f, indent=2)

    print("\n" + "="*60)
    print(f"✅ GIORNATA CRISTALLIZZATA CORRETTAMENTE")
    print(f"📄 Report salvato in: {report_path}")
    print(f"🔐 SUPER-HASH (Digital Fingerprint):")
    print(f"   {super_hash}")
    print("="*60)
    print("\n💡 CONSIGLIO LEGALE:")
    print("Invia questo file JSON (o il Super-Hash) via PEC all'indirizzo dell'azienda")
    print("per ottenere una Data Certa opponibile a terzi su tutto il lotto.")

if __name__ == "__main__":
    # Puoi passare una data specifica YYYY-MM-DD come argomento, o usa oggi
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else None
    freeze_day(target)