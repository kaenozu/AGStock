import os
import re

def get_file_map():
    mapping = {}
    for root, _, files in os.walk('src'):
        for f in files:
            if f.endswith('.py'):
                module_path = root.replace(os.sep, '.') + '.' + f[:-3]
                mapping[f[:-3]] = module_path
    return mapping

def super_patch():
    file_map = get_file_map()
    print(f"Mapped {len(file_map)} modules.")
    
    # Files to patch
    targets = []
    for root, _, fs in os.walk('src'):
        for f in fs:
            if f.endswith('.py'): targets.append(os.path.join(root, f))
    targets.extend(["app.py", "fully_automated_trader.py", "main.py"])

    for path in targets:
        if not os.path.exists(path): continue
        with open(path, "rb") as f: content = f.read().decode("utf-8", errors="ignore")
        
        # Regex to find 'from .module' or 'from . import module'
        # This is simplified but covers most cases we broke
        new_content = content
        
        # Find 'from .X import' and replace with absolute
        matches = re.findall(r"from \.(\w+) import", content)
        for m in matches:
            if m in file_map:
                new_content = new_content.replace(f"from .{m} import", f"from {file_map[m]} import")
        
        if new_content != content:
            with open(path, "wb") as f: f.write(new_content.encode("utf-8"))
            print(f"Super Patched: {path}")

if __name__ == "__main__":
    super_patch()
