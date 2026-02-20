import cv2
import json
import sys
import os

# --- CONFIGURAZIONE ROBUSTA DEI PERCORSI ---
# Ottiene la cartella dove si trova questo script (backend/tools)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Risale alla cartella padre (backend)
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
# Costruisce il percorso assoluto verso l'immagine
TEMPLATE_PATH = os.path.join(BACKEND_DIR, "assets", "templates", "Model_CIE_retro.jpg")

WINDOW_NAME = "Rafting Republic - Zone Calibrator"

def calibrate_template(image_path):
    print(f"Cercando immagine in: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"❌ ERRORE: Immagine non trovata.")
        print(f"Assicurati di aver messo 'cie_front.jpg' in: {os.path.dirname(image_path)}")
        return

    # Carica immagine
    img = cv2.imread(image_path)
    if img is None:
        print("❌ ERRORE: OpenCV non riesce ad aprire l'immagine (formato non valido o file corrotto).")
        return

    h, w = img.shape[:2]
    print(f"\n--- CALIBRAZIONE AVVIATA ---")
    print(f"Immagine: {w}x{h}")
    print("\nISTRUZIONI:")
    print("1. Si aprirà una finestra con l'immagine.")
    print("2. Usa il mouse per disegnare un rettangolo attorno al dato (es. Cognome).")
    print("3. Premi SPAZIO o INVIO per confermare la selezione.")
    print("4. Torna qui nella console e scrivi il nome del campo (es. 'cognome').")
    print("5. Premi 'c' per cancellare una selezione errata.")
    print("6. Premi 'q' (o Esc) sulla finestra immagine per terminare e generare il JSON.")
    print("----------------------------")

    zones = {}

    while True:
        # Usa la funzione nativa di OpenCV per selezionare ROI
        try:
            rect = cv2.selectROI(WINDOW_NAME, img, showCrosshair=True)
        except KeyboardInterrupt:
            break
        
        # rect è una tupla (x, y, w, h)
        x, y, rw, rh = rect

        # Se l'utente preme 'q' o chiude, esce (w e h sono 0)
        if rw == 0 or rh == 0:
            print("\nFine selezione.")
            break

        print(f"\nSelezione rilevata: x={x}, y={y}, w={rw}, h={rh}")
        field_name = input("Nome campo (es. 'cognome') o 'skip' per annullare: ").strip()

        if field_name.lower() == 'skip' or not field_name:
            print("Selezione ignorata.")
            continue

        # Calcolo percentuali (4 decimali di precisione)
        p_x = round(x / w, 4)
        p_y = round(y / h, 4)
        p_w = round(rw / w, 4)
        p_h = round(rh / h, 4)

        zones[field_name] = (p_x, p_y, p_w, p_h)
        print(f"✅ Campo '{field_name}' salvato in memoria.")

        # Disegna rettangolo di conferma sull'immagine (visuale)
        cv2.rectangle(img, (x, y), (x+rw, y+rh), (0, 255, 0), 2)
        cv2.putText(img, field_name, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.destroyAllWindows()

    if zones:
        print("\n\n=== COPIA QUESTO JSON IN local_vision_service.py ===")
        print(json.dumps(zones, indent=4))
        print("====================================================")
    else:
        print("\nNessuna zona selezionata.")

if __name__ == "__main__":
    # Se passi il file come argomento usa quello, altrimenti il default calcolato
    path = sys.argv[1] if len(sys.argv) > 1 else TEMPLATE_PATH
    calibrate_template(path)