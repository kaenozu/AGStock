import os
import py_compile
from pathlib import Path
import re

def brute_force_fix(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    
    for _ in range(50): # More passes
        try:
            py_compile.compile(str(file_path), doraise=True)
            break
        except Exception as e:
            import re
            match = re.search(r'line (\d+)', str(e))
            if not match:
                break
            
            line_no = int(match.group(1)) - 1
            if line_no < len(lines):
                bad_line = lines[line_no]
                
                # If it's an indentation error "expected an indented block", add a pass
                if "expected an indented block" in str(e).lower():
                    print(f"Adding pass to {file_path} at line {line_no+1}")
                    # Find the parent indent
                    parent_line = lines[line_no]
                    indent_match = re.match(r'^(\s*)', parent_line)
                    indent = indent_match.group(1) if indent_match else ""
                    lines.insert(line_no + 1, indent + "    pass\n")
                    modified = True
                elif '"""' in bad_line:
                    print(f"Removing bad docstring from {file_path} at line {line_no+1}")
                    lines.pop(line_no)
                    modified = True
                else:
                    # Try to see if next line is a docstring debris
                    if line_no + 1 < len(lines) and '"""' in lines[line_no+1]:
                         lines.pop(line_no+1)
                         modified = True
                    else:
                        break
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            else:
                break
                
    return modified

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    for py_file in py_files:
        brute_force_fix(py_file)
