# backend/tools/generate_synthetic_data.py
import cv2
import numpy as np
import os
import random
from pathlib import Path

# Configurazione
NUM_IMAGES = 100  # Generiamo 100 immagini finte
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "assets" / "templates"
OUTPUT_DIR = BASE_DIR / "datasets" / "id_cards"

# Crea cartelle
(OUTPUT_DIR / "train" / "images").mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "train" / "labels").mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "val" / "images").mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "val" / "labels").mkdir(parents=True, exist_ok=True)

def create_random_background(h, w):
    """Crea uno sfondo rumoroso casuale"""
    # Colore base casuale (grigio/legno/tavolo)
    color = np.random.randint(100, 200, size=(1, 1, 3), dtype=np.uint8)
    bg = np.ones((h, w, 3), dtype=np.uint8) * color
    # Aggiungi rumore
    noise = np.random.randint(-50, 50, size=(h, w, 3), dtype=np.int16)
    bg = np.clip(bg + noise, 0, 255).astype(np.uint8)
    return bg

def rotate_image(image, angle):
    """Ruota l'immagine e calcola i nuovi 4 angoli"""
    h, w = image.shape[:2]
    cx, cy = w // 2, h // 2
    
    # Matrice di rotazione
    M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    
    # Nuove dimensioni bounding box
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    
    M[0, 2] += (nW / 2) - cx
    M[1, 2] += (nH / 2) - cy
    
    rotated = cv2.warpAffine(image, M, (nW, nH), borderValue=(0,0,0))
    
    # Calcola le coordinate dei 4 angoli originali trasformati
    # Ordine: TL, TR, BR, BL
    corners = np.array([
        [0, 0],
        [w, 0],
        [w, h],
        [0, h]
    ])
    
    ones = np.ones(shape=(len(corners), 1))
    corners_ones = np.hstack([corners, ones])
    transformed = M.dot(corners_ones.T).T
    
    # Maschera alpha per incollare
    mask = cv2.warpAffine(np.ones((h, w), dtype=np.uint8)*255, M, (nW, nH))
    
    return rotated, mask, transformed

def generate():
    # Cerca i template disponibili (CIE, Patente, ecc.)
    templates = list(TEMPLATES_DIR.glob("*.jpg")) + list(TEMPLATES_DIR.glob("*.png"))
    if not templates:
        print(f"❌ Nessun template trovato in {TEMPLATES_DIR}")
        return

    print(f"🎨 Generazione {NUM_IMAGES} immagini sintetiche da {len(templates)} template...")

    for i in range(NUM_IMAGES):
        # 1. Scegli template e sfondo
        tpl_path = random.choice(templates)
        card = cv2.imread(str(tpl_path))
        
        # Ridimensiona template a una dimensione realistica (es. larghezza 400-600px)
        target_w = random.randint(400, 600)
        aspect = card.shape[0] / card.shape[1]
        card = cv2.resize(card, (target_w, int(target_w * aspect)))
        
        # Sfondo più grande
        bg_h, bg_w = 1024, 1024
        bg = create_random_background(bg_h, bg_w)
        
        # 2. Ruota la carta
        angle = random.randint(-180, 180)
        rot_card, mask, corners = rotate_image(card, angle)
        
        # 3. Posiziona la carta sullo sfondo
        h_rot, w_rot = rot_card.shape[:2]
        # Assicuriamoci che stia dentro
        max_x = bg_w - w_rot
        max_y = bg_h - h_rot
        
        if max_x < 0 or max_y < 0: continue # Skip se troppo grande dopo rotazione
        
        x_off = random.randint(0, max_x)
        y_off = random.randint(0, max_y)
        
        # Incolla
        roi = bg[y_off:y_off+h_rot, x_off:x_off+w_rot]
        # Dove la maschera è > 0, usa la carta, altrimenti tieni lo sfondo
        mask_bool = mask > 0
        roi[mask_bool] = rot_card[mask_bool]
        bg[y_off:y_off+h_rot, x_off:x_off+w_rot] = roi
        
        # 4. Aggiorna coordinate assolute globali
        final_corners = corners + [x_off, y_off]
        
        # 5. Prepara Label YOLO OBB
        # Formato: class_index x1 y1 x2 y2 x3 y3 x4 y4 (Normalizzati 0-1)
        # class_index è sempre 0 ("id_card")
        norm_corners = final_corners / [bg_w, bg_h]
        flat_coords = " ".join([f"{c[0]:.6f} {c[1]:.6f}" for c in norm_corners])
        label_str = f"0 {flat_coords}"
        
        # 6. Salva (Split 80/20 train/val)
        subset = "train" if i < (NUM_IMAGES * 0.8) else "val"
        filename = f"syn_{i:04d}"
        
        cv2.imwrite(str(OUTPUT_DIR / subset / "images" / f"{filename}.jpg"), bg)
        with open(OUTPUT_DIR / subset / "labels" / f"{filename}.txt", "w") as f:
            f.write(label_str)

    print("✅ Generazione completata. Dataset pronto in backend/datasets/id_cards")

if __name__ == "__main__":
    generate()