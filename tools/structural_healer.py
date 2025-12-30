import os
import re
from pathlib import Path

def structural_healer(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    new_lines = []
    in_class = False
    modified = False
    
    for line in lines:
        stripped = line.strip()
        lstripped = line.lstrip()
        indent = len(line) - len(lstripped)
        
        # Determine if we are entering or leaving a class context
        if indent == 0:
            if stripped.startswith('class '):
                in_class = True
            elif stripped.startswith('def ') or stripped.startswith('if __name__'):
                in_class = False
                
        # If we are in a class and see a flattened method or decorator
        if in_class and indent == 0:
            if stripped.startswith('def ') or stripped.startswith('@'):
                # Check it's not the class definition itself
                if not stripped.startswith('class '):
                    line = '    ' + line
                    modified = True
        
        new_lines.append(line)

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    return modified

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if structural_healer(py_file):
            count += 1
    print(f"Structurally healed {count} files.")
