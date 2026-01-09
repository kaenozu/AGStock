import os

REPLACEMENTS = [
    ("from src.config import", "from src.core.config import"),
    ("from src.constants", "from src.core.constants"),
    ("from src.logger_config", "from src.core.logger"),
    ("from src.error_handling", "from src.utils.error_handling"),
    ("from src.data_loader", "from src.data.data_loader"),
    ("from src.paper_trader", "from src.trading.paper_trader"),
]

TARGETS = [
    "src/agents/committee.py",
    "src/strategies/__init__.py",
    "src/backtester.py",
    "src/strategies/base.py",
    "src/strategies/ml.py"
]

def patch():
    for p in TARGETS:
        if not os.path.exists(p): continue
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        for old, new in REPLACEMENTS:
            content = content.replace(old, new)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Patched: {p}")

if __name__ == "__main__":
    patch()
