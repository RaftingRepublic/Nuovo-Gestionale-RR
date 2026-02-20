### backend/tools/check_full_stack.py
import os
import sys

# Disabilita check online e log
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["GLOG_minloglevel"] = "2"

print("⏳ [STEP 1] Verifica importazioni...")

try:
    # 1. Numpy Check
    import numpy as np
    print(f"✅ Numpy: {np.__version__}")
    if int(np.__version__.split('.')[0]) >= 2:
        raise ImportError("Numpy 2.x rilevato!")

    # 2. Paddle Check
    import paddle
    from paddleocr import PaddleOCR
    paddle.set_device('cpu')
    print(f"✅ Paddle Core: {paddle.__version__}")
    
    # Istanza Test (Parametri Aggiornati per v2.7+)
    # FIX: Rimossi parametri deprecati (show_log, use_angle_cls)
    ocr = PaddleOCR(
        use_textline_orientation=False, 
        lang='it', 
        enable_mkldnn=False
    )
    print("✅ PaddleOCR: Istanziato OK")

    # 3. Torch CPU Check
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
    
    # 4. Ultralytics Check
    from ultralytics import YOLO
    print("✅ Ultralytics: Importato OK")

    # 5. GLINER Check
    from gliner import GLiNER
    print("✅ GLINER: Importato OK")

    print("\n🚀 AMBIENTE STABILE. Nessun conflitto DLL rilevato.")

except Exception as e:
    print(f"\n❌ ERRORE CRITICO: {e}")
    sys.exit(1)