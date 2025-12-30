
import time
import os
import inspect
from typing import Dict
import logging
import glob

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("ImpactMeasurer")

def count_lines(filepath: str) -> int:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return len(f.readlines())
    except Exception:
        return 0

def measure_init_time(cls_name, module_path, cls_obj) -> float:
    start_time = time.time()
    try:
        # Mock config if needed
        if cls_name == "FullyAutomatedTrader":
            _ = cls_obj("config.json")
        elif cls_name == "InvestmentCommittee":
            _ = cls_obj(None)
        else:
            _ = cls_obj()
    except Exception as e:
        logger.warning(f"Init failed for {cls_name}: {e}")
    return (time.time() - start_time) * 1000  # ms

def main():
    print("=== 📊 AGStock Refactoring Impact Report ===")
    
    # 1. Code Logic Distribution (LOC Analysis)
    print("\n[1. Code Complexity / LOC Distribution]")
    
    files = {
        "FullyAutomatedTrader (Facade)": "src/trading/fully_automated_trader.py",
        "MarketScanner (Refactored)": "src/trading/market_scanner.py",
        "TradeExecutor (Refactored)": "src/trading/trade_executor.py",
        "DailyReporter (Refactored)": "src/trading/daily_reporter.py",
        "InvestmentCommittee": "src/agents/committee.py",
        "RL Trainer (Phase 4)": "src/rl/trainer.py",
        "Dojo UI (Phase 4/5)": "src/ui/dojo.py"
    }
    
    total_lines = 0
    
    for name, path in files.items():
        if os.path.exists(path):
            loc = count_lines(path)
            total_lines += loc
            print(f"  - {name:<30}: {loc:>4} lines")
        else:
            print(f"  - {name:<30}: NOT FOUND")

    print(f"  > Total Lines (Core + RL): {total_lines}")
    
    # ... (Initialization tests remain same) ...

    # 3. New Feature Verification
    print("\n[3. Feature Verification]")
    
    # Divine Sight
    json_path = "data/latest_scan_results.json"
    if os.path.exists(json_path):
        size = os.path.getsize(json_path)
        print(f"  - [Phase 3] Divine Sight Data : FOUND ({size} bytes)")
    else:
        print("  - [Phase 3] Divine Sight Data : NOT FOUND")

    # Dojo & Deployment
    rl_models = glob.glob("models/rl/*.pth")
    print(f"  - [Phase 4] Trained RL Models : {len(rl_models)} found")
    
    prod_model = "models/production/active_agent.pth"
    if os.path.exists(prod_model):
        mtime = time.ctime(os.path.getmtime(prod_model))
        print(f"  - [Phase 5] Active Prod Model : DEPLOYED ({mtime})")
    else:
        print("  - [Phase 5] Active Prod Model : NOT DEPLOYED")

    print("\n=== End of Report ===")

if __name__ == "__main__":
    main()
