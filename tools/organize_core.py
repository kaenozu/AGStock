import os
import shutil

def organize_core_with_proxies():
    print("Organizing core with proxies...")
    os.makedirs("src/core", exist_ok=True)
    
    mapping = {
        "src/config.py": "src/core/config.py",
        "src/constants.py": "src/core/constants.py",
        "src/logger_config.py": "src/core/logger.py",
        "src/types.py": "src/core/types.py",
        "src/schemas.py": "src/core/schemas.py",
    }
    
    for orig, dest in mapping.items():
        if os.path.exists(orig):
            # Move content to core
            shutil.copy2(orig, dest)
            print(f"Copied {orig} to {dest}")
            
            # Replace original with proxy
            module_path = dest.replace("/", ".").replace(".py", "")
            with open(orig, "w", encoding="utf-8") as f:
                f.write(f"from {module_path} import *\n")
            print(f"Created proxy at {orig}")

if __name__ == "__main__":
    organize_core_with_proxies()
