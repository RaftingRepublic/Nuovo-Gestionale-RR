import time
import os
import sys
import numpy as np

# --- TRUCCO PER WINDOWS ---
# Risolve il conflitto "OMP: Error #15: Initializing libiomp5md.dll"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# Silenzia i log inutili
os.environ["GLOG_minloglevel"] = "2"

def cronometro(step, start_time):
    now = time.time()
    elapsed = now - start_time
    print(f"⏱️  {step}: {elapsed:.4f} secondi")
    return now

print("--- INIZIO TEST LOCALE ---")
global_start = time.time()
last_checkpoint = global_start

# 1. Caricamento Librerie
import torch
last_checkpoint = cronometro("Import PyTorch", last_checkpoint)

from paddleocr import PaddleOCR
# Usa i parametri compatibili con l'ultima versione
ocr = PaddleOCR(use_angle_cls=False, lang='it', show_log=False, use_gpu=False) 
last_checkpoint = cronometro("Inizializzazione PaddleOCR (Load Model)", last_checkpoint)

# 2. Creazione Immagine Finta (HD)
# Simuliamo una foto 1920x1080 (Full HD)
fake_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
print("\n--- AVVIO INFERENZA (Simulazione Foto Full HD) ---")

# 3. Inferenza Reale
start_inference = time.time()
try:
    result = ocr.ocr(fake_img, cls=False)
    end_inference = time.time()
    print(f"✅ INFERENZA COMPLETATA IN: {end_inference - start_inference:.4f} secondi")
except Exception as e:
    print(f"❌ Errore durante l'inferenza: {e}")

print("\n--- RIEPILOGO ---")
print(f"Tempo Totale Script: {time.time() - global_start:.4f} secondi")
