import os
import subprocess

# Critical files mapping for binary restoration
RESTORE_MAP = {
    "src/cache_config.py": "src/data/cache_config.py",
    "src/data_loader.py": "src/data/data_loader.py",
    "src/data_manager.py": "src/data/data_manager.py",
    "src/database_manager.py": "src/data/database_manager.py",
    "src/data_preprocessing.py": "src/data/data_preprocessing.py",
    "src/data_processor.py": "src/data/data_processor.py",
}

def binary_restore():
    print("Restoring binary clean content...")
    for orig, dest in RESTORE_MAP.items():
        try:
            content = subprocess.check_output(["git", "show", f"HEAD:{orig}"])
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(content)
            print(f"Restored binary: {dest}")
        except Exception as e:
            print(f"Failed binary restore {orig}: {e}")

def fix_all_imports():
    print("Fixing all imports in src recursively...")
    REPLACEMENTS = [
        ("from src.config import", "from src.core.config import"),
        ("from src.constants", "from src.core.constants"),
        ("from src.logger_config", "from src.core.logger"),
        ("from src.paper_trader", "from src.trading.paper_trader"),
        ("from src.error_handling", "from src.utils.error_handling"),
        ("from src.data_loader", "from src.data.data_loader"),
        ("from src.data_manager", "from src.data.data_manager"),
        ("from .constants", "from src.core.constants"), # Local relative fix
    ]
    
    for root, dirs, files in os.walk('src'):
        for file in files:
            if not file.endswith('.py'): continue
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                new_content = content
                for old, new in REPLACEMENTS:
                    new_content = new_content.replace(old, new)
                
                if new_content != content:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Patched imports: {path}")
            except Exception as e:
                print(f"Error patching {path}: {e}")

if __name__ == "__main__":
    binary_restore()
    fix_all_imports()
    print("Final recovery step done.")
