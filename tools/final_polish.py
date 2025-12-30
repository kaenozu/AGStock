import os
import subprocess
from pathlib import Path

def final_polish(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    new_lines = []
    modified = False
    for line in lines:
        stripped = line.strip()
        # Fix 1: If it's a comment, lstrip it to 0 or match a sane level 
        # Actually lstripping to 0 is safest for our mess.
        if stripped.startswith('#'):
            new_lines.append(line.lstrip())
            modified = True
        else:
            new_lines.append(line)
            
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    
    # Try to format
    try:
        subprocess.run(["ruff", "format", str(file_path)], check=False, capture_output=True)
    except:
        pass

if __name__ == "__main__":
    count = 0
    py_files = list(Path("src").rglob("*.py"))
    for py_file in py_files:
        final_polish(py_file)
    print("Polished all files.")
