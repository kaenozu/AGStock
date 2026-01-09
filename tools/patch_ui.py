import os

REPS = [
    ("from src.ui_renderers", "from src.ui.ui_renderers"),
    ("from src.ui_components", "from src.ui.ui_components"),
    ("from src.simple_dashboard", "from src.ui.simple_dashboard"),
    ("from src.visualizer", "from src.ui.visualizer"),
    ("from src.shortcuts", "from src.ui.shortcuts"),
]

def patch():
    # Patch root entry points
    for p in ["app.py", "fully_automated_trader.py"]:
        if not os.path.exists(p): continue
        with open(p, "rb") as f: c = f.read().decode("utf-8", errors="ignore")
        for old, new in REPS: c = c.replace(old, new)
        with open(p, "wb") as f: f.write(c.encode("utf-8"))
    
    # Patch all files in src/
    for root, _, fs in os.walk('src'):
        for f in fs:
            if not f.endswith(".py"): continue
            path = os.path.join(root, f)
            with open(path, "rb") as file: c = file.read().decode("utf-8", errors="ignore")
            new_c = c
            for old, new in REPS: new_c = new_c.replace(old, new)
            if new_c != c:
                with open(path, "wb") as file: file.write(new_c.encode("utf-8"))

if __name__ == "__main__":
    patch()
