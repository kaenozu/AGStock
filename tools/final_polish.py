import os

def final_polish():
    # 1. Fix app.py
    if os.path.exists("app.py"):
        with open("app.py", "r") as f: content = f.read()
        content = content.replace("from src.core.logger import setup_logger", "from src.core.logger import setup_logging")
        content = content.replace("setup_logger()", "setup_logging()")
        with open("app.py", "w") as f: f.write(content)
        print("Fixed app.py naming")

    # 2. Fix data_loader.py imports
    path = "src/data/data_loader.py"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f: content = f.read()
        content = content.replace("from .data_quality_guard", "from src.data.data_quality_guard")
        content = content.replace("from .helpers import", "from src.utils import")
        with open(path, "w", encoding="utf-8") as f: f.write(content)
        print("Fixed data_loader.py imports")

    # 3. Fix data_manager.py relative imports
    path = "src/data/data_manager.py"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f: content = f.read()
        content = content.replace("from .constants", "from src.core.constants")
        content = content.replace("from .errors", "from src.utils.errors")
        with open(path, "w", encoding="utf-8") as f: f.write(content)
        print("Fixed data_manager.py imports")

if __name__ == "__main__":
    final_polish()
