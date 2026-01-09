import os

def safe_patch(file_path, replacements):
    if not os.path.exists(file_path): return
    with open(file_path, "rb") as f:
        content = f.read().decode("utf-8", errors="ignore")
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(file_path, "wb") as f:
        f.write(content.encode("utf-8"))
    print(f"Safe Patched: {file_path}")

ENTRY_REPS = [
    ("from src.config import", "from src.core.config import"),
    ("from src.constants import", "from src.core.constants import"),
    ("from src.logger_config import", "from src.core.logger import"),
    ("import src.config as config", "import src.core.config as config"),
]

if __name__ == "__main__":
    safe_patch("app.py", ENTRY_REPS)
    safe_patch("fully_automated_trader.py", ENTRY_REPS)
    print("Core patch done.")
