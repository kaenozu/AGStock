import os
import re
from pathlib import Path

def deindent_top_level(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        # If line starts with from or import or __all__ and is indented, remove indent
        if re.match(r'^\s+(from|import|__all__|_|logger\s*=)', line):
            new_lines.append(line.lstrip())
        else:
            new_lines.append(line)
            
    if new_lines != lines:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    for py_file in py_files:
        deindent_top_level(py_file)
