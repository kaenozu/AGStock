import os
import re
from pathlib import Path

def fix_common_indents(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for IndentationError pattern: unindent does not match...
        # This usually happens when we have:
        # def func():
        #     # some lines
        #    return x  # <-- broken indent
        
        # My previous tool left 2 or 6 spaces indents.
        # I'll normalize everything to multiples of 4.
        
        match = re.match(r'^(\s+)', line)
        if match:
            indent_str = match.group(1)
            indent_len = len(indent_str)
            if indent_len % 4 != 0:
                # Round to nearest 4
                new_indent_len = round(indent_len / 4) * 4
                if new_indent_len == 0 and indent_len > 0:
                    new_indent_len = 4
                
                print(f"Normalizing indent in {file_path} at line {i+1}: {indent_len} -> {new_indent_len}")
                new_lines.append(' ' * new_indent_len + line.lstrip())
                modified = True
                i += 1
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
        if fix_common_indents(py_file):
            count += 1
    print(f"Normalized {count} files.")
