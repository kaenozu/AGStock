import os
import re
from pathlib import Path

def heal_docstrings_v3(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    modified_total = False
    
    # Repeat until no more changes
    while True:
        modified_pass = False
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for def or class
            if re.match(r'^\s*(def|class)\s+', line):
                # Scan ahead to see if we find a stray closing quote
                j = i + 1
                text_lines = []
                found_stray_end = False
                stray_end_idx = -1
                
                while j < i + 15 and j < len(lines):
                    l = lines[j].strip()
                    if not l:
                        j += 1
                        continue
                    if l.startswith('"""'):
                        # If we haven't seen an opening docstring yet
                        # (simplified: if the line exactly matches """ or looks like a closing quote)
                        if not any(tl.strip().startswith('"""') for tl in text_lines):
                            found_stray_end = True
                            stray_end_idx = j
                        break
                    if l.startswith('#'):
                        j += 1
                        continue
                    if re.match(r'^\s*(def|class|if|for|while|with|return|yield|import|from)\s+', lines[j]):
                        # Hit another structural element, stop looking
                        break
                        
                    text_lines.append(lines[j])
                    j += 1
                
                if found_stray_end and text_lines:
                    print(f"Healing broken docstring in {file_path} near line {i+1}")
                    # Find indent of the first text line
                    indent_match = re.match(r'^(\s*)', text_lines[0])
                    indent = indent_match.group(1) if indent_match else "    "
                    
                    # Insert opening quote
                    # We modify 'lines' in place for the next pass
                    lines.insert(i + 1, indent + '"""\n')
                    modified_pass = True
                    modified_total = True
                    # Break current pass to rebuild new_lines correctly or just restart
                    break # Out of while i < len(lines)
            
            new_lines.append(line)
            i += 1
        
        if not modified_pass:
            break
        # If modified, lines is already updated for the next pass

    if modified_total:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    return modified_total

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    unbalanced_files = []
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                if f.read().count('"""') % 2 != 0:
                    unbalanced_files.append(py_file)
        except: pass
        
    count = 0
    for py_file in unbalanced_files:
        if heal_docstrings_v3(py_file):
            count += 1
    print(f"V3 Healed {count} files.")
