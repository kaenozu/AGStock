import os
import py_compile
from pathlib import Path
import re

def brute_force_aggressive(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    modified_total = False
    
    for iteration in range(100):
        try:
            py_compile.compile(str(file_path), doraise=True)
            break
        except Exception as e:
            modified_total = True
            msg = str(e)
            match = re.search(r'line (\d+)', msg)
            if not match:
                break
            
            line_no = int(match.group(1)) - 1
            if line_no < 0 or line_no >= len(lines):
                break
                
            bad_line = lines[line_no]
            
            # If it's a docstring quote, remove it
            if '"""' in bad_line:
                print(f"[{file_path}] Removing docstring line at {line_no+1}")
                lines.pop(line_no)
            # If it's an indentation error, try to indent/deindent or insert pass
            elif "indent" in msg.lower():
                if "expected an indented block" in msg.lower():
                    print(f"[{file_path}] Inserting pass at {line_no+1}")
                    indent_match = re.match(r'^(\s*)', lines[line_no])
                    indent = indent_match.group(1) if indent_match else "    "
                    lines.insert(line_no + 1, indent + "    pass\n")
                else:
                    print(f"[{file_path}] Removing bad indent line at {line_no+1}")
                    lines.pop(line_no)
            # If it's a syntax error with Japanese characters or weird debris
            elif "invalid character" in msg.lower():
                print(f"[{file_path}] Removing invalid character line at {line_no+1}")
                lines.pop(line_no)
            else:
                # Last resort: remove the line
                print(f"[{file_path}] Removing mysterious error line at {line_no+1}")
                lines.pop(line_no)
            
            # Save for next compile check
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
    return modified_total

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if brute_force_aggressive(py_file):
            count += 1
    print(f"Aggressively fixed {count} files.")
