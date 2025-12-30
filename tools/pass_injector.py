import os
import re
from pathlib import Path

def inject_pass(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    new_lines = []
    modified = False
    
    for i in range(len(lines)):
        line = lines[i]
        new_lines.append(line)
        
        if line.strip().endswith(':'):
            # Check if it's a block-starting line
            # Look at next lines
            is_empty = True
            parent_indent = len(line) - len(line.lstrip())
            
            j = i + 1
            while j < len(lines):
                next_l = lines[j]
                stripped_next = next_l.strip()
                if not stripped_next:
                    j += 1
                    continue
                
                # If it's a comment, we keep looking (unless it's indented)
                next_indent = len(next_l) - len(next_l.lstrip())
                if stripped_next.startswith('#'):
                    if next_indent > parent_indent:
                        is_empty = False
                        break
                    j += 1
                    continue
                
                if next_indent > parent_indent:
                    is_empty = False
                    break
                else:
                    # Found a line at the same or less indent!
                    break
                j += 1
            
            if is_empty:
                print(f"[{file_path}] Injecting pass after line {i+1}")
                indent = ' ' * (parent_indent + 4)
                new_lines.append(indent + "pass\n")
                modified = True
                
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    return modified

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if inject_pass(py_file):
            count += 1
    print(f"Injected pass in {count} files.")
