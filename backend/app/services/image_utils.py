# backend/app/services/image_utils.py
import cv2
import numpy as np
import os
import time
import uuid
from pathlib import Path
from PIL import Image

# [FASE 2] Integrazione Libreria YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️ Ultralytics non installato. YOLO non disponibile.")

# --- CONFIGURAZIONE PERCORSI ROBUSTA ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEBUG_DIR = BASE_DIR / "storage" / "debug_captures"
DATASET_DIR = BASE_DIR / "storage" / "dataset_raw"
MODELS_DIR = BASE_DIR / "assets" / "models"

# Costanti per la standardizzazione ID-1 (formato carta di credito/CIE/Patente)
# Rapporto aspetto standard: 85.60mm / 53.98mm ≈ 1.585
TARGET_WIDTH = 1000
TARGET_HEIGHT = 630 # 1000 / 1.585

try:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"❌ ERRORE CREAZIONE DIR: {e}")

# --- SINGLETON MODELLO YOLO ---
_yolo_model = None

def get_yolo_model():
    """
    Carica il modello YOLOv11n-OBB una volta sola (Singleton).
    """
    global _yolo_model
    if not YOLO_AVAILABLE:
        return None
        
    if _yolo_model is None:
        model_path = MODELS_DIR / "id_card_detector_v11n.pt"
        if model_path.exists():
            print(f"🧠 [SETUP] Caricamento Modello YOLO da: {model_path}")
            try:
                _yolo_model = YOLO(str(model_path))
                print("🧠 [SETUP] Modello caricato correttamente.")
            except Exception as e:
                print(f"❌ [SETUP] Errore caricamento pesi YOLO: {e}")
                return None
        else:
            print(f"⚠️ [SETUP] Modello YOLO non trovato in {model_path}. Esegui il training prima!")
            return None
    return _yolo_model

def release_yolo_model():
    """
    Rilascia la memoria occupata dal modello YOLO.
    """
    global _yolo_model
    if _yolo_model is not None:
        del _yolo_model
        _yolo_model = None
        import gc
        gc.collect()
        print("🗑️ [CLEANUP] Modello YOLO scaricato dalla RAM.")

def order_points(pts):
    """
    Ordina le coordinate (top-left, top-right, bottom-right, bottom-left)
    necessario per il perspective warp corretto.
    """
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)] # TL
    rect[2] = pts[np.argmax(s)] # BR
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)] # TR
    rect[3] = pts[np.argmax(diff)] # BL
    return rect

