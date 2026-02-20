import os
import sys
import json
import time
import argparse
from pathlib import Path
from PIL import Image
from datetime import datetime
import statistics

# --- CONFIGURAZIONE AMBIENTALE ---
# Necessario per importare i moduli backend
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Disabilita log pesanti durante il benchmark
os.environ["GLOG_minloglevel"] = "2"
os.environ["ID_IMAGE_RETENTION"] = "NONE"
# Fix per Windows "OMP: Error #15" e DLL loading
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

try:
    import torch
except ImportError:
    pass

from app.services.local_vision_service import analyze_documents_locally

TEST_DATASET_DIR = BASE_DIR / "storage" / "test_dataset"
INPUT_DIR = TEST_DATASET_DIR / "input"
REF_DIR = TEST_DATASET_DIR / "reference"
REPORT_FILE = TEST_DATASET_DIR / "report.md"

def ensure_dirs():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    REF_DIR.mkdir(parents=True, exist_ok=True)

def load_image(path):
    try:
        return Image.open(path).convert("RGB")
    except Exception as e:
        print(f"❌ Errore caricamento {path.name}: {e}")
        return None

def run_prediction(image, doc_type="AUTO"):
    # analyze_documents_locally si aspetta (front, back, hint)
    # Per il benchmark, se abbiamo solo un'immagine, la passiamo come FRONT.
    # Se il file ha suffisso _BACK, potremmo gestirlo, ma per ora semplifichiamo.
    return analyze_documents_locally(image, None, doc_type)

def compare_results(prediction, reference):
    score = 0
    total_fields = 0
    mismatches = []

    # Campi chiave da confrontare
    keys_to_check = [
        "nome", "cognome", "data_nascita", "numero_documento", 
        "scadenza_documento", "comune_nascita", "comune_residenza",
        "cittadinanza", "codice_fiscale"
    ]

    for k in keys_to_check:
        ref_val = reference.get(k)
        pred_val = prediction.get(k)

        if not ref_val: continue # Se il reference non ha il campo, saltiamo (o penalizziamo?)
        
        total_fields += 1
        
        # Normalizzazione basilare per confronto
        r_norm = str(ref_val).lower().strip()
        p_norm = str(pred_val).lower().strip() if pred_val else ""

        if r_norm == p_norm:
            score += 1
        else:
            mismatches.append(f"{k}: Ref='{ref_val}' vs Pred='{pred_val}'")

    accuracy = (score / total_fields) * 100 if total_fields > 0 else 100.0
    return accuracy, mismatches

def generate_ground_truth():
    print(f"🚀 [GENERATE MODE] Creazione JSON di riferimento in {REF_DIR}...")
    ensure_dirs()
    
    images = list(INPUT_DIR.glob("*.jpg")) + list(INPUT_DIR.glob("*.png")) + list(INPUT_DIR.glob("*.jpeg"))
    if not images:
        print("⚠️ Nessuna immagine trovata in input/.")
        return

    for img_path in images:
        print(f"📄 Elaborazione: {img_path.name}")
        img = load_image(img_path)
        if not img: continue

        start = time.time()
        result = run_prediction(img)
        elapsed = time.time() - start

        # Rimuoviamo il debug_log per pulizia nel JSON
        result.pop("debug_log", None)
        
        ref_path = REF_DIR / f"{img_path.stem}.json"
        with open(ref_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        
        print(f"   ✅ Salvato JSON ({elapsed:.2f}s)")

    print("✨ Generazione completata.")

def run_benchmark():
    print(f"🚀 [BENCHMARK MODE] Avvio test di regressione...")
    ensure_dirs()
    
    images = list(INPUT_DIR.glob("*.jpg")) + list(INPUT_DIR.glob("*.png")) + list(INPUT_DIR.glob("*.jpeg"))
    if not images:
        print("⚠️ Nessuna immagine trovata in input/.")
        return

    report_lines = []
    report_lines.append(f"# OCR Benchmark Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("| Image | Accuracy | Time (s) | Mismatches |")
    report_lines.append("|---|---|---|---|")

    total_time = 0
    accuracies = []

    for img_path in images:
        ref_path = REF_DIR / f"{img_path.stem}.json"
        if not ref_path.exists():
            print(f"⚠️ Reference mancante per {img_path.name}. Salto.")
            continue

        with open(ref_path, "r", encoding="utf-8") as f:
            reference = json.load(f)

        img = load_image(img_path)
        start = time.time()
        prediction = run_prediction(img)
        elapsed = time.time() - start
        total_time += elapsed

        acc, errors = compare_results(prediction, reference)
        accuracies.append(acc)

        error_str = "<br>".join(errors) if errors else "✅ Perfect"
        row = f"| {img_path.name} | {acc:.1f}% | {elapsed:.2f} | {error_str} |"
        report_lines.append(row)
        print(f"   📄 {img_path.name}: {acc:.1f}% in {elapsed:.2f}s")

    avg_acc = statistics.mean(accuracies) if accuracies else 0
    avg_time = total_time / len(images) if images else 0

    report_lines.append(f"\n**Summary**")
    report_lines.append(f"- **Avg Accuracy**: {avg_acc:.2f}%")
    report_lines.append(f"- **Avg Time**: {avg_time:.2f}s")
    report_lines.append(f"- **Total Documents**: {len(images)}")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\n📊 Report salvato in: {REPORT_FILE}")
    print(f"   Accuracy Media: {avg_acc:.2f}%")
    print(f"   Tempo Medio: {avg_time:.2f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCR Benchmark Tool")
    parser.add_argument("--mode", choices=["generate", "benchmark"], default="benchmark", help="Mode: generate ground truth or run benchmark")
    args = parser.parse_args()

    if args.mode == "generate":
        generate_ground_truth()
    else:
        run_benchmark()
