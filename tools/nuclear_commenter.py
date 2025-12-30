import os
import re
from pathlib import Path

def nuclear_comment(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    new_lines = []
    in_docstring = False
    modified = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Detect start of docstring
        # Note: This is naive but for our broken codebase it might be best.
        if '"""' in line:
            # Toggle state
            # If we see multiple on one line, it handles it.
            quotes = line.count('"""')
            
            # Special case: line is JUST an opening quote or starts with it
            # We comment it out anyway.
            new_lines.append('# ' + line)
            if quotes % 2 != 0:
                in_docstring = not in_docstring
            modified = True
            continue
            
        if in_docstring:
            # We are inside a docstring.
            # Safety check: if we hit a def/class/import at the start of a line (0 spaces),
            # the docstring MUST have been broken. Stop commenting.
            if re.match(r'^(def |class |import |from |@|if __name__)', line):
                print(f"[{file_path}] Found code but was in docstring! Force closing at {i+1}")
                in_docstring = False
                new_lines.append(line)
            else:
                new_lines.append('# ' + line)
                modified = True
        else:
            new_lines.append(line)
            
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    return modified

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if nuclear_comment(py_file):
            count += 1
    print(f"Nuclear Commented {count} files.")
