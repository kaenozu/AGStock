import os

def final_fix():
    print("Final safety fix using Python only...")
    
    # 1. Fix app.py
    if os.path.exists("app.py"):
        with open("app.py", "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        with open("app.py", "w", encoding="utf-8") as f:
            for line in lines:
                if 'st.markdown("日本' in line:
                    f.write('st.markdown("AGStock AI Trading System: Global Market Analysis and Backtesting.")\n')
                elif 'setup_logger' in line:
                    f.write(line.replace('setup_logger', 'setup_logging'))
                else:
                    f.write(line)
        print("Fixed app.py")

    # 2. Fix data_manager.py and data_loader.py
    paths = ["src/data/data_manager.py", "src/data/data_loader.py"]
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            content = content.replace("from .config import settings", "from src.core.config import settings")
            content = content.replace("from .constants import", "from src.core.constants import")
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed {p}")

    # 3. Aggressive cleanup of fully_automated_trader.py
    if os.path.exists("fully_automated_trader.py"):
        with open("fully_automated_trader.py", "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        with open("fully_automated_trader.py", "w", encoding="utf-8") as f:
            for line in lines:
                # Remove any line that still contains broken bytes/chars
                if any(ord(c) > 127 for c in line):
                    # For log or print, just replace content
                    if 'log' in line or 'print' in line or 'st.' in line:
                        line = "".join(c for c in line if ord(c) <= 127)
                f.write(line)
        print("Cleaned fully_automated_trader.py")

if __name__ == "__main__":
    final_fix()
