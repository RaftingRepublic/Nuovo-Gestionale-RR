# backend/tools/train_yolo.py
from ultralytics import YOLO
import os

def train_document_detector():
    """
    Script per addestrare YOLOv11n-OBB sul dataset di documenti.
    Output: un modello .pt ottimizzato per il crop dei documenti.
    """
    # 1. Carica il modello pre-addestrato nano (più veloce per CPU)
    # La versione -obb (Oriented Bounding Box) è cruciale per documenti ruotati
    model = YOLO("yolo11n-obb.pt") 

    # 2. Configura i percorsi
    # Assicurati di avere un file dataset.yaml nel formato standard YOLO
    # che punta alle tue immagini annotate.
    dataset_yaml = "dataset.yaml" 
    
    if not os.path.exists(dataset_yaml):
        print("❌ ERRORE: File 'dataset.yaml' mancante.")
        print("   Crea un file YAML che punti alle cartelle 'train' e 'val' delle immagini annotate.")
        return

    print("🚀 Avvio Training YOLOv11-OBB...")
    
    # 3. Avvia il training
    # epochs=100: un buon bilanciamento iniziale
    # imgsz=640: risoluzione standard
    # device='cpu' o '0' (se hai GPU Nvidia)
    results = model.train(
        data=dataset_yaml, 
        epochs=100, 
        imgsz=640, 
        patience=20,
        batch=16,
        project="rafting_republic_train",
        name="id_card_obb"
    )

    # 4. Export del modello migliore
    # Lo salviamo dove il backend se lo aspetta
    backend_model_dir = os.path.join("..", "assets", "models")
    os.makedirs(backend_model_dir, exist_ok=True)
    
    best_model_path = os.path.join("rafting_republic_train", "id_card_obb", "weights", "best.pt")
    dest_path = os.path.join(backend_model_dir, "id_card_detector_v11n.pt")
    
    if os.path.exists(best_model_path):
        import shutil
        shutil.copy2(best_model_path, dest_path)
        print(f"✅ Modello salvato e pronto in: {dest_path}")
    else:
        print("⚠️ Training completato ma non trovo i pesi finali.")

if __name__ == "__main__":
    train_document_detector()