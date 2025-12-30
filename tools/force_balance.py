import os
from pathlib import Path

def force_balance(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    count = content.count('"""')
    if count % 2 != 0:
        print(f"Force balancing {file_path}")
        with open(file_path, 'a', encoding='utf-8') as f:
            # Add a closing quote at the end of the file
            f.write('\n""" # Force Balanced\n')
        return True
    return False

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if force_balance(py_file):
            count += 1
    print(f"Force balanced {count} files.")
