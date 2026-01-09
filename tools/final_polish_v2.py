import os

REPS = [
    ("from src.dynamic_risk_manager", "from src.risk.dynamic_risk_manager"),
    ("from src.risk_guard", "from src.risk.risk_guard"),
    ("from src.risk_limiter", "from src.risk.risk_limiter"),
    ("from src.safety_manager", "from src.risk.safety_manager"),
    ("from src.portfolio_manager", "from src.risk.portfolio_manager"),
    ("from src.backup_manager", "from src.risk.backup_manager"),
    ("from src.data_loader", "from src.data.data_loader"),
    ("from src.data_manager", "from src.data.data_manager"),
    ("from src.database_manager", "from src.risk.database_manager"),
    ("from src.online_learning", "from src.models.online_learning"),
    ("from src.online_learner", "from src.models.online_learning"),
    ("from src.lgbm_predictor", "from src.models.lgbm_predictor"),
    ("from src.base_predictor", "from src.models.base_predictor"),
]

def polish():
    targets = ["app.py", "fully_automated_trader.py", "src/trading/fully_automated_trader.py", "src/ui/simple_dashboard.py"]
    for path in targets:
        if not os.path.exists(path): continue
        with open(path, "rb") as f: content = f.read().decode("utf-8", errors="ignore")
        for old, new in REPS:
            content = content.replace(old, new)
        with open(path, "wb") as f: f.write(content.encode("utf-8"))
        print(f"Polished: {path}")

if __name__ == "__main__":
    polish()
