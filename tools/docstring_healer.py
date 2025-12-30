import os
import re
from pathlib import Path

def heal_docstrings(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Pattern 1: def/class followed by a non-quote text line, then a triple-quote line
        # def func():
        #     Some Text.
        #     """
        if i + 2 < len(lines):
            curr = lines[i]
            next1 = lines[i+1]
            next2 = lines[i+2]
            
            if (re.match(r'^\s*(def|class)\s+', curr) and 
                next1.strip() and not next1.strip().startswith('"""') and not next1.strip().startswith('#') and
                next2.strip() == '"""'):
                
                print(f"Healing pattern 1 in {file_path} at line {i+2}")
                indent = re.match(r'^(\s*)', next1).group(1)
                new_lines.append(curr)
                new_lines.append(indent + '"""\n')
                new_lines.append(next1)
                new_lines.append(next2)
                i += 3
                modified = True
                continue

        # Pattern 2: Triple quote that looks like it's ending something that never started
        # This is harder. Let's just count them and if we find an odd one, try to see if it's misplaced.
        
        new_lines.append(line)
        i += 1

    # Final check for unbalanced quotes in the whole file
    content = "".join(new_lines)
    if content.count('"""') % 2 != 0:
        # If still unbalanced, maybe there's a standalone """ after a def/class
        # def func():
        #     """
        #     (missing closing?)
        
        # Let's try to close any unclosed quotes at the end of functions
        # For now, let's just log it.
        pass

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    return modified

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if heal_docstrings(py_file):
            count += 1
    print(f"Healed {count} files.")
