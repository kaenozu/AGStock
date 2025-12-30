import os
import re
from pathlib import Path

def remove_trash_docstrings(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match the specific trash pattern
    # Usually starts with \n and several spaces, then triple quotes, then title, then Args
    pattern = re.compile(r'\n\s*\"\"\"\s+[A-Z][a-z0-9 ]+ \.\s+Args:[\s\S]*?\"\"\"', re.MULTILINE)
    
    new_content = pattern.sub('', content)
    
    # Also remove some other common trash
    trash_patterns = [
        r'\n\s*\"\"\"\s+Init  \.\s+Args:[\s\S]*?\"\"\"',
        r'\n\s*\"\"\"\s+Init  \.\s+"""',
    ]
    
    for p in trash_patterns:
        new_content = re.sub(p, '', new_content)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if remove_trash_docstrings(py_file):
            count += 1
    print(f"Cleaned trash from {count} files.")