def isolate_document_yolo(image: Image.Image, debug_prefix: str = "yolo") -> Image.Image | None:
    """
    [FASE 2 STRATEGIA]
    Usa YOLOv11-OBB per rilevare il documento, trovare i 4 angoli 
    e applicare la correzione prospettica (Warp) su una griglia standardizzata.
    Include LOG DETTAGLIATI per debug.
    """
    print(f"\n🔍 [YOLO DETECT] Avvio analisi su immagine sorgente ({debug_prefix})")
    
    model = get_yolo_model()
    if model is None:
        print("   ❌ [YOLO] Modello non caricato. Salto.")
        return None
    
    if image is None:
        print("   ❌ [YOLO] Immagine input vuota (None).")
        return None

    img_cv = pil_to_cv2(image)
    if img_cv is None: 
        print("   ❌ [YOLO] Conversione PIL->CV2 fallita.")
        return None

    # Inferenza (verbose=False per pulizia log, li facciamo noi manuali)
    results = model(img_cv, verbose=False)
    
    if not results or len(results) == 0:
        print(f"   ❌ [YOLO] Nessun risultato restituito dal modello.")
        return None

    r = results[0]
    
    # Controllo se è OBB
    if r.obb is None or len(r.obb) == 0:
        print(f"   ⚠️ [YOLO] Nessun oggetto rilevato (OBB vuoto).")
        return None

    # Prendi il box con confidenza maggiore
    best_idx = int(r.obb.conf.argmax())
    conf = float(r.obb.conf[best_idx])
    
    # LOG CONFIDENZA
    print(f"   ✅ [YOLO] Documento TROVATO! Confidenza: {conf:.4f}")
    
    # Estrazione angoli (xyxyxyxy)
    corners = r.obb.xyxyxyxy[best_idx].cpu().numpy()
    
    # LOG COORDINATE GREZZE
    print(f"      [YOLO] Angoli grezzi rilevati:\n{corners}")
    
    # 1. Ordina i punti rilevati: TL, TR, BR, BL
    rect = order_points(corners)
    (tl, tr, br, bl) = rect

    # 2. Calcola larghezza e altezza reali rilevate (per decidere l'orientamento)
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    detected_width = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    detected_height = max(int(heightA), int(heightB))
    
    # LOG DIMENSIONI
    print(f"      [YOLO] Dimensioni stimate crop: {detected_width}x{detected_height} px")

    # 3. Logica "Smart Orientation"
    final_w, final_h = TARGET_WIDTH, TARGET_HEIGHT
    
    # Se l'altezza rilevata è maggiore della larghezza, la carta è verticale (ruotata di 90 o 270)
    is_vertical = detected_height > detected_width
    
    if is_vertical:
            print(f"      [YOLO] 🔄 Rilevata carta VERTICALE (H > W). Preparo rotazione per OCR...")
            # Impostiamo il target del warp verticale (630x1000)
            warp_w, warp_h = TARGET_HEIGHT, TARGET_WIDTH 
    else:
            print(f"      [YOLO] ➡️ Rilevata carta ORIZZONTALE. Procedo standard.")
            # Impostiamo il target del warp orizzontale (1000x630)
            warp_w, warp_h = TARGET_WIDTH, TARGET_HEIGHT

    # Punti sorgente (dal detection)
    src_pts = rect
    
    # Punti destinazione (rettangolo perfetto)
    dst_dynamic = np.array([
        [0, 0],
        [warp_w - 1, 0],
        [warp_w - 1, warp_h - 1],
        [0, warp_h - 1]], dtype="float32")

    # Calcolo matrice e Warp
    M = cv2.getPerspectiveTransform(src_pts, dst_dynamic)
    warped = cv2.warpPerspective(img_cv, M, (warp_w, warp_h))
    
    # Se abbiamo fatto il warp verticale, ora ruotiamo di 90° per averla orizzontale
    if is_vertical:
        warped = cv2.rotate(warped, cv2.ROTATE_90_CLOCKWISE)
        print("      [YOLO] 🔄 Rotazione 90° applicata post-warp.")

    # A questo punto abbiamo SEMPRE un'immagine ~1000x630 orizzontale.
    _save_debug_step(warped, debug_prefix, "YOLO_WARP_HD")
    
    print(f"      [YOLO] ✅ Operazione completata. Immagine pronta per OCR.")
    release_yolo_model()
    return cv2_to_pil(warped)


def save_raw_dataset_image(img, label: str):
    """
    Salva l'immagine grezza in storage/dataset_raw per il futuro training di YOLOv11.
    """
    if img is None: return
    try:
        unique_id = str(uuid.uuid4())[:8]
        ts = int(time.time())
        filename = f"{ts}_{unique_id}_{label}.jpg"
        path = DATASET_DIR / filename
        if isinstance(img, Image.Image):
            img.save(str(path), quality=95)
        else:
            cv2.imwrite(str(path), img)
    except Exception as e:
        print(f"   ⚠️ [DATASET ERROR]: {e}")

def _save_debug_step(img, prefix, step_name):
    if img is None: return None
    try:
        ts = int(time.time() * 1000)
        safe_prefix = "".join(c for c in prefix if c.isalnum() or c in ('_', '-'))
        filename = f"debug_{safe_prefix}_{ts}_{step_name}.jpg"
        path = DEBUG_DIR / filename
        if isinstance(img, Image.Image):
            img.save(str(path))
        else:
            cv2.imwrite(str(path), img)
        return filename
    except Exception as e:
        print(f"   ❌ [DEBUG ERROR] {step_name}: {e}")
        return None

