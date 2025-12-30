import os
import re
from pathlib import Path

def local_balancer(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    new_lines = []
    i = 0
    modified = False
    
    while i < len(lines):
        line = lines[i]
        
        # If we see an opening docstring that doesn't close on the same line
        if line.strip() == '"""' or line.strip().startswith('"""'):
            if line.strip().count('"""') == 1:
                # Search for a closer within the next 20 lines
                j = i + 1
                found_closer = False
                while j < i + 25 and j < len(lines):
                    if lines[j].strip().endswith('"""'):
                        found_closer = True
                        break
                    if re.match(r'^\s*(def|class|return|yield|if|for|while|import|from)\s+', lines[j]):
                        # We hit code before a closer - this is a broken docstring
                        break
                    j += 1
                
                if not found_closer:
                    # Insert a closer before the code starts or at j
                    print(f"Closing docstring in {file_path} at line {j}")
                    indent_match = re.match(r'^(\s*)', line)
                    indent = indent_match.group(1) if indent_match else "    "
                    lines.insert(j, indent + '"""\n')
                    modified = True
                    # Re-evaluate from here
                    new_lines.append(line)
                    i += 1
                    continue
        
        new_lines.append(line)
        i += 1
        
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    return modified

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if local_balancer(py_file):
            count += 1
    print(f"Locally balanced {count} files.")
