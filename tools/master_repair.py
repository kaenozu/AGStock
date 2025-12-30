import os
import re
from pathlib import Path

def master_repair(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        # If line starts with 4 or 8 spaces and is a keyword that usually starts at 0
        if re.match(r'^\s+(class|def|import|from|@|#|if __name__)', line):
            # Only de-indent if it's currently indented
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
    count = 0
    for py_file in py_files:
        if master_repair(py_file):
            count += 1
    print(f"Repaired {count} files.")
