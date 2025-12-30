import os
import re
from pathlib import Path

def fix_indentation(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified = False
    new_lines = []
    
    for i in range(len(lines)):
        line = lines[i]
        
        # Check if previous line was a def/class and current is a docstring
        if i > 0:
            prev_line = lines[i-1]
            prev_match = re.match(r'^(\s*)(def|class)\s+', prev_line)
            curr_match = re.match(r'^(\s*)("""[\s\S]*?""")', line.strip()) # This is tricky for multiline
            
            # Simpler check: if this line starts with whitespace and triple quotes
            # and follows a def/class
            if prev_match and line.strip().startswith('"""'):
                parent_indent = len(prev_match.group(1))
                expected_indent = parent_indent + 4
                
                curr_indent_match = re.match(r'^(\s*)', line)
                curr_indent = len(curr_indent_match.group(1)) if curr_indent_match else 0
                
                if curr_indent != expected_indent:
                    print(f"Fixing indent in {file_path} at line {i+1}: {curr_indent} -> {expected_indent}")
                    new_lines.append(' ' * expected_indent + line.lstrip())
                    modified = True
                    continue
        
        new_lines.append(line)

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    for py_file in py_files:
        fix_indentation(py_file)
