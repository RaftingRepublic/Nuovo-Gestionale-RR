# backend/tools/test_yolo_inference.py
import sys
import os
import cv2
from pathlib import Path

# Aggiungiamo la root del backend al path per poter importare i moduli app.*
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.services.image_utils import isolate_document_yolo, cv2_to_pil, pil_to_cv2

def test_inference():
    print("🧠 TEST INFERENZA YOLOv11...")
    
    # 1. Prendiamo un'immagine dal dataset di validazione generato prima
    val_dir = BASE_DIR / "datasets" / "id_cards" / "val" / "images"
    images = list(val_dir.glob("*.jpg"))
    
    if not images:
        print("❌ Nessuna immagine trovata in datasets/id_cards/val/images")
        return

    # Prendiamo la prima immagine
    target_img_path = images[0]
    print(f"📄 Test su immagine: {target_img_path.name}")
    
    # Carichiamo come PIL (come farebbe il backend)
    original_pil = cv2_to_pil(cv2.imread(str(target_img_path)))
    
    # 2. ESEGUIAMO LA MAGIA
    # Questa funzione ora usa il tuo modello id_card_detector_v11n.pt!
    try:
        cropped_pil = isolate_document_yolo(original_pil, debug_prefix="TEST_MANUALE")
    except Exception as e:
        print(f"❌ Errore durante l'inferenza: {e}")
        return

    if cropped_pil:
        print("✅ SUCCESSO! Documento rilevato e raddrizzato.")
        
        # Salviamo il risultato per vederlo
        out_path = "test_result_cropped.jpg"
        pil_to_cv2(cropped_pil) # Riconvertiamo per salvare con cv2 se necessario, o usa save del PIL
        cropped_pil.save(out_path)
        print(f"💾 Risultato salvato in: {os.path.abspath(out_path)}")
        print("   Aprilo e verifica che sia un rettangolo perfetto senza sfondo!")
    else:
        print("❌ FALLITO. Il modello non ha trovato nulla (o il file .pt non è nel posto giusto).")

if __name__ == "__main__":
    test_inference()