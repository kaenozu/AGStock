import os
import re

def get_full_module_map():
    mapping = {}
    for root, _, files in os.walk('src'):
        for f in files:
            if f.endswith('.py'):
                module_name = f[:-3]
                # Map filename to its new absolute src.xxx.yyy path
                full_path = root.replace(os.sep, '.') + '.' + module_name
                if module_name not in mapping:
                    mapping[module_name] = []
                mapping[module_name].append(full_path)
    return mapping

def ultimate_absolute_patch():
    mmap = get_full_module_map()
    print(f"Mapped {len(mmap)} unique module names.")
    
    targets = []
    for root, _, fs in os.walk('src'):
        for f in fs:
            if f.endswith('.py'): targets.append(os.path.join(root, f))
    targets.extend(["app.py", "fully_automated_trader.py", "main.py"])

    for path in targets:
        if not os.path.exists(path): continue
        with open(path, "rb") as f: content = f.read().decode("utf-8", errors="ignore")
        
        new_content = content
        # Pattern 1: from .module import ...
        # Pattern 2: from ..module import ...
        # Pattern 3: from . import module
        
        rel_matches = re.findall(r"from \.+(\w+) import", content)
        for m in rel_matches:
            if m in mmap:
                # Use the first match (heuristic)
                target_abs = mmap[m][0]
                new_content = new_content.replace(f"from .{m} import", f"from {target_abs} import")
                new_content = new_content.replace(f"from ..{m} import", f"from {target_abs} import")
        
        if new_content != content:
            with open(path, "wb") as f: f.write(new_content.encode("utf-8"))
            print(f"Resolved relative imports in: {path}")

if __name__ == "__main__":
    ultimate_absolute_patch()
