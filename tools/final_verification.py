import os
import sys
import logging
import pandas as pd

# PYTHONPATHEsys.path.append(os.getcwd())

# Elogging.basicConfig(level=logging.INFO)
from src.trading.fully_automated_trader import FullyAutomatedTrader

def run_final_verification():
    print(" --- E EE---")
    
    # 1. E    trader = FullyAutomatedTrader()
    
    # 2. EE
    is_safe, reason = trader.is_safe_to_trade()
    print(f"EE {is_safe} ({reason})")
    
    # 3. EEEE    # E
    print("\n...E)"
    # get_target_tickersE
    trader.get_target_tickers = lambda: ["9984.T", "7203.T", "NVDA"]
    
    signals = trader.scan_market()
    
    print("\nE)"
    if not signals:
        print("  EEE)"
    else:
        for s in signals:
            print(f"   {s['ticker']}: {s['action']} (: {s['strategy']}, E: {s['reason']})")

    print("\n--- 4. UIEEE---")
    try:
        from src.ui.dashboard_router import DashboardRouter
        tabs = DashboardRouter.get_tabs(len(signals))
        print(f"  UI: {len(tabs)} (DashboardRouter )")
    except Exception as e:
        print(f"  EUI: {e}")

    print("\nEEEE)"

if __name__ == "__main__":
    run_final_verification()