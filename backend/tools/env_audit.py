import os
import sys
import pkg_resources
import platform

def check_asset(path, description):
    if os.path.exists(path):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"✅ FILE TROVATO: {description}")
        print(f"   Percorso: {path}")
        print(f"   Dimensione: {size_mb:.2f} MB")
        return True
    else:
        print(f"❌ FILE MANCANTE: {description}")
        print(f"   Percorso atteso: {path}")
        print("   ⚠️ QUESTO FILE DEVE ESSERE INCLUSO IN GIT!")
        return False

def check_package(package_name, expected_version=None):
    try:
        version = pkg_resources.get_distribution(package_name).version
        status = "✅"
        note = ""
        if expected_version:
            if version == expected_version:
                note = "(Corretto)"
            else:
                status = "⚠️"
                note = f"(Atteso: {expected_version} - RISCHIO!)"
        
        print(f"{status} {package_name.ljust(20)} : {version} {note}")
    except pkg_resources.DistributionNotFound:
        print(f"❌ {package_name.ljust(20)} : NON INSTALLATO")

print("="*60)
print(f"🔍 AUDIT AMBIENTE - {platform.system()} - Python {sys.version.split()[0]}")
print("="*60)

# 1. VERIFICA LIBRERIE CRITICHE
print("\n--- 1. VERIFICA LIBRERIE CHIAVE ---")
check_package("numpy", "1.26.4")
check_package("paddleocr", "2.7.3")
check_package("paddlepaddle", "2.6.2")
check_package("torch", "2.4.1+cpu")  # O 2.4.1 standard
check_package("ultralytics", "8.3.20")
check_package("gliner", "0.2.7")
check_package("huggingface-hub", "0.22.2")
check_package("opencv-python-headless")

# 2. VERIFICA FILE FISICI (ASSETS)
print("\n--- 2. VERIFICA ASSETS (File Modelli) ---")
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
yolo_path = os.path.join(base_dir, "assets", "models", "id_card_detector_v11n.pt")

yolo_ok = check_asset(yolo_path, "Modello YOLO v11")

# 3. VERIFICA CARTELLA DEBUG
debug_dir = os.path.join(base_dir, "debug_crops")
if not os.path.exists(debug_dir):
    print(f"\n⚠️ Cartella {debug_dir} non esiste. Verrà creata al volo (OK).")

print("\n" + "="*60)
if yolo_ok:
    print("🚀 AUDIT PASSATO: Tutti i componenti critici sono presenti.")
else:
    print("🛑 AUDIT FALLITO: Mancano file essenziali per il deploy.")
print("="*60)