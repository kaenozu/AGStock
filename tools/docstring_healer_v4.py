import os
import re
from pathlib import Path

def heal_docstrings_v4(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    modified_total = False
    
    while True:
        modified_pass = False
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for def or class
            if re.match(r'^\s*(def|class)\s+', line):
                # Find the end of the signature (the colon)
                k = i
                found_colon = False
                while k < i + 10 and k < len(lines):
                    if ':' in lines[k]:
                        found_colon = True
                        break
                    k += 1
                
                if not found_colon:
                    i += 1
                    continue
                
                # Scan ahead from k+1 for stray closing quote
                j = k + 1
                text_lines = []
                found_stray_end = False
                
                while j < k + 15 and j < len(lines):
                    l = lines[j].strip()
                    if not l:
                        j += 1
                        continue
                    if l.startswith('"""'):
                        if not any(tl.strip().startswith('"""') for tl in text_lines):
                            found_stray_end = True
                        break
                    if l.startswith('#'):
                        j += 1
                        continue
                    if re.match(r'^\s*(def|class|if|for|while|with|return|yield|import|from)\s+', lines[j]):
                        break
                        
                    text_lines.append(lines[j])
                    j += 1
                
                if found_stray_end and text_lines:
                    print(f"Healing broken docstring in {file_path} near line {k+2}")
                    indent_match = re.match(r'^(\s*)', text_lines[0])
                    indent = indent_match.group(1) if indent_match else "    "
                    
                    lines.insert(k + 1, indent + '"""\n')
                    modified_pass = True
                    modified_total = True
                    break
            
            i += 1
        
        if not modified_pass:
            break

    if modified_total:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    return modified_total

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    # Run on all files because even balanced ones might have the "signature in-between" bug I introduced
    count = 0
    for py_file in py_files:
        if heal_docstrings_v4(py_file):
            count += 1
    print(f"V4 Healed {count} files.")
