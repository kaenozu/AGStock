import os
import re

# Final comprehensive mapping
ABS_REPS = [
    (r"from \.base_predictor", "from src.models.base_predictor"),
    (r"from \.lgbm_predictor", "from src.models.lgbm_predictor"),
    (r"from \.online_learning", "from src.models.online_learning"),
    (r"from \.online_lgbm", "from src.models.online_lgbm"),
    (r"from \.data_loader", "from src.data.data_loader"),
    (r"from \.data_manager", "from src.data.data_manager"),
    (r"from \.paper_trader", "from src.trading.paper_trader"),
    (r"from \.live_trading", "from src.trading.live_trading"),
    (r"from \.config", "from src.core.config"),
    (r"from \.constants", "from src.core.constants"),
    (r"from \.logger", "from src.core.logger"),
    (r"from \.error_handling", "from src.utils.error_handling"),
    (r"from \.helpers", "from src.utils.helpers"),
]

def final_absolute_patch():
    print("Converting relative imports to absolute for stability...")
    for root, _, fs in os.walk('src'):
        for f in fs:
            if not f.endswith('.py'): continue
            path = os.path.join(root, f)
            with open(path, "rb") as file: 
                content = file.read().decode("utf-8", errors="ignore")
            
            new_content = content
            for pattern, replacement in ABS_REPS:
                new_content = re.sub(pattern, replacement, new_content)
            
            if new_content != content:
                with open(path, "wb") as file:
                    file.write(new_content.encode("utf-8"))
                print(f"Fixed relative imports in: {path}")

if __name__ == "__main__":
    final_absolute_patch()
