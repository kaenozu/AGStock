import os
import re
from pathlib import Path

def resurrect_structure(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    new_lines = []
    modified = False
    in_resurrection = False
    
    for line in lines:
        stripped = line.strip()
        
        # Keywords that should almost never be commented out if they exist
        structural_keywords = [
            r'^#\s*except(\s|$)', 
            r'^#\s*finally(\s|$)', 
            r'^#\s*elif(\s|$)', 
            r'^#\s*else(\s|$)'
        ]
        
        is_structural = any(re.match(kw, stripped) for kw in structural_keywords)
        
        if is_structural:
            print(f"[{file_path}] Resurrecting structural line: {stripped}")
            line = line.replace('# ', '', 1).replace('#', '', 1)
            in_resurrection = True
            modified = True
        elif in_resurrection:
            # If we are resurrecting, keep going until we hit a blank line or a new block
            if not stripped or re.match(r'^[^#\s]', line) or re.match(r'^\s*(def|class|if|for|while|try)\s', line.lstrip('# ')):
                in_resurrection = False
            else:
                # Uncomment the body line too
                line = line.replace('# ', '', 1).replace('#', '', 1)
                modified = True
                
        new_lines.append(line)
        
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    return modified

if __name__ == "__main__":
    count = 0
    py_files = list(Path("src").rglob("*.py"))
    for py_file in py_files:
        if resurrect_structure(py_file):
            count += 1
    print(f"Resurrected structure in {count} files.")
