import os
from dotenv import load_dotenv
import pytesseract

# 1. Carica le variabili d'ambiente
load_dotenv()

# 2. Leggi il percorso dal .env
tess_path = os.getenv("TESSERACT_CMD")

print(f"\n--- DIAGNOSTICA TESSERACT ---")
print(f"1. Percorso letto dal .env: [{tess_path}]")

if not tess_path:
    print("❌ ERRORE: La variabile TESSERACT_CMD è vuota o non esiste nel .env")
    exit()

# 3. Verifica se il file esiste fisicamente
if os.path.exists(tess_path):
    print("✅ Il file esiste nel percorso specificato.")
else:
    print("❌ ERRORE: Il file NON esiste in questo percorso. Controlla il path.")
    # Tentativo di indovinare dove potrebbe essere
    common_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(common_path):
        print(f"💡 SUGGERIMENTO: L'ho trovato qui: {common_path}")
        print("   Copia questo percorso nel tuo .env!")
    exit()

# 4. Prova a configurare ed eseguire Tesseract
try:
    pytesseract.pytesseract.tesseract_cmd = tess_path
    version = pytesseract.get_tesseract_version()
    print(f"✅ Tesseract risponde! Versione installata: {version}")
    print("🚀 Il problema è risolto in questo script. Se il backend fallisce, riavvialo completamente.")
except Exception as e:
    print(f"❌ ERRORE DI ESECUZIONE: {e}")