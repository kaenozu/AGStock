import os
import re
from pathlib import Path

def fix_corrupted_docstrings(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    
    # Fix 1: Docstring inside def(...) before the colon
    # Pattern: def name( [misplaced doc] [params] ):
    def_pattern = re.compile(r'(def\s+\w+\s*\()(\s*\"\"\"[\s\S]*?\"\"\"\s*)([\s\S]*?\):)', re.MULTILINE)
    new_content = def_pattern.sub(r'\1\3\n        \2', new_content)
    
    # Fix 2: Docstring after a one-liner def or class
    # Pattern: def func(params): pass\n    """doc"""
    # Or: class Mock: pass\n    """doc"""
    one_liner_pattern = re.compile(r'((\s*)(?:def|class)\s+[\s\S]*?:\s*[^\n]+)\n\s*(\"\"\"[\s\S]*?\"\"\")', re.MULTILINE)
    new_content = one_liner_pattern.sub(r'\1\n\2    \3', new_content)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

if __name__ == "__main__":
    # Identified files with errors (from check_syntax.py output)
    # I'll just scan the whole src directory this time to be sure.
    py_files = list(Path("src").rglob("*.py"))
    
    fixed_count = 0
    for py_file in py_files:
        if fix_corrupted_docstrings(py_file):
            print(f"Fixed {py_file}")
            fixed_count += 1
            
    print(f"Total fixed: {fixed_count}")
