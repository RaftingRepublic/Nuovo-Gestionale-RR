import cv2
import numpy as np
import pytesseract
import os
import sys
import argparse
from pathlib import Path

# --- CONFIGURAZIONE TESSERACT (Simile al tuo backend) ---
# Tenta di trovare Tesseract automaticamente
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
    print("❌ Tesseract non trovato. Imposta TESSERACT_CMD o installalo nei percorsi standard.")
    sys.exit(1)

pytesseract.pytesseract.tesseract_cmd = TESS_CMD

def get_tess_config(whitelist=True):
    """Restituisce la configurazione 'hardcore' per MRZ"""
    config = "--oem 3 --psm 6" # PSM 6 = Assume un singolo blocco di testo uniforme
    if whitelist:
        # Whitelist stretta per MRZ
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"
        config += f" -c tessedit_char_whitelist={chars}"
    return config

def run_test_pipeline(image_path):
    print(f"\n🧪 AVVIO TEST ISOLATO SU: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"❌ File non trovato: {image_path}")
        return

    # Carica immagine originale (in scala di grigi)
    original = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if original is None:
        print("❌ Impossibile leggere l'immagine.")
        return

    # Lista delle pipeline da testare
    pipelines = [
        ("1. RAW (Nessun filtro)", lambda img: img),
        
        ("2. OTSU (Binarizzazione Classica)", lambda img: 
         cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
        
        ("3. ADAPTIVE GAUSSIAN (Attuale in Prod)", lambda img: 
         cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
        
        ("4. EROSION (Ispessisce i caratteri)", lambda img: 
         cv2.erode(cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1], np.ones((2,2), np.uint8), iterations=1)),
        
        ("5. DENOISE + OTSU (Rimuove sfondo CIE)", lambda img: 
         cv2.threshold(cv2.fastNlMeansDenoising(img, None, 10, 7, 21), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
        
        ("6. UPSCALE + CLAHE + OTSU (High Definition)", lambda img: _pipeline_hd(img))
    ]

    # Cartella output per vedere cosa "vede" Tesseract
    out_dir = Path("debug_isolation_results")
    out_dir.mkdir(exist_ok=True)

    print(f"📂 Le immagini processate verranno salvate in: {out_dir.absolute()}")
    print("-" * 60)

    # Verifica lingue disponibili
    langs = pytesseract.get_languages(config='')
    print(f"📚 Lingue disponibili: {langs}")
    best_score = 0
    best_method = ""

    for name, func in pipelines:
        print(f"\n👉 Testing: {name}")
        
        # 1. Applica filtro
        try:
            processed = func(original.copy())
        except Exception as e:
            print(f"   ⚠️ Errore nel preprocessing: {e}")
            continue

        # 2. Salva anteprima
        safe_name = name.split(" ")[1].lower()
        out_path = out_dir / f"test_{safe_name}.jpg"
        cv2.imwrite(str(out_path), processed)

        # 3. Esegui OCR con entrambe le lingue se possibile
        test_langs = ['ocrb', 'eng'] if 'ocrb' in langs else ['eng']
        
        for lang in test_langs:
            try:
                # Usa config con whitelist
                cfg = get_tess_config(whitelist=True)
                text = pytesseract.image_to_string(processed, lang=lang, config=cfg).strip()
                
                # Pulizia output
                text_clean = text.replace(" ", "")
                
                # Valutazione base
                score = 0
                if "<<" in text_clean: score += 5
                if "ITA" in text_clean: score += 3
                if len(text_clean) > 20: score += 2
                
                # Feedback visuale
                marker = "✅" if score >= 5 else "❌"
                print(f"   [{lang.upper()}] Score: {score}/10 -> {marker} Result: {text_clean[:50]}...")

                if score > best_score:
                    best_score = score
                    best_method = f"{name} ({lang})"

            except Exception as e:
                print(f"   ⚠️ Errore Tesseract: {e}")

    print("-" * 60)
    print(f"🏆 VINCITORE: {best_method if best_method else 'Nessuno (Il documento è illeggibile)'}")
    print("Consiglio: Apri la cartella 'debug_isolation_results' e guarda quale immagine ha il testo nero più nitido senza rumore di fondo.")

def _pipeline_hd(img):
    # Scala 2x
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    # Aumenta contrasto locale
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img = clahe.apply(img)
    # Binarizzazione pulita
    return cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

if __name__ == "__main__":
    # Esempio uso: python backend/test_ocr_isolation.py backend/storage/debug_captures/debug_mrz_....jpg
    if len(sys.argv) < 2:
        print("Uso: python test_ocr_isolation.py <path_to_debug_image_jpg>")
        # Cerca l'ultimo file di debug se non passato
        debug_dir = Path(__file__).parent / "debug_captures"
        if debug_dir.exists():
            files = sorted(list(debug_dir.glob("debug_mrz_*.jpg")), key=os.path.getmtime, reverse=True)
            if files:
                print(f"💡 Nessun file specificato. Uso l'ultimo trovato: {files[0].name}")
                run_test_pipeline(str(files[0]))
            else:
                print("❌ Nessun file di debug trovato in backend/debug_captures")
    else:
        run_test_pipeline(sys.argv[1])