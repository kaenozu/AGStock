import os

def fix_data_loader():
    path = "src/data/data_loader.py"
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    # Precise replacements
    content = content.replace("from .config import", "from src.core.config import")
    content = content.replace("from .constants import", "from src.core.constants import")
    content = content.replace("from .data_manager import", "from src.data.data_manager import")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched data_loader.py")

if __name__ == "__main__":
    fix_data_loader()
