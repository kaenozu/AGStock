import os
import re
from pathlib import Path

def aggressive_deindent(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    new_lines = []
    in_bracket = 0
    modified = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            new_lines.append(line)
            continue
            
        current_indent = len(line) - len(line.lstrip())
        
        # Check if we are inside a bracket block (approximate)
        in_bracket += (line.count('(') + line.count('[') + line.count('{'))
        in_bracket -= (line.count(')') + line.count(']') + line.count('}'))

        if i > 0:
            # Find last non-blank line
            prev_idx = i - 1
            while prev_idx >= 0 and not lines[prev_idx].strip():
                prev_idx -= 1
            
            if prev_idx >= 0:
                prev_line = lines[prev_idx]
                prev_stripped = prev_line.strip()
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                
                # If current line is indented relative to previous block,
                # but previous line did NOT end with a colon AND we are at top level or mismatched
                if current_indent > 0 and not prev_stripped.endswith(':') and in_bracket <= 0:
                    # If it's a comment, it might be okay, but for our mess, let's lstrip it.
                    # UNLESS the previous line was also indented (then they are part of a block that just lacks an opener)
                    if prev_indent == 0:
                        print(f"[{file_path}] De-indenting orphaned line {i+1}")
                        line = line.lstrip()
                        modified = True
                        
        new_lines.append(line)
        
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    return modified

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if aggressive_deindent(py_file):
            count += 1
    print(f"Aggressively de-indented {count} files.")
