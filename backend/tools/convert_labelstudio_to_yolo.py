import json
import shutil
import os
import random
import cv2
import numpy as np
from pathlib import Path

# --- CONFIGURAZIONE ROBUSTA (FIX PERCORSI) ---
# 1. Ottieni la cartella dove si trova QUESTO file script (cioè backend/tools)
SCRIPT_DIR = Path(__file__).resolve().parent

# 2. Il file JSON deve essere nella stessa cartella dello script
JSON_EXPORT_PATH = SCRIPT_DIR / "project_export.json"

# 3. Risaliamo alla cartella 'backend' (padre di 'tools')
BACKEND_DIR = SCRIPT_DIR.parent

# 4. Definiamo gli altri percorsi partendo da BACKEND_DIR
# Cartella immagini raw: backend/storage/dataset_raw
RAW_IMAGES_DIR = BACKEND_DIR / "storage" / "dataset_raw"

# Output Dataset YOLO: backend/datasets/id_cards
OUTPUT_DIR = BACKEND_DIR / "datasets" / "id_cards"

def convert():
    # Debug visivo dei percorsi
    print(f"📂 Script Dir: {SCRIPT_DIR}")
    print(f"📂 Cerco JSON qui: {JSON_EXPORT_PATH}")
    print(f"📂 Cerco Immagini qui: {RAW_IMAGES_DIR}")

    if not JSON_EXPORT_PATH.exists():
        print(f"❌ ERRORE: File non trovato: {JSON_EXPORT_PATH}")
        print("   Assicurati di aver salvato l'export di Label Studio come 'project_export.json'")
        print("   dentro la cartella: backend/tools/")
        return

    # Pulisci e crea cartelle output
    for split in ['train', 'val']:
        (OUTPUT_DIR / split / "images").mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / split / "labels").mkdir(parents=True, exist_ok=True)

    try:
        with open(JSON_EXPORT_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("❌ ERRORE: Il file JSON non è valido o è corrotto.")
        return

    print(f"🔄 Elaborazione di {len(data)} task di annotazione...")
    
    success_count = 0

    for task in data:
        # 1. Trova il nome file originale
        # Label studio path es: "/data/upload/12/345-immagine.jpg"
        # Prendiamo l'ultima parte dopo eventuali separatori di percorso
        ls_path = task['data']['image']
        
        # In Label Studio locale, spesso il file viene rinominato con un hash prefisso (es. "8d7s6f-nomefile.jpg")
        # Tentiamo di recuperare il file originale.
        if '-' in ls_path:
            # Prende tutto dopo il primo trattino (rischiose se il file ha trattini, ma standard LS)
            # O meglio: controlliamo se esiste il file esatto in RAW, altrimenti cerchiamo il suffix
            filename_part = ls_path.split('/')[-1] # nomefile completo in LS
        else:
            filename_part = ls_path.split('/')[-1]

        # Cerchiamo il file nella cartella raw
        found_img_path = None
        
        # Tentativo 1: Cerca corrispondenza esatta nella cartella raw (se LS non ha rinominato)
        if (RAW_IMAGES_DIR / filename_part).exists():
            found_img_path = RAW_IMAGES_DIR / filename_part
        else:
            # Tentativo 2: Il nome in LS ha un hash davanti (es "34534-foto.jpg").
            # Cerchiamo nella cartella raw un file che "finisca" con la parte originale del nome.
            # Questo è necessario perché non sappiamo l'hash esatto che LS ha generato se non usiamo il suo storage.
            original_name_candidate = filename_part
            if '-' in filename_part:
                 original_name_candidate = filename_part.split('-', 1)[-1] # Rimuove solo il primo pezzo (hash)
            
            if (RAW_IMAGES_DIR / original_name_candidate).exists():
                found_img_path = RAW_IMAGES_DIR / original_name_candidate
            else:
                # Tentativo 3: Ricerca brutale per suffisso (lento ma sicuro)
                for f in RAW_IMAGES_DIR.glob("*"):
                    if filename_part.endswith(f.name) or f.name in filename_part:
                        found_img_path = f
                        break
        
        if not found_img_path:
            print(f"⚠️ Immagine non trovata per: {filename_part}")
            continue

        # 2. Leggi dimensioni immagine (per normalizzare)
        img = cv2.imread(str(found_img_path))
        if img is None: 
            print(f"⚠️ Impossibile leggere immagine: {found_img_path}")
            continue
            
        h_img, w_img = img.shape[:2]

        # 3. Estrai annotazioni
        label_lines = []
        # Supporto sia per struttura export standard che snapshot
        annotations = task.get('annotations', [])
        
        for ann in annotations:
            for res in ann.get('result', []):
                # Gestiamo solo PolygonLabels
                if res['type'] != 'polygonlabels': continue
                
                points = res['value']['points'] # [[x,y], [x,y]...] in percentuale 0-100
                
                # YOLO OBB vuole: class x1 y1 x2 y2 x3 y3 x4 y4 (Normalizzati 0-1)
                
                flat_coords = []
                for p in points:
                    # Label studio usa coordinate relative 0-100
                    nx = p[0] / 100.0
                    ny = p[1] / 100.0
                    flat_coords.extend([f"{nx:.6f}", f"{ny:.6f}"])
                
                # Se abbiamo meno di 3 punti, non è un poligono valido
                if len(points) < 3: continue
                
                # Class index 0 = id_card (unica classe)
                line = f"0 {' '.join(flat_coords)}"
                label_lines.append(line)

        if not label_lines:
            # Nessuna annotazione poligonale valida trovata
            continue

        # 4. Split Train/Val (80% Train, 20% Val)
        subset = "train" if random.random() < 0.8 else "val"
        
        # 5. Salva File
        # Usiamo un nome univoco basato sull'ID del task per evitare sovrascritture
        out_name = f"{task['id']}_{found_img_path.name}"
        
        # Copia immagine
        shutil.copy2(found_img_path, OUTPUT_DIR / subset / "images" / out_name)
        
        # Scrivi Label
        # Sostituisci estensione immagine con .txt
        txt_name = os.path.splitext(out_name)[0] + ".txt"
        with open(OUTPUT_DIR / subset / "labels" / txt_name, "w") as out_f:
            out_f.write("\n".join(label_lines))
            
        success_count += 1

    print("-" * 50)
    print(f"✅ Conversione completata!")
    print(f"📊 Immagini processate con successo: {success_count}")
    print(f"📂 Cartella Output: {OUTPUT_DIR}")

if __name__ == "__main__":
    convert()