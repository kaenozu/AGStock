import os
import re
from pathlib import Path

def final_rescue(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    modified = False
    
    # Pattern 1: Triple quote inside a signature (V3 bug)
    # Match: (something not a colon) \n (indent) """ \n (indent)
    # Replace with: \1 \2
    p1 = re.compile(r'([^:]\n)(\s*)\"\"\"\n(\s*)', re.MULTILINE)
    if p1.search(content):
        # We need to be careful not to remove valid nested strings, but inside a signature it's very rare
        print(f"Fixing Pattern 1 (signature garbage) in {file_path}")
        content = p1.sub(r'\1\3', content)
        modified = True

    # Pattern 2: Text body followed by ending quote after def/class (Missing opening)
    # Match: (def/class line with colon) \n (indent) (Text not starting with quote or #) \n (same indent) """
    p2 = re.compile(r'(:\s*\n)(\s+)([^\"#\s][^\n]*\n)(\s*)\"\"\"', re.MULTILINE)
    if p2.search(content):
        print(f"Fixing Pattern 2 (missing opening) in {file_path}")
        # Insert the opening quote with proper indent
        content = p2.sub(r'\1\2\"\"\"\n\2\3\4\"\"\"', content)
        modified = True

    # Pattern 3: Unwanted indented quotes at top level (Master Repair debris)
    # (Matches what master_repair missed)
    p3 = re.compile(r'^\s+(\"\"\"\n)', re.MULTILINE)
    # This is risky, skip for now.

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    return modified

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if final_rescue(py_file):
            count += 1
    print(f"Rescued {count} files.")
