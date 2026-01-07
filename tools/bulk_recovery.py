import os
import subprocess

def get_git_files():
    output = subprocess.check_output(["git", "ls-tree", "-r", "HEAD", "--name-only"]).decode('utf-8')
    return output.splitlines()

def get_dest_path(orig_path):
    # Mapping logic based on previous moves
    if orig_path in ["app.py", "fully_automated_trader.py", "main.py"]:
        return orig_path
    
    if orig_path.startswith("src/"):
        filename = os.path.basename(orig_path)
        
        # Exceptions / Specific destinations
        if filename in ["config.py", "constants.py", "types.py", "schemas.py", "logger_config.py", "log_config.py", "logging_config.py"]:
            if "logger" in filename or "log" in filename:
                return "src/core/logger.py"
            return f"src/core/{filename}"
            
        if filename.startswith("ui_") or filename in ["simple_dashboard.py", "visualizer.py", "responsive_ui.py", "shortcuts.py"]:
            return f"src/ui/{filename}"
            
        if filename in ["paper_trader.py", "live_trading.py", "broker.py", "rakuten_broker.py", "trading_cost.py"]:
            return f"src/trading/{filename}"
            
        if filename in ["advanced_models.py", "base_predictor.py", "ml_prediction_system.py", "online_learning.py", "online_lgbm.py", "bert_sentiment.py", "lgbm_predictor.py"]:
            return f"src/models/{filename}"
            
        if filename in ["advanced_analytics.py", "analytics.py", "metrics.py", "regime.py", "fundamentals.py", "sentiment.py", "patterns.py", "regime_detector.py", "market_access.py"]:
            return f"src/analysis/{filename}"
            
        if filename in ["advanced_risk.py", "portfolio_risk.py", "kelly_criterion.py", "portfolio.py", "portfolio_manager.py", "portfolio_optimizer.py", "portfolio_rebalancer.py"]:
            return f"src/risk/{filename}"
            
        if filename in ["async_data_loader.py", "async_fetcher.py", "async_processor.py", "external_data.py", "data_quality.py", "japan_financial_statements.py", "data_loader.py", "realtime_data.py", "cache_manager.py", "persistent_cache.py", "data_manager.py", "database_manager.py", "data_preprocessing.py", "data_processor.py"]:
            return f"src/data/{filename}"
            
        if filename in ["notification_system.py", "notifier.py", "smart_notifier.py", "websocket_notifier.py", "alert_manager.py", "alert_system.py"]:
            return f"src/services/{filename}"
            
        if filename in ["helpers.py", "formatters.py", "error_handling.py", "errors.py", "exceptions.py", "paths.py"]:
            return f"src/utils/{filename}"

    return orig_path # Default: keep same

def bulk_restore():
    files = get_git_files()
    print(f"Restoring {len(files)} files from Git...")
    for f in files:
        if not f.endswith(".py"): continue
        dest = get_dest_path(f)
        try:
            content = subprocess.check_output(["git", "show", f"HEAD:{f}"])
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as out:
                out.write(content)
        except Exception as e:
            print(f"Failed {f}: {e}")

def bulk_patch():
    print("Bulk patching imports...")
    REPLACEMENTS = [
        ("from src.config import", "from src.core.config import"),
        ("from src.constants", "from src.core.constants"),
        ("from src.logger_config", "from src.core.logger"),
        ("from src.log_config", "from src.core.logger"),
        ("from src.logging_config", "from src.core.logger"),
        ("from src.error_handling", "from src.utils.error_handling"),
        ("from src.data_loader", "from src.data.data_loader"),
        ("from src.paper_trader", "from src.trading.paper_trader"),
        ("from src.lgbm_predictor", "from src.models.lgbm_predictor"),
        ("from src.online_learner", "from src.models.online_learning"), # Fixed name mapping
        ("from src.backup_manager", "from src.utils.backup_manager"), # Heuristic
        ("from .config import", "from src.core.config import"),
        ("from .constants", "from src.core.constants"),
    ]
    
    for root, _, files in os.walk('src'):
        for file in files:
            if not file.endswith('.py'): continue
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            new_content = content
            for old, new in REPLACEMENTS:
                new_content = new_content.replace(old, new)
            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)

if __name__ == "__main__":
    bulk_restore()
    bulk_patch()
    print("Bulk recovery finished.")
