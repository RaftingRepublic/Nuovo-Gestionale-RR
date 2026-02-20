import subprocess
import sys
import os

def install(package):
    print(f"📦 Installazione: {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--no-cache-dir"])
        print(f"✅ {package} installato.")
    except Exception as e:
        print(f"❌ Errore installazione {package}: {e}")

def fix_environment():
    print("\n☢️  RAFTING REPUBLIC - AI STACK REPAIR (V5 - CLEAN ORDER)")
    print("=========================================================")
    print("Obiettivo: Risolvere RuntimeError: Numpy is not available")

    # 1. RIMOZIONE TOTALE
    print("\n1️⃣  Rimozione totale librerie AI...")
    pkgs = [
        "ultralytics", "gliner", "paddleocr", "paddlepaddle",
        "torch", "torchvision", "torchaudio", 
        "numpy", "scipy", "pandas", "huggingface-hub"
    ]
    subprocess.call([sys.executable, "-m", "pip", "uninstall", "-y"] + pkgs)

    # 2. INSTALLAZIONE NUMPY (Base Solida)
    print("\n2️⃣  Installazione NumPy 1.26.4...")
    # Versione gold standard per compatibilità
    install("numpy==1.26.4")

    # 3. INSTALLAZIONE PYTORCH CPU (Minimale)
    print("\n3️⃣  Installazione PyTorch 2.3.1 CPU...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "torch==2.3.1", "torchvision==0.18.1", "torchaudio==2.3.1",
            "--index-url", "https://download.pytorch.org/whl/cpu"
        ])
        print("✅ PyTorch installato.")
    except Exception as e:
        print(f"❌ Errore PyTorch: {e}")
        return

    # 4. INSTALLAZIONE PADDLE (Senza rompere NumPy)
    print("\n4️⃣  Installazione Paddle...")
    install("paddlepaddle==2.6.1")
    install("paddleocr>=2.7.0")
    # Forziamo protobuf compatibile per Paddle
    install("protobuf==3.20.3")

    # 5. INSTALLAZIONE ULTRALYTICS & GLINER
    print("\n5️⃣  Installazione YOLO & GLiNER...")
    install("ultralytics>=8.2.0")
    install("huggingface-hub>=0.23.0")
    install("gliner")

    # 6. VERIFICA FINALE
    print("\n6️⃣  Test Finale...")
    try:
        import numpy
        print(f"   ✅ NumPy: {numpy.__version__}")
        
        import torch
        # Verifica se PyTorch vede NumPy
        t = torch.tensor([1, 2, 3])
        n = t.numpy()
        print(f"   ✅ PyTorch -> NumPy bridge OK: {n}")
        
        from gliner import GLiNER
        print("   ✅ GLiNER importato.")
        
        print("\n🚀 RIPARAZIONE COMPLETATA. Riavvia il server.")
        
    except ImportError as e:
        print(f"❌ Errore Import: {e}")
    except RuntimeError as e:
        print(f"❌ Errore Runtime: {e}")
    except Exception as e:
        print(f"❌ Errore Generico: {e}")

if __name__ == "__main__":
    fix_environment()