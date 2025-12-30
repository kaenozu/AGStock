import os
import re
from pathlib import Path

def heal_docstrings_v2(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for def or class
        if re.match(r'^\s*(def|class)\s+', line):
            # Scan ahead to see if we find a stray closing quote
            # We look for lines that are not comments/blank/quotes until we hit a """
            j = i + 1
            text_lines = []
            found_stray_end = False
            while j < i + 10 and j < len(lines): # Check up to 10 lines ahead
                l = lines[j].strip()
                if not l:
                    j += 1
                    continue
                if l.startswith('"""'):
                    # If it's a single line """ or starts a docstring
                    # If we haven't seen any opening docstring yet, this might be the end of a broken one
                    if not any(tl.startswith('"""') for tl in text_lines):
                        found_stray_end = True
                    break
                if l.startswith('#'):
                    # Skip comments
                    j += 1
                    continue
                # It's some text
                text_lines.append(lines[j])
                j += 1
            
            if found_stray_end and text_lines:
                # We hit a """ after some text lines, without an opening """
                print(f"Healing broken docstring in {file_path} near line {i+1}")
                new_lines.append(line)
                indent = re.match(r'^(\s*)', text_lines[0]).group(1)
                new_lines.append(indent + '"""\n')
                # The text_lines are already in the correct place, we just need to insert the opening quote
                # Actually, our loop already added 'line'. We will let the normal process add the rest.
                # But we need to skip the i increment to not double-add.
                # It's better to just reconstruct:
                
                # Wait, I'll just insert it into lines and restart or continue.
                lines.insert(i + 1, indent + '"""\n')
                modified = True
                # Start over on this file to be safe
                return heal_docstrings_v2(file_path) if modified else False

        new_lines.append(line)
        i += 1

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    return modified

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    # Only target unbalanced files to avoid false positives
    unbalanced_files = []
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                if f.read().count('"""') % 2 != 0:
                    unbalanced_files.append(py_file)
        except: pass
        
    count = 0
    for py_file in unbalanced_files:
        if heal_docstrings_v2(py_file):
            count += 1
    print(f"V2 Healed {count} files.")
