import os
import shutil

def bulk_organize_with_proxies():
    print("Bulk organizing categories with proxies...")
    
    categories = {
        "ui": ["src/ui_renderers.py", "src/ui_components.py", "src/simple_dashboard.py", "src/visualizer.py", "src/ui_alerts.py", "src/ui_automation.py"],
        "trading": ["src/paper_trader.py", "src/live_trading.py", "src/broker.py", "src/rakuten_broker.py", "src/trading_cost.py"],
        "data": ["src/data_loader.py", "src/data_manager.py", "src/database_manager.py", "src/cache_config.py", "src/async_data_loader.py"],
        "models": ["src/advanced_models.py", "src/base_predictor.py", "src/lgbm_predictor.py", "src/online_learning.py"],
        "analysis": ["src/analytics.py", "src/fundamentals.py", "src/sentiment.py", "src/metrics.py", "src/regime.py"],
        "risk": ["src/advanced_risk.py", "src/portfolio_manager.py", "src/portfolio_optimizer.py", "src/risk_guard.py"]
    }
    
    for folder, files in categories.items():
        dest_dir = os.path.join("src", folder)
        os.makedirs(dest_dir, exist_ok=True)
        
        for orig in files:
            # Standardize paths to use forward slash for internal logic
            orig = orig.replace("\", "/")
            if os.path.exists(orig):
                filename = os.path.basename(orig)
                dest = os.path.join(dest_dir, filename)
                
                # Copy content
                shutil.copy2(orig, dest)
                print(f"Copied {orig} to {dest}")
                
                # Replace original with proxy
                # We want module path like 'src.ui.simple_dashboard'
                mod_path = dest.replace(".py", "").replace(os.sep, ".").replace("/", ".")
                with open(orig, "w", encoding="utf-8") as f:
                    f.write(f"from {mod_path} import *\n")
                print(f"Created proxy at {orig}")

if __name__ == "__main__":
    bulk_organize_with_proxies()
