import os

def fix_init_exports():
    path = "src/__init__.py"
    REPS = [
        ("from .continual_learning", "from src.models.continual_learning"),
        ("from .enhanced_ensemble_predictor", "from src.models.enhanced_ensemble_predictor"),
        ("from .base_predictor", "from src.models.base_predictor"),
        ("from .lgbm_predictor", "from src.models.lgbm_predictor"),
        ("from .online_learning", "from src.models.online_learning"),
        ("from .prediction_backtester", "from src.analysis.prediction_backtester"),
    ]
    with open(path, "r", encoding="utf-8", errors="ignore") as f: content = f.read()
    for old, new in REPS: content = content.replace(old, new)
    with open(path, "w", encoding="utf-8") as f: f.write(content)

if __name__ == "__main__":
    fix_init_exports()
