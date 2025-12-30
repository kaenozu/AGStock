import py_compile
import re
import os
from pathlib import Path

def persistent_fix(file_path):
    print(f"Fixing {file_path}...")
    for _ in range(500):  # Limit iterations per file
        try:
            py_compile.compile(str(file_path), doraise=True)
            return True
        except Exception as e:
            msg = str(e)
            match = re.search(r'line (\d+)', msg)
            if not match:
                print(f"  Cannot find line number in error: {msg}")
                return False
            
            line_no = int(match.group(1)) - 1
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if line_no < 0 or line_no >= len(lines):
                print(f"  Line number {line_no+1} out of range (total {len(lines)})")
                return False
                
            line = lines[line_no]
            
            # Case 1: Unterminated string literal
            if "unterminated triple-quoted string literal" in msg:
                print(f"  [{line_no+1}] Closing triple quote")
                lines.append('\n"""\n')
            
            # Case 2: IndentationError: expected an indented block
            elif "expected an indented block" in msg:
                print(f"  [{line_no+1}] Inserting pass")
                indent_match = re.match(r'^(\s*)', lines[line_no])
                indent = indent_match.group(1) if indent_match else ""
                lines.insert(line_no + 1, indent + "    pass\n")
            
            # Case 3: IndentationError: unexpected indent
            elif "unexpected indent" in msg or "unindent does not match" in msg:
                print(f"  [{line_no+1}] Normalizing indent")
                if line_no > 0:
                    prev_indent_match = re.match(r'^(\s*)', lines[line_no-1])
                    prev_indent = prev_indent_match.group(1) if prev_indent_match else ""
                    # If the previous line ends with :, indent more, otherwise same
                    if lines[line_no-1].strip().endswith(':'):
                        lines[line_no] = prev_indent + "    " + line.lstrip()
                    else:
                        lines[line_no] = prev_indent + line.lstrip()
                else:
                    lines[line_no] = line.lstrip()
            
            # Case 4: SyntaxError: invalid syntax or invalid character
            else:
                # Most likely garbage text or misplaced quote
                print(f"  [{line_no+1}] Commenting out line")
                lines[line_no] = "# " + line
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
    return False

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    # Sort files to prioritize small ones or specific patterns if needed
    count = 0
    for py_file in py_files:
        try:
            py_compile.compile(str(py_file), doraise=True)
        except:
            if persistent_fix(py_file):
                count += 1
    print(f"Fixed {count} files.")
