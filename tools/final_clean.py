import os
import re
from pathlib import Path

def final_clean(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # This regex looks for:
    # 1. Any def/class ending with :
    # 2. Potential empty lines/whitespace
    # 3. A docstring that starts with 14 spaces and has "Description of" or similar
    
    # Actually, let's just target the specific mess:
    # \n\s*\n\s*\n\s*"""\n\s+[A-Z].*\n\s*Args:[\s\S]*?"""
    
    bad_doc_pattern = re.compile(r'\n\s*\n\s*\"\"\"\n\s+[A-Z][a-z0-9 ]+ \.\n\n\s+Args:\n(?:\s+.*\n)*?\s+\"\"\"')
    
    new_content = bad_doc_pattern.sub('', content)
    
    # Also remove some specific mess in advanced_models.py
    new_content = re.sub(r'\):(\s*\n){2,}\s+\"\"\"[\s\S]*?\"\"\"', r'):\n        """Docstring."""', new_content)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    for py_file in py_files:
        if final_clean(py_file):
            print(f"Cleaned {py_file}")
