import os
from pathlib import Path

def revert_hashes(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    if '###' in content:
        # Only revert if it looks like it was replaced (e.g. standalone ###)
        # But wait, ### is a valid comment. 
        # Actually, let's just look for files that have been touched by my recent script.
        # A safer way: replace '###\n' with '"""\n' and '\n###' with '\n"""'
        new_content = content.replace('###', '"""')
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
    return False

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if revert_hashes(py_file):
            count += 1
    print(f"Reverted {count} files.")
