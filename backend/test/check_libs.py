# backend/check_libs.py
try:
    import gliner
    print("✅ GLINER trovato! Versione:", gliner.__version__)
except ImportError as e:
    print("❌ GLINER NON trovato:", e)

try:
    import paddleocr
    print("✅ PaddleOCR trovato!")
except ImportError as e:
    print("❌ PaddleOCR NON trovato:", e)