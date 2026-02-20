import os
import platform
import sys
import subprocess

def check_cpu_instructions():
    print("--- DIAGNOSTICA CPU E AMBIENTE ---")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {sys.version.split()[0]}")
    
    # Tentativo di rilevamento CPU
    try:
        if platform.system() == "Windows":
            command = "wmic cpu get name"
            output = subprocess.check_output(command, shell=True).decode().strip().split('\n')[1]
            print(f"CPU Model: {output}")
        else:
            # Linux/Mac fallback
            with open('/proc/cpuinfo') as f:
                for line in f:
                    if "model name" in line:
                        print(f"CPU Model: {line.split(':')[1].strip()}")
                        break
    except Exception as e:
        print(f"CPU Model detection failed: {e}")

    print("\n--- CONSIGLIO INSTALLAZIONE PADDLE ---")
    print("Se la tua CPU è Intel Core (4a gen o superiore) o AMD Ryzen recente -> Supporta AVX.")
    print("Se sei su una VM Windows Server vecchia o CPU Celeron/Pentium vecchi -> Potrebbe NON supportare AVX.")
    print("\nREGOLA D'ORO:")
    print("1. Prova prima l'installazione STANDARD (MKL).")
    print("2. Esegui lo script 'verify_paddle.py' (che creeremo tra poco).")
    print("3. Se ottieni errore 'Illegal Instruction' o crash, passa alla versione NO-AVX.")

if __name__ == "__main__":
    check_cpu_instructions()