import os
import re

def build_map():
    m = {}
    for root, _, files in os.walk('src'):
        for f in files:
            if f.endswith('.py'):
                name = f[:-3]
                full = root.replace(os.sep, '.') + '.' + name
                if name not in m: m[name] = []
                m[name].append(full)
    return m

def fix_file(path, mmap):
    with open(path, 'rb') as f:
        content = f.read().decode('utf-8', errors='ignore')
    
    new_content = content
    # Fix 'from src.module'
    for name, locations in mmap.items():
        best_loc = locations[0]
        # Avoid self-referencing loop
        if best_loc in path.replace(os.sep, '.'): continue
        
        new_content = new_content.replace(f"from src.{name} import", f"from {best_loc} import")
        new_content = new_content.replace(f"import src.{name} as", f"import {best_loc} as")
        # Relative fixes
        new_content = new_content.replace(f"from .{name} import", f"from {best_loc} import")
    
    # Global Infra fixes
    new_content = new_content.replace("from src.config", "from src.core.config")
    new_content = new_content.replace("from src.constants", "from src.core.constants")
    new_content = new_content.replace("from src.logger_config", "from src.core.logger")
    
    if new_content != content:
        with open(path, 'wb') as f: f.write(new_content.encode('utf-8'))
        return True
    return False

if __name__ == "__main__":
    mmap = build_map()
    print("Fixing all imports...")
    targets = ["app.py", "fully_automated_trader.py"]
    for root, _, fs in os.walk('src'):
        for f in fs:
            if f.endswith('.py'): targets.append(os.path.join(root, f))
    
    count = 0
    for t in targets:
        if os.path.exists(t):
            if fix_file(t, mmap): count += 1
    print(f"Fixed {count} files.")
