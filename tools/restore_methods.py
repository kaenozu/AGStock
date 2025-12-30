import os
import re
from pathlib import Path

def restore_methods(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    new_lines = []
    in_class = False
    class_indent = 0
    modified = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            new_lines.append(line)
            continue
            
        # Detect class
        if stripped.startswith('class '):
            in_class = True
            # Get indent of class (though usually 0)
            class_indent = len(line) - len(line.lstrip())
            new_lines.append(line)
            continue
            
        # Detect top-level def that looks like a method
        if stripped.startswith('def ') and (line.startswith('def ') or line.startswith(' ' * class_indent + 'def ')):
            current_indent = len(line) - len(line.lstrip())
            if in_class and current_indent <= class_indent:
                # Check if it's a method: has (self or (cls
                if '(self' in stripped or '(cls' in stripped:
                    print(f"[{file_path}] Re-indenting method: {stripped[:30]}...")
                    line = ' ' * (class_indent + 4) + line.lstrip()
                    modified = True
            elif not in_class:
                # If we see a def at 0 spaces and no self, it's just a regular function
                pass
        
        # If we are inside a class, and we see something at 0 spaces that isn't a class/def
        # it might be logic that was flattened.
        elif in_class and line.startswith(tuple('abcdefghijklmnopqrstuvwxyz')):
             # This is a bit risky but often true for the broken codebase
             if not line.startswith(('import ', 'from ', 'class ', 'def ')):
                 print(f"[{file_path}] Re-indenting flattened logic: {line[:20]}...")
                 line = '    ' + line
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
        if restore_methods(py_file):
            count += 1
    print(f"Restored methods in {count} files.")
