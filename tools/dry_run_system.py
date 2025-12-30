
import os
import sys
import logging
import json
import sqlite3
import pandas as pd
from unittest.mock import MagicMock, patch

# Ensure src is in path
sys.path.append(os.getcwd())

from src.trading.fully_automated_trader import FullyAutomatedTrader
from src.schemas import TradingDecision

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DryRun")

def run_dry_test():
    logger.info("🚀 Starting Dry Run System Test...")

    # 1. Create a temporary config
    test_config = {
        "paper_trading": {"initial_capital": 1000000},
        "auto_trading": {
            "max_daily_trades": 5,
            "daily_loss_limit_pct": -5.0,
            "max_vix": 100.0, # High limit to pass check
        },
        "ai_committee": {"enabled": True},
        "risk_limits": {
            "max_position_size": 0.5,
            "max_daily_trades": 10,
            "max_daily_loss_pct": -10.0,
            "max_total_exposure": 1.0,
            "require_confirmation": False,
            "emergency_stop_loss_pct": -20.0,
            "min_cash_reserve": 0.0,
        },
        "portfolio_targets": {
            "japan": 100, "us": 0, "europe": 0, "crypto": 0, "fx": 0
        }
    }
    
    with open("dry_run_config.json", "w") as f:
        json.dump(test_config, f)

    # 2. Mock UniverseManager to avoid heavy scanning
    with patch("src.trading.fully_automated_trader.UniverseManager") as MockUniverse:
        instance = MockUniverse.return_value
        instance.get_top_candidates.return_value = ["7203.T"] # Toyota only
        
        # 3. Initialize Trader (using test config)
        logger.info("Initializing FullyAutomatedTrader...")
        trader = FullyAutomatedTrader(config_path="dry_run_config.json")
        
        
        # Override PaperTrader DB to use a temporary file
        try:
            trader.pt.db_path = "data/dry_run_paper_trading.db"
            trader.pt._initialize_database() # Re-init with new path
        except Exception as e:
            logger.error(f"❌ DB Init Failed: {e}")
            with open("dry_run_error.txt", "w") as f:
                import traceback
                traceback.print_exc(file=f)
            return
        
        # 4. Mock Market Data (Optional, but safer to rely on real data if yfinance works)
        # For this test, let's try REAL data first to verify yfinance integration.
        # If it fails, we know external connectivity is the issue.
        
        # 5. Run Scan Market
        logger.info("Running scan_market()...")
        try:
            # We must set backup_manager to None or mock it to avoid creating real backups
            trader.backup_manager = None 
            
            # Hook into the logger to see output
            trader.logger = logger 
            
            if hasattr(trader, 'scan_market'):
                 logger.info("Invoking scan_market method...")
                 signals = trader.scan_market()
                 logger.info(f"Scan complete. Signals generated: {len(signals) if signals else 0}")
            else:
                 logger.error("scan_market method missing!")
            
        except Exception as e:
            logger.error(f"❌ Scan Market Failed: {e}")
            with open("dry_run_error.txt", "w") as f:
                import traceback
                traceback.print_exc(file=f)
            return

        # 6. Test Digital Twin Integration (Manual Check)
        logger.info("Checking Digital Twin integration...")
        if trader.committee and hasattr(trader.committee, 'twin'):
             logger.info("✅ Digital Twin is attached to Committee.")
        else:
             logger.warning("⚠️ Digital Twin NOT found on Committee.")

        # 7. Test MTF Analyst
        logger.info("Checking MTF Analyst...")
        if trader.committee and hasattr(trader.committee, 'mtf_analyst'):
            logger.info("✅ MTF Analyst is attached to Committee.")
        else:
             logger.warning("⚠️ MTF Analyst NOT found on Committee.")

        # 8. Test RL Agent Loading (Manual check of file existence)
        logger.info("Checking RL Model availability...")
        if os.path.exists("models/rl_dqn.pth"):
             logger.info("✅ RL Model found.")
        else:
             logger.warning("⚠️ RL Model NOT found. (Run train_rl_agent.py to fix)")

    # Cleanup
    if os.path.exists("dry_run_config.json"):
        os.remove("dry_run_config.json")
    if os.path.exists("data/dry_run_paper_trading.db"):
        try:
            os.remove("data/dry_run_paper_trading.db")
        except:
            pass
    
    logger.info("✅ Dry Run Test Complete.")

if __name__ == "__main__":
    run_dry_test()