def cv2_to_pil(img_cv):
    if img_cv is None: return None
    try:
        if len(img_cv.shape) == 2: return Image.fromarray(img_cv)
        if len(img_cv.shape) == 3 and img_cv.shape[2] == 3:
            return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        if len(img_cv.shape) == 3 and img_cv.shape[2] == 4:
            return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGRA2RGBA))
        return Image.fromarray(img_cv)
    except: return None

def pil_to_cv2(img_pil):
    try:
        if img_pil.mode != "RGB":
            img_pil = img_pil.convert("RGB")
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    except: return None

# --- FUNZIONI LEGACY/HELPER (Mantenute per retrocompatibilità) ---
def apply_clahe(image):
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)
    except:
        return image

def align_images_orb(image, template, max_features=5000, debug_prefix="align", mask=None):
    # Deprecato in favore di YOLO, ma mantenuto per sicurezza
    try:
        if image is None or template is None: return None
        h_tpl, w_tpl = template.shape[:2]
        h_img, w_img = image.shape[:2]
        scale_factor = 1.0
        working_image = image.copy()
        if w_img > w_tpl * 1.5:
            scale_factor = w_tpl / w_img
            new_w = int(w_img * scale_factor)
            new_h = int(h_img * scale_factor)
            working_image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

        imgGray = apply_clahe(working_image)
        tmplGray = apply_clahe(template)
        orb = cv2.ORB_create(nfeatures=max_features)
        kpsA, descsA = orb.detectAndCompute(imgGray, None)
        kpsB, descsB = orb.detectAndCompute(tmplGray, mask=mask)

        if descsA is None or descsB is None: return None
        matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
        knn_matches = matcher.knnMatch(descsA, descsB, 2)
        good_matches = []
        for m, n in knn_matches:
            if m.distance < 0.75 * n.distance: good_matches.append(m)

        if len(good_matches) < 10: return None
        ptsA = np.zeros((len(good_matches), 2), dtype="float")
        ptsB = np.zeros((len(good_matches), 2), dtype="float")
        for (i, m) in enumerate(good_matches):
            ptsA[i] = np.array(kpsA[m.queryIdx].pt) * (1.0 / scale_factor)
            ptsB[i] = kpsB[m.trainIdx].pt

        (H, mask_ransac) = cv2.findHomography(ptsA, ptsB, method=cv2.RANSAC, ransacReprojThreshold=5.0)
        if H is None: return None
        (h, w) = template.shape[:2]
        aligned = cv2.warpPerspective(image, H, (w, h))
        return aligned
    except Exception as e:
        print(f"❌ ALIGN CRASH: {e}")
        return None

def enhance_image_for_mrz(pil_image, debug_prefix="mrz"):
    try:
        image = pil_to_cv2(pil_image)
        if image is None: return pil_image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        h, w = gray.shape[:2]
        if w < 1000:
            scale = 2.0
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        return cv2_to_pil(thresh)
    except Exception: return pil_image

def enhance_field_crop(pil_image, debug_prefix="field"):
    try:
        image = pil_to_cv2(pil_image)
        if image is None: return pil_image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        h, w = gray.shape[:2]
        if h < 60:
            scale = 2.0
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        blur = cv2.GaussianBlur(gray, (25, 25), 0)
        norm = cv2.divide(gray, blur, scale=255)
        binary = cv2.adaptiveThreshold(norm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5)
        return cv2_to_pil(binary)
    except Exception: return pil_image

def assess_image_quality(image_cv):
    if image_cv is None: return False, {"error": "No image"}
    try:
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        mean_brightness = np.mean(gray)
        return True, {"blur": blur_score, "brightness": mean_brightness}
    except: return False, {}