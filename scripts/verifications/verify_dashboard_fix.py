import sys
import os
import logging

# Ensure src is locally importable
sys.path.append(os.getcwd())

from src.paper_trader import PaperTrader

def test_daily_summary():
    print("Testing PaperTrader.get_daily_summary()...")
    pt = PaperTrader()
    try:
        summary = pt.get_daily_summary()
        print(f"Daily Summary Success! Result: {summary}")
        
        print("Testing PaperTrader.get_equity_history(days=30)...")
        equity = pt.get_equity_history(days=30)
        print(f"Equity History Success! Rows: {len(equity)}")
        
    except Exception as e:
        print(f"Failed: {e}")
        raise e
    finally:
        pt.close()

if __name__ == "__main__":
    test_daily_summary()
