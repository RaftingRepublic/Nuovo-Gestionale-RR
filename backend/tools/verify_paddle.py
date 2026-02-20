import os
import sys
import time
import numpy as np

# Disabilitiamo i log di debug e il check online
os.environ["GLOG_minloglevel"] = "2"
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

print("⏳ [STEP 1] Avvio test di importazione librerie...")

try:
    # 1. Verifica Numpy
    print(f"✅ Numpy importato. Versione: {np.__version__}")
    if int(np.__version__.split('.')[0]) >= 2:
        raise ImportError("❌ ERRORE FATALE: Numpy versione 2.x rilevata!")

    # 2. Import Core e Toolkit
    import paddle
    import paddleocr
    from paddleocr import PaddleOCR
    
    print(f"✅ Paddle Core: {paddle.__version__}")
    print(f"✅ Paddle OCR: {paddleocr.__version__}")

    # 3. Test Inferenza Dummy
    print("\n⏳ [STEP 2] Avvio Inferenza Dummy (Configurazione Sicura)...")

    # CONFIGURAZIONE SICURA PER PADDLEOCR v3.3.3
    ocr = PaddleOCR(
        use_textline_orientation=False, # Aggiornato da use_angle_cls
        lang='it', 
        use_gpu=False,
        enable_mkldnn=False             # Disabilitato per stabilità massima
    )
    
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    start = time.time()
    result = ocr.ocr(img, cls=False)
    end = time.time()
    
    print(f"✅ Inferenza completata in {end - start:.4f} secondi.")
    print("\n🎉 SISTEMA PRONTO E STABILE.")

except Exception as e:
    print(f"\n❌ ERRORE RUNTIME: {e}")
    sys.exit(1)