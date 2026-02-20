import os
import psutil
import time
import sys
import numpy as np

# --- TRUCCO PER WINDOWS ---
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# Silenzia i log
os.environ["GLOG_minloglevel"] = "2"

def print_ram(step):
    # Ottiene l'ID del processo corrente
    pid = os.getpid()
    py = psutil.Process(pid)
    # Calcola la memoria RSS (Resident Set Size) in MB
    memoryUse = py.memory_info().rss / 1024 / 1024
    print(f"📊 RAM [{step}]: {memoryUse:.2f} MB")

print("--- INIZIO TEST MEMORIA LOCALE ---")
print_ram("1. Avvio Python a vuoto")

import torch
print_ram("2. Dopo Import PyTorch")

from paddleocr import PaddleOCR
print("⏳ Caricamento Modelli in RAM...")

# Carichiamo il modello (Simulazione avvio server)
ocr = PaddleOCR(use_angle_cls=False, lang='it', show_log=False, use_gpu=False) 
print_ram("3. Modello Caricato (IDLE)")

print("\n--- AVVIO INFERENZA PESANTE ---")
# Creiamo un'immagine MOLTO grande (4K) per vedere il picco massimo possibile
# 3840 x 2160 pixel
fake_img = np.zeros((2160, 3840, 3), dtype=np.uint8)
print(f"📸 Immagine di test: 4K (3840x2160) - {fake_img.nbytes / 1024 / 1024:.2f} MB grezzi")

start = time.time()
try:
    # Eseguiamo l'OCR
    ocr.ocr(fake_img, cls=False)
    print_ram("4. PICCO DURANTE/DOPO SCAN")
except Exception as e:
    print(f"❌ Errore: {e}")

print(f"\n✅ Finito in {time.time() - start:.2f} secondi")