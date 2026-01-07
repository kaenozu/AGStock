
import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

from src.trading.fully_automated_trader import FullyAutomatedTrader

def test_initialization():
    print("Initializing FullyAutomatedTrader...")
    try:
        trader = FullyAutomatedTrader()
        print("Successfully initialized.")
        return trader
    except Exception as e:
        print(f"Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_safety_check(trader):
    print("Testing safety check...")
    is_safe, reason = trader.is_safe_to_trade()
    print(f"Is safe: {is_safe}, Reason: {reason}")

def test_get_tickers(trader):
    print("Testing get target tickers...")
    tickers = trader.get_target_tickers()
    print(f"Got {len(tickers)} tickers.")

if __name__ == "__main__":
    trader = test_initialization()
    if trader:
        test_safety_check(trader)
        test_get_tickers(trader)
