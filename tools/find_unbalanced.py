import os
from pathlib import Path

def find_unbalanced_quotes():
    py_files = list(Path("src").rglob("*.py"))
    unbalanced = []
    
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Count triple quotes
                count = content.count('"""')
                if count % 2 != 0:
                    unbalanced.append((py_file, count))
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
            
    if not unbalanced:
        print("All files have balanced triple quotes.")
    else:
        print(f"Found {len(unbalanced)} files with unbalanced triple quotes:")
        for file, count in unbalanced:
            print(f"{file}: {count}")

if __name__ == "__main__":
    find_unbalanced_quotes()
