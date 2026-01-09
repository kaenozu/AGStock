import os

def reset_imports():
    REPS = [
        ("from src.ui.simple_dashboard", "from src.simple_dashboard"),
        ("from src.data.data_loader", "from src.data_loader"),
        ("from src.trading.fully_automated_trader", "from src.fully_automated_trader"),
    ]
    for p in ["app.py", "fully_automated_trader.py"]:
        if not os.path.exists(p): continue
        with open(p, "rb") as f: c = f.read().decode("utf-8", errors="ignore")
        for old, new in REPS: c = c.replace(old, new)
        with open(p, "wb") as f: f.write(c.encode("utf-8"))

if __name__ == "__main__":
    reset_imports()
