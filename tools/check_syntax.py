import os
import py_compile
from pathlib import Path

def check_syntax():
    py_files = list(Path("src").rglob("*.py"))
    errors = []
    
    for py_file in py_files:
        try:
            py_compile.compile(str(py_file), doraise=True)
        except Exception as e:
            errors.append((py_file, str(e)))
            
    if not errors:
        print("No syntax errors found!")
    else:
        print(f"Found {len(errors)} files with syntax errors:")
        for file, error in errors:
            print(f"--- {file} ---")
            print(error)
            print()

if __name__ == "__main__":
    check_syntax()
