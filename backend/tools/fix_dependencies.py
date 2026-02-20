import subprocess
import sys
import os

def install(package):
    print(f"📦 Installazione/Downgrade: {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_and_fix():
    print("🔧 AVVIO RIPARAZIONE AMBIENTE PER GLINER...")
    
    # 1. Downgrade huggingface_hub per compatibilità GLiNER
    # La versione 0.23+ ha rimosso 'is_offline_mode', rompendo gliner attuale.
    # Forziamo una versione stabile precedente.
    try:
        import huggingface_hub
        print(f"   Versione attuale huggingface_hub: {huggingface_hub.__version__}")
    except ImportError:
        print("   huggingface_hub non trovato.")

    print("   👉 Eseguo downgrade a huggingface_hub==0.22.2 (Versione sicura)...")
    install("huggingface_hub==0.22.2")

    # 2. Reinstalliamo GLiNER per sicurezza
    print("   👉 Aggiorno GLiNER...")
    install("gliner>=0.2.0")

    # 3. Pre-scaricamento del modello (evita timeout al primo avvio)
    print("   ⬇️ Pre-scaricamento modello 'urchade/gliner_medium-v2.1'...")
    try:
        from gliner import GLiNER
        model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")
        print("   ✅ Modello scaricato e caricato correttamente in cache.")
    except Exception as e:
        print(f"   ❌ Errore download modello: {e}")
        print("   Assicurati di essere connesso a internet.")

    print("\n✅ OPERAZIONE COMPLETATA.")
    print("   Ora riavvia il server backend con: uvicorn main:app --reload")

if __name__ == "__main__":
    check_and_fix()