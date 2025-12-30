import os
import re
from pathlib import Path

def debris_remover(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Remove definitely-garbage docstrings
    # 1. "Docstring."
    content = re.sub(r'\"\"\"Docstring\.\"\"\"', 'pass', content)
    
    # 2. Large blocks of Args/Returns/Description that are just placeholders
    # Match: """ \n indent (Text) \n indent Args: \n ... \n indent """
    bad_doc_pattern = re.compile(
        r'\"\"\"\s*\n\s*[A-Z][a-z]+ [A-Z][a-z]+(\s+[A-Z][a-z]+)?\.\s*\n\s+Args:\s*\n.*?\n\s+\"\"\"', 
        re.DOTALL
    )
    content = bad_doc_pattern.sub('pass', content)
    
    # 3. Stray "Force Balanced" quotes
    content = re.sub(r'\"\"\" # Force Balanced', '', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if debris_remover(py_file):
            count += 1
    print(f"Cleaned debris from {count} files.")
