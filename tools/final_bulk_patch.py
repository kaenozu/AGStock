import os

# All moves mapping
MAPPING = {
    "src.config": "src.core.config",
    "src.constants": "src.core.constants",
    "src.logger_config": "src.core.logger",
    "src.log_config": "src.core.logger",
    "src.logging_config": "src.core.logger",
    "src.types": "src.core.types",
    "src.schemas": "src.core.schemas",
    "src.ui_renderers": "src.ui.ui_renderers",
    "src.ui_components": "src.ui.ui_components",
    "src.simple_dashboard": "src.ui.simple_dashboard",
    "src.visualizer": "src.ui.visualizer",
    "src.paper_trader": "src.trading.paper_trader",
    "src.live_trading": "src.trading.live_trading",
    "src.broker": "src.trading.broker",
    "src.data_loader": "src.data.data_loader",
    "src.data_manager": "src.data.data_manager",
    "src.cache_config": "src.data.cache_config",
    "src.database_manager": "src.data.database_manager",
    "src.advanced_models": "src.models.advanced_models",
    "src.lgbm_predictor": "src.models.lgbm_predictor",
    "src.advanced_risk": "src.risk.advanced_risk",
    "src.portfolio_manager": "src.risk.portfolio_manager",
    "src.error_handling": "src.utils.error_handling",
    "src.helpers": "src.utils.helpers",
}

def patch_file(path):
    with open(path, "rb") as f:
        content = f.read().decode("utf-8", errors="ignore")
    
    new_content = content
    # Precise replacements for absolute imports
    for old, new in MAPPING.items():
        new_content = new_content.replace(f"from {old}", f"from {new}")
        new_content = new_content.replace(f"import {old}", f"import {new}")
    
    # Fix setup_logger vs setup_logging which I noticed earlier
    if "app.py" in path:
        new_content = new_content.replace("setup_logger", "setup_logging")

    if new_content != content:
        with open(path, "wb") as f:
            f.write(new_content.encode("utf-8"))
        return True
    return False

def main():
    print("Starting final bulk patch...")
    targets = ["app.py", "fully_automated_trader.py", "main.py"]
    for root, _, fs in os.walk('src'):
        for f in fs:
            if f.endswith('.py'):
                targets.append(os.path.join(root, f))
    
    count = 0
    for t in targets:
        if os.path.exists(t):
            if patch_file(t): count += 1
    print(f"Patched {count} files.")

if __name__ == "__main__":
    main()
