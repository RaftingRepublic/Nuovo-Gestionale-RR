import google.generativeai as genai
import os
from dotenv import load_dotenv

# 1. Carica la chiave segreta
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERRORE: Chiave non trovata nel file .env")
else:
    # 2. Configura Google
    genai.configure(api_key=api_key)

    print("\n--- LISTA DEI MODELLI CHE PUOI USARE ---")
    try:
        # 3. Chiede a Google la lista ufficiale
        found_any = False
        for m in genai.list_models():
            # Filtriamo solo quelli che generano testo/immagini
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ {m.name}")
                found_any = True
        
        if not found_any:
            print("Nessun modello trovato. La chiave potrebbe non avere permessi.")
            
    except Exception as e:
        print(f"ERRORE DI CONNESSIONE: {e}")