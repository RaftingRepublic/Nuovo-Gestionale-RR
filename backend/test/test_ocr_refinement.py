import cv2
import numpy as np
import pytesseract
import os
import sys
from pathlib import Path

# --- CONFIGURAZIONE ---
DEFAULT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"/usr/bin/tesseract",
    r"/usr/local/bin/tesseract"
]

TESS_CMD = os.getenv("TESSERACT_CMD")
if not TESS_CMD:
    for p in DEFAULT_PATHS:
        if os.path.exists(p):
            TESS_CMD = p
            break
if TESS_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESS_CMD

def get_tess_config():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"
    return f"--oem 3 --psm 6 -c tessedit_char_whitelist={chars}"

def run_refinement(image_path):
    print(f"\n🧼 REFINEMENT TEST SU: {os.path.basename(image_path)}")
    
    # Leggi in scala di grigi
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("❌ File non trovato.")
        return

    # Se l'immagine è per lo più nera (come il blackhat), invertila per avere testo nero su bianco
    if np.mean(img) < 127:
        print("🔄 Rilevato sfondo scuro: Inverto i colori...")
        img = cv2.bitwise_not(img)

    # Assicuriamo una dimensione minima per far funzionare i kernel morfologici
    h, w = img.shape
    if h < 200:
        scale = 2.0
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        print(f"🔍 Upscaling 2x attivo (nuova h: {img.shape[0]})")

    # Binarizzazione base di partenza (Otsu)
    _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # --- LE ARMI SEGRETE CONTRO LE LINEE SOTTILI ---
    strategies = []

    # 1. Median Blur (Ottimo per rumore "sale e pepe" e linee sottili)
    strategies.append(("Median Blur 3", cv2.medianBlur(binary, 3)))
    strategies.append(("Median Blur 5", cv2.medianBlur(binary, 5)))

    # 2. Morphological Opening (Erosione seguita da Dilatazione) -> Mangia le linee sottili
    kernel_small = np.ones((2,2), np.uint8)
    strategies.append(("Morph Open (2x2)", cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_small)))

    kernel_med = np.ones((3,3), np.uint8)
    strategies.append(("Morph Open (3x3)", cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_med)))

    # 3. Combo: Median + Open (Distruzione totale rumore)
    combo = cv2.medianBlur(binary, 3)
    combo = cv2.morphologyEx(combo, cv2.MORPH_OPEN, kernel_small)
    strategies.append(("COMBO (Median+Open)", combo))

    out_dir = Path("debug_refinement_results")
    out_dir.mkdir(exist_ok=True)

    for name, processed in strategies:
        # Salva
        fname = name.replace(" ", "_").replace("(", "").replace(")", "").lower()
        cv2.imwrite(str(out_dir / f"refine_{fname}.jpg"), processed)

        # OCR
        text = "N/A"
        try:
            text = pytesseract.image_to_string(processed, lang='ocrb', config=get_tess_config())
        except:
            text = pytesseract.image_to_string(processed, lang='eng', config=get_tess_config())
        
        text_clean = text.strip().replace(" ", "")
        
        # Score
        score = 0
        if "<<" in text_clean: score += 5
        if "ITA" in text_clean: score += 3
        if len(text_clean) > 20: score += 2

        marker = "✅" if score >= 5 else "❌"
        print(f"   [{name}] Score: {score}/10 -> {marker}")
        print(f"      Lettura: {text_clean[:50]}...")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_refinement(sys.argv[1])
    else:
        # Cerca l'ultimo file debug
        debug_dir = Path(__file__).parent / "debug_captures"
        if debug_dir.exists():
            files = sorted(list(debug_dir.glob("debug_mrz_*.jpg")), key=os.path.getmtime, reverse=True)
            if files: run_refinement(str(files[0]))