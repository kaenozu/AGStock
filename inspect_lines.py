
import linecache

files = [
    ("src/ui_automation.py", 126),
    ("src/ui_customizer.py", 26),
    ("src/ui_ghostwriter.py", 68)
]

for filename, lineno in files:
    line = linecache.getline(filename, lineno)
    print(f"File: {filename}, Line {lineno}")
    print(f"Content: {repr(line)}")
    print("-" * 20)
