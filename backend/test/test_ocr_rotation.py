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

if not TESS_CMD:
    print("❌ Tesseract non trovato.")
    sys.exit(1)

pytesseract.pytesseract.tesseract_cmd = TESS_CMD

def get_tess_config():
    # PSM 6 = Assume un singolo blocco di testo uniforme
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"
    return f"--oem 3 --psm 6 -c tessedit_char_whitelist={chars}"

def apply_smart_preprocessing(img):
    """
    Applica una pulizia aggressiva per CIE:
    1. Upscale (per caratteri piccoli)
    2. Grayscale
    3. Contrasto locale (CLAHE)
    4. Otsu Threshold (Binarizzazione)
    """
    # 1. Upscale se l'immagine è piccola
    h, w = img.shape[:2]
    if h < 100: # Se l'MRZ è più piccola di 100px in altezza, è illeggibile
        scale = 2.0
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # 2. Grayscale (se non lo è già)
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    # 3. CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(gray)

    # 4. Otsu Thresholding (più pulito dell'Adaptive per le CIE)
    _, binary = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary

def run_rotation_test(image_path):
    print(f"\n🔄 TEST ROTAZIONE SU: {os.path.basename(image_path)}")
    
    original = cv2.imread(image_path)
    if original is None:
        print("❌ Impossibile leggere file.")
        return

    # Info base
    h, w = original.shape[:2]
    print(f"📏 Dimensioni originali: {w}x{h} px")
    if h < 50:
        print("⚠️ ATTENZIONE: L'immagine è troppo bassa (<50px). Tesseract fallirà quasi sicuramente.")

    # Prepariamo le varianti
    rotations = [
        ("0° (Originale)", original),
        ("90° Orario", cv2.rotate(original, cv2.ROTATE_90_CLOCKWISE)),
        ("180° Capovolto", cv2.rotate(original, cv2.ROTATE_180)),
        ("270° Antiorario", cv2.rotate(original, cv2.ROTATE_90_COUNTERCLOCKWISE))
    ]

    out_dir = Path("debug_rotation_results")
    out_dir.mkdir(exist_ok=True)

    winner_text = ""
    winner_rot = ""

    for label, img_rot in rotations:
        # Preprocess
        processed = apply_smart_preprocessing(img_rot)
        
        # Salva per debug
        safe_label = label.split(" ")[0].replace("°", "deg")
        cv2.imwrite(str(out_dir / f"rot_{safe_label}.jpg"), processed)

        # OCR
        try:
            # Prova OCRB se c'è, altrimenti ENG
            text = pytesseract.image_to_string(processed, lang='ocrb', config=get_tess_config())
        except:
            text = pytesseract.image_to_string(processed, lang='eng', config=get_tess_config())

        text_clean = text.strip().replace(" ", "")
        
        # Punteggio
        score = 0
        if "<<" in text_clean: score += 5
        if "ITA" in text_clean: score += 3
        if len(text_clean) > 20 and "<" in text_clean: score += 2

        marker = "✅" if score >= 5 else "❌"
        print(f"   [{label}] Score: {score}/10 -> {marker}")
        if score > 0:
            print(f"      Lettura: {text_clean[:60]}...")
        else:
            print(f"      (Spazzatura): {text_clean[:20]}...")

        if score >= 5:
            winner_text = text_clean
            winner_rot = label
            break # Trovato!

    print("-" * 50)
    if winner_rot:
        print(f"🎉 SOLUZIONE TROVATA! L'immagine era ruotata di: {winner_rot}")
        print(f"📄 Testo: {winner_text}")
    else:
        print("💀 Ancora nessun risultato valido. Il problema potrebbe essere il ritaglio errato a monte.")

if __name__ == "__main__":
    # Cerca l'ultimo file debug se non passato
    target = None
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        debug_dir = Path(__file__).parent / "debug_captures"
        files = sorted(list(debug_dir.glob("debug_mrz_*.jpg")), key=os.path.getmtime, reverse=True)
        if files:
            target = str(files[0])
    
    if target:
        run_rotation_test(target)
    else:
        print("Nessun file trovato.")