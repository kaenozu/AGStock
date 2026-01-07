import logging
import os
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SovereignMorning")

sys.path.append(os.getcwd())

from src.optimization.evolution_engine import SovereignEvolutionEngine
from src.trading.fully_automated_trader import FullyAutomatedTrader
from src.smart_notifier import SmartNotifier
from src.oracle.oracle_2026 import Oracle2026

def run_morning_constitution():
    print(""""
    ===================================================
        SOVEREIGN MORNING CONSTITUTION (2026) 
    ===================================================
    """)"
    
    # 1. Self-Evolution
    logger.info("Step 1: Awakening the Sovereign Spirit...")
    try:
        engine = SovereignEvolutionEngine()
        engine.evolve()
    except Exception as e:
        logger.error(f"Evolution failed: {e}")
        
    notifier = SmartNotifier()
    oracle = Oracle2026()
    
    # 2. Oracle Guidance
    logger.info("Step 2: Receiving Divine Mandate...")
    guidance = oracle.get_risk_guidance()
    oracle_msg = guidance.get("oracle_message", "Silent")
    
    # 3. Market Scan
    logger.info("Step 3: Scanning the Empire...")
    trader = FullyAutomatedTrader()
    # Note: scan_market behavior depends on implementation (returns list of signals)
    # We might need to mock cash or balance if it checks broker.
    # scan_market usually returns a list of dicts.
    
    try:
        signals = trader.scan_market()
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        signals = []
        
    logger.info(f"Scan Complete. Found {len(signals)} opportunities.")
    
    # Filter for high quality
    top_signals = signals[:5]
    
    # 4. Reporting
    logger.info("Step 4: Broadcasting to Emperor...")
    
    summary = {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "total_value": trader.pt.get_current_balance().get("total_equity", 0),
        "daily_pnl": trader.calculate_daily_pnl(),
        "monthly_pnl": trader.calculate_monthly_pnl(),
        "win_rate": 0,
        "signals": sorted(top_signals, key=lambda x: x.get("confidence", 0), reverse=True),
        "advice": f" Oracle: {oracle_msg}"
    }
    
    notifier.send_daily_summary_rich(summary)
    
    print("\nEMorning Constitution Complete. The Empire is ready.")

if __name__ == "__main__":
    run_morning_constitution() 