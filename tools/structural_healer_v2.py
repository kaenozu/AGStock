import os
import re
from pathlib import Path

def structural_healer_v2(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    new_lines = []
    in_class = False
    modified = False
    
    for line in lines:
        stripped = line.strip()
        lstripped = line.lstrip()
        indent = len(line) - len(lstripped)
        
        # Determine if we are at top level
        if indent == 0 and stripped:
            if stripped.startswith('class '):
                in_class = True
            elif stripped.startswith('if __name__') or stripped.startswith('import ') or stripped.startswith('from '):
                in_class = False
            elif stripped.startswith('def '):
                # Is it a top-level function or a misplaced method?
                # Heuristic: if we are in_class, it's likely a method.
                if in_class:
                    line = '    ' + line
                    modified = True
                else:
                    # Stays False
                    pass
            elif stripped.startswith('@') and in_class:
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
        if structural_healer_v2(py_file):
            count += 1
    print(f"Structurally healed V2 {count} files.")
