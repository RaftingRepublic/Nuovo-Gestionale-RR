import os
from datetime import datetime

# --- CONFIGURAZIONE ---
OUTPUT_FILE = "full_project_dump.txt"

# Cartelle da IGNORARE (non vogliamo vedere le librerie)
IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", 
    "node_modules", ".quasar", "dist", "build", ".vscode", ".idea",
    "coverage", ".pytest_cache"
}

# Estensioni di file da INCLUDERE (solo codice sorgente rilevante)
INCLUDE_EXTENSIONS = {
    ".py", ".js", ".ts", ".vue", ".json", ".html", ".css", ".scss", 
    ".md", ".yml", ".yaml", ".ini", ".env.example"
}

# File specifici da IGNORARE (se necessario)
IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "full_project_dump.txt", "generate_dump.py"
}

def is_ignored(path, is_dir=False):
    name = os.path.basename(path)
    if is_dir:
        return name in IGNORE_DIRS
    return name in IGNORE_FILES

def get_file_structure(start_path):
    structure = ""
    for root, dirs, files in os.walk(start_path):
        # Modifica 'dirs' in-place per saltare le cartelle ignorate
        dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d), is_dir=True)]
        
        level = root.replace(start_path, '').count(os.sep)
        indent = ' ' * 4 * (level)
        structure += f"{indent}{os.path.basename(root)}/\n"
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if not is_ignored(os.path.join(root, f)) and os.path.splitext(f)[1] in INCLUDE_EXTENSIONS:
                structure += f"{subindent}{f}\n"
    return structure

def write_dump():
    start_path = "."
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        # Header
        out.write(f"RAFTING REPUBLIC - PROJECT DUMP\n")
        out.write(f"GENERATED: {timestamp}\n")
        out.write("="*50 + "\n\n")

        # 1. Struttura del progetto
        print("Scansione della struttura...")
        out.write("=== PROJECT STRUCTURE ===\n")
        out.write(get_file_structure(start_path))
        out.write("\n" + "="*50 + "\n\n")

        # 2. Contenuto dei file
        print("Estrazione del codice sorgente...")
        out.write("=== FILE CONTENTS ===\n\n")
        
        for root, dirs, files in os.walk(start_path):
            # Salta cartelle ignorate
            dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d), is_dir=True)]
            
            for file in files:
                if is_ignored(file):
                    continue
                    
                _, ext = os.path.splitext(file)
                if ext in INCLUDE_EXTENSIONS:
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, start_path)
                    
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            
                        out.write(f"<FILE_START path=\"{relative_path}\">\n")
                        out.write(content)
                        # Assicura una newline alla fine se manca
                        if content and not content.endswith('\n'):
                            out.write('\n')
                        out.write(f"<FILE_END>\n\n")
                        print(f"Incluso: {relative_path}")
                    except Exception as e:
                        print(f"Errore leggendo {relative_path}: {e}")
                        out.write(f"<FILE_ERROR path=\"{relative_path}\">\n{e}\n<FILE_END>\n\n")

    print(f"\nCompletato! File generato: {OUTPUT_FILE}")

if __name__ == "__main__":
    write_dump()