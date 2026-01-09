import os
import subprocess

# Mapping of original Git paths to their NEW destinations
MAPPING = {
    # Entry points (keep at root but restore content)
    "app.py": "app.py",
    "fully_automated_trader.py": "fully_automated_trader.py",
    
    # Core Infrastructure
    "src/config.py": "src/core/config.py",
    "src/constants.py": "src/core/constants.py",
    "src/types.py": "src/core/types.py",
    "src/schemas.py": "src/core/schemas.py",
    "src/logger_config.py": "src/core/logger.py",
    
    # UI
    "src/ui_renderers.py": "src/ui/ui_renderers.py",
    "src/ui_components.py": "src/ui/ui_components.py",
    "src/simple_dashboard.py": "src/ui/simple_dashboard.py",
    "src/visualizer.py": "src/ui/visualizer.py",
    "src/responsive_ui.py": "src/ui/responsive_ui.py",
    "src/ui/shortcuts.py": "src/ui/shortcuts.py",
    
    # Trading
    "src/paper_trader.py": "src/trading/paper_trader.py",
    "src/live_trading.py": "src/trading/live_trading.py",
    "src/broker.py": "src/trading/broker.py",
    "src/rakuten_broker.py": "src/trading/rakuten_broker.py",
    "src/trading_cost.py": "src/trading/trading_cost.py",
    
    # Models
    "src/advanced_models.py": "src/models/advanced_models.py",
    "src/base_predictor.py": "src/models/base_predictor.py",
    "src/ml_prediction_system.py": "src/models/ml_prediction_system.py",
    "src/online_learning.py": "src/models/online_learning.py",
    "src/online_lgbm.py": "src/models/online_lgbm.py",
    "src/bert_sentiment.py": "src/models/bert_sentiment.py",
    
    # Analysis
    "src/advanced_analytics.py": "src/analysis/advanced_analytics.py",
    "src/analytics.py": "src/analysis/analytics.py",
    "src/metrics.py": "src/analysis/metrics.py",
    "src/regime.py": "src/analysis/regime.py",
    "src/fundamentals.py": "src/analysis/fundamentals.py",
    "src/sentiment.py": "src/analysis/sentiment.py",
    "src/patterns.py": "src/analysis/patterns.py",
    "src/regime_detector.py": "src/analysis/regime_detector.py",
    "src/market_access.py": "src/analysis/market_access.py",
    
    # Risk
    "src/advanced_risk.py": "src/risk/advanced_risk.py",
    "src/portfolio_risk.py": "src/risk/portfolio_risk.py",
    "src/kelly_criterion.py": "src/risk/kelly_criterion.py",
    "src/portfolio.py": "src/risk/portfolio.py",
    "src/portfolio_manager.py": "src/risk/portfolio_manager.py",
    "src/portfolio_optimizer.py": "src/risk/portfolio_optimizer.py",
    "src/portfolio_rebalancer.py": "src/risk/portfolio_rebalancer.py",
    
    # Data
    "src/async_data_loader.py": "src/data/async_data_loader.py",
    "src/async_fetcher.py": "src/data/async_fetcher.py",
    "src/async_processor.py": "src/data/async_processor.py",
    "src/external_data.py": "src/data/external_data.py",
    "src/data_quality.py": "src/data/data_quality.py",
    "src/japan_financial_statements.py": "src/data/japan_financial_statements.py",
    "src/data_loader.py": "src/data/data_loader.py",
    "src/realtime_data.py": "src/data/realtime_data.py",
    "src/cache_manager.py": "src/data/cache_manager.py",
    "src/persistent_cache.py": "src/data/persistent_cache.py",
    
    # Services
    "src/notification_system.py": "src/services/notification_system.py",
    "src/notifier.py": "src/services/notifier.py",
    "src/smart_notifier.py": "src/services/smart_notifier.py",
    "src/websocket_notifier.py": "src/services/websocket_notifier.py",
    
    # Utils
    "src/helpers.py": "src/utils/helpers.py",
    "src/formatters.py": "src/utils/formatters.py",
    "src/error_handling.py": "src/utils/error_handling.py",
    "src/errors.py": "src/utils/errors.py",
    "src/exceptions.py": "src/utils/exceptions.py",
    "src/paths.py": "src/utils/paths.py",
}

def restore_from_git():
    print("Restoring original content from Git...")
    for orig_path, dest_path in MAPPING.items():
        try:
            # Get content from HEAD (last good commit)
            content = subprocess.check_output(["git", "show", f"HEAD:{orig_path}"])
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            # Write content exactly as it was
            with open(dest_path, "wb") as f:
                f.write(content)
            print(f"Restored: {orig_path} -> {dest_path}")
        except Exception as e:
            print(f"Failed to restore {orig_path}: {e}")

def update_imports():
    print("Updating import paths safely...")
    # Common replacements
    REPLACEMENTS = [
        ("from src.config import settings", "from src.core.config import settings"),
        ("from src.config import config", "from src.core.config import config"),
        ("import src.config as config", "import src.core.config as config"),
        ("from src.constants", "from src.core.constants"),
        ("from src.logger_config import logger", "from src.core.logger import logger"),
        ("from src.log_config import logger", "from src.core.logger import logger"),
        ("from src.logging_config import logger", "from src.core.logger import logger"),
        ("from src.paper_trader", "from src.trading.paper_trader"),
        ("from src.live_trading", "from src.trading.live_trading"),
        ("from src.broker", "from src.trading.broker"),
        ("from src.rakuten_broker", "from src.trading.rakuten_broker"),
        ("from src.error_handling", "from src.utils.error_handling"),
        ("from src.ui_renderers", "from src.ui.ui_renderers"),
        ("from src.simple_dashboard", "from src.ui.simple_dashboard"),
        ("from src.visualizer", "from src.ui.visualizer"),
    ]
    
    for _, dest_path in MAPPING.items():
        if not os.path.exists(dest_path): continue
        try:
            with open(dest_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            new_lines = []
            for line in lines:
                for old, new in REPLACEMENTS:
                    line = line.replace(old, new)
                new_lines.append(line)
            
            with open(dest_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception as e:
            print(f"Failed to update imports in {dest_path}: {e}")

if __name__ == "__main__":
    restore_from_git()
    update_imports()
    print("Recovery complete.")
