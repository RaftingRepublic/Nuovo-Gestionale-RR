import shutil
import os
from pathlib import Path

BASE = Path("c:/Users/theob/Desktop/quartoRRgestionale/backend/storage/test_dataset")
INPUT_BASE = BASE / "input"
INPUT_WRONG = INPUT_BASE / "input"
REF_WRONG = INPUT_BASE / "reference"

print(f"Checking {INPUT_WRONG}...")

if INPUT_WRONG.exists():
    print(f"Moving files from {INPUT_WRONG} -> {INPUT_BASE}")
    for item in INPUT_WRONG.iterdir():
        if item.is_file():
            dest = INPUT_BASE / item.name
            if not dest.exists():
                shutil.move(str(item), str(dest))
                print(f"Moved {item.name}")
    try:
        INPUT_WRONG.rmdir() 
        print("Removed empty input/input folder")
    except Exception as e:
        print(f"Failed to remove input/input: {e}")

if REF_WRONG.exists():
    REF_CORRECT = BASE / "reference"
    if not REF_CORRECT.exists():
        print(f"Moving {REF_WRONG} -> {REF_CORRECT}")
        shutil.move(str(REF_WRONG), str(REF_CORRECT))
    else:
        print(f"Ref folder already exists at {REF_CORRECT}")

print("Cleanup complete.")
