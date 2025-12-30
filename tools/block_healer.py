import os
import re
from pathlib import Path

def block_healer(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    new_lines = []
    modified = False
    
    for i in range(len(lines)):
        line = lines[i]
        stripped = line.strip()
        
        if i > 0:
            prev_line = lines[i-1].rstrip()
            if prev_line.endswith(':'):
                # The current line SHOULD be indented relative to prev_line
                curr_indent = len(line) - len(line.lstrip())
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                
                if curr_indent <= prev_indent and stripped:
                    # It's at the same level or less, but follows a colon!
                    # Indent it!
                    print(f"[{file_path}] Indenting line {i+1} due to colon on {i}")
                    line = ' ' * (prev_indent + 4) + line.lstrip()
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
        if block_healer(py_file):
            count += 1
    print(f"Block healed {count} files.")
