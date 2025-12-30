import os
import re
from pathlib import Path

def shred_trash(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    new_lines = []
    i = 0
    modified = False
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 1. Fix orphaned signatures: 'def name(\n) -> type:'
        if stripped.startswith('def ') and stripped.endswith('('):
            if i + 1 < len(lines) and lines[i+1].strip().startswith(')') and '->' in lines[i+1]:
                print(f"[{file_path}] Joining orphaned signature at {i+1}")
                combined = line.rstrip() + lines[i+1].lstrip()
                new_lines.append(combined)
                i += 2
                modified = True
                continue
        
        # 2. Block removal: detect the placeholder docstrings
        # Matches: """ \n description \n Args: ... \n """
        if '"""' in line:
            # Check if it's the start of a garbage block
            j = i + 1
            is_garbage = False
            while j < i + 15 and j < len(lines):
                s = lines[j].strip()
                if 'Args:' in s or 'Returns:' in s or 'Description of' in s or 'Docstring.' in s:
                    is_garbage = True
                if '"""' in lines[j]:
                    break
                # If we hit logic, it's NOT garbage
                if re.match(r'^\s*(def|class|if|for|while|import|from|return)\s+', lines[j]):
                    is_garbage = False
                    break
                j += 1
            
            if is_garbage and j < len(lines) and '"""' in lines[j]:
                print(f"[{file_path}] Shredding garbage docstring lines {i+1}-{j+1}")
                # Replace with '    pass\n' if it's inside a def/class to avoid empty blocks
                indent_match = re.match(r'^(\s*)', line)
                indent = indent_match.group(1) if indent_match else "    "
                new_lines.append(indent + 'pass  # Docstring removed\n')
                i = j + 1
                modified = True
                continue

        new_lines.append(line)
        i += 1

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    return modified

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if shred_trash(py_file):
            count += 1
    print(f"Shredded trash in {count} files.")
