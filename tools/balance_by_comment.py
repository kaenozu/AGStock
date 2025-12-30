import os
import re
from pathlib import Path

def delete_unbalanced_docstrings(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    if content.count('"""') % 2 != 0:
        print(f"[{file_path}] Deleting all triple quotes to balance.")
        # Replace all triple quotes with '#' to turn them into comments
        content = content.replace('"""', '###')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if delete_unbalanced_docstrings(py_file):
            count += 1
    print(f"Balanced {count} files by commenting out quotes.")
