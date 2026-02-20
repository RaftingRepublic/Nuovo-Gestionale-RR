import cv2
import numpy as np
import pytesseract
import os
import sys
from pathlib import Path

# --- CONFIGURAZIONE BASE ---
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
    print("❌ Tesseract non trovato. Verifica l'installazione.")
    sys.exit(1)

pytesseract.pytesseract.tesseract_cmd = TESS_CMD

def get_tess_config():
    # PSM 6 = Blocco di testo uniforme (perfetto per MRZ)
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"
    return f"--oem 3 --psm 6 -c tessedit_char_whitelist={chars}"

# --- PIPELINE AVANZATE DI PULIZIA ---

def pipe_1_division_norm(img):
    """
    Tecnica 'Division Normalization':
    Divide l'immagine per la sua versione sfocata. 
    Questo appiattisce lo sfondo (rimuovendo ombre e pattern leggeri) lasciando il testo netto.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    
    # Sfocatura ampia per stimare lo sfondo
    bg = cv2.GaussianBlur(gray, (25, 25), 0)
    
    # Divisione: (img / bg) * 255
    # Evitiamo divisione per zero aggiungendo 1
    norm = cv2.divide(gray, bg, scale=255)
    
    # Binarizzazione finale su immagine normalizzata
    _, binary = cv2.threshold(norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def pipe_2_morph_blackhat(img):
    """
    Tecnica 'Black Hat':
    Estrae elementi scuri (testo) su sfondo chiaro.
    Molto potente contro pattern e ologrammi.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    
    # Kernel rettangolare orizzontale (adatto ai caratteri MRZ)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
    
    # Blackhat: Differenza tra chiusura e immagine originale
    blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
    
    # Aumentiamo il contrasto del risultato
    # Tutto ciò che era sfondo ora è nero, il testo è bianco/grigio
    _, binary = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Invertiamo per avere testo nero su bianco (formato standard OCR)
    return cv2.bitwise_not(binary)

def pipe_3_gamma_contrast(img):
    """
    Aumento contrasto estremo + Gamma Correction
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    
    # Gamma < 1 schiarisce i mezzitoni (lo sfondo)
    gamma = 0.5
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    adjusted = cv2.LUT(gray, table)
    
    # Binarizzazione
    _, binary = cv2.threshold(adjusted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def pipe_4_heavy_blur_threshold(img):
    """
    Sfocatura prima del threshold per 'fondere' il rumore di fondo
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    
    # Gaussian Blur leggero per rimuovere il retino tipografico
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Adaptive Threshold con parametri più laschi
    binary = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY, 21, 10)
    return binary

def run_noise_test(image_path):
    print(f"\n🧹 TEST RIMOZIONE RUMORE SU: {os.path.basename(image_path)}")
    
    original = cv2.imread(image_path)
    if original is None:
        print("❌ File non trovato.")
        return

    pipelines = [
        ("Division Norm", pipe_1_division_norm),
        ("Morph BlackHat", pipe_2_morph_blackhat),
        ("Gamma Contrast", pipe_3_gamma_contrast),
        ("Blur+Adaptive", pipe_4_heavy_blur_threshold)
    ]

    out_dir = Path("debug_noise_results")
    out_dir.mkdir(exist_ok=True)

    winner_method = ""
    best_score = 0

    for name, func in pipelines:
        # Elabora
        processed = func(original.copy())
        
        # Salva debug
        safe_name = name.replace(" ", "_").lower()
        cv2.imwrite(str(out_dir / f"noise_{safe_name}.jpg"), processed)

        # OCR
        try:
            text = pytesseract.image_to_string(processed, lang='ocrb', config=get_tess_config())
        except:
            text = pytesseract.image_to_string(processed, lang='eng', config=get_tess_config())

        text_clean = text.strip().replace(" ", "")
        
        # Scoring
        score = 0
        if "<<" in text_clean: score += 5
        if "ITA" in text_clean: score += 3
        if len(text_clean) > 20: score += 2
        # Penalità per troppi caratteri strani (rumore letto come testo)
        if len(text_clean) > 90: score -= 3 

        marker = "✅" if score >= 5 else "❌"
        print(f"   [{name}] Score: {score}/10 -> {marker}")
        if score > 0:
            print(f"      Lettura: {text_clean[:60]}...")
        
        if score > best_score:
            best_score = score
            winner_method = name

    print("-" * 50)
    if winner_method:
        print(f"🏆 METODO VINCENTE: {winner_method}")
        print("Integra questo metodo in 'image_utils.py' > 'enhance_image_for_mrz'")
    else:
        print("💀 Nessun metodo ha funzionato perfettamente. Controlla la cartella 'debug_noise_results' per vedere quale immagine è più pulita all'occhio umano.")

if __name__ == "__main__":
    target = None
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        debug_dir = Path(__file__).parent / "debug_captures"
        if debug_dir.exists():
            files = sorted(list(debug_dir.glob("debug_mrz_*.jpg")), key=os.path.getmtime, reverse=True)
            if files: target = str(files[0])
    
    if target:
        run_noise_test(target)
    else:
        print("Nessuna immagine di debug trovata.")