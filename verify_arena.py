"""
Verify Strategy Arena Backend
"""
import pandas as pd
from src.backtest_engine import HistoricalBacktester
from src.strategies import SMACrossoverStrategy, RSIStrategy

def test_arena_backend():
    print("Testing Strategy Arena Backend...")
    
    # Initialize Engine
    engine = HistoricalBacktester()
    
    # Strategies to test
    strategies = [
        (SMACrossoverStrategy, {'short_window': 5, 'long_window': 10}),
        (RSIStrategy, {'period': 14})
    ]
    
    ticker = "7203.T" # Toyota
    
    print(f"Running comparison for {ticker}...")
    
    # Note: run_test inside compare_strategies fetches data. 
    # If network is an issue, this might fail, but let's assume network is fine or use mock in real test.
    # For this verification, we'll try running it. If fetch fails, we can't test fully without mocking.
    # But let's see.
    
    try:
        metrics, equity = engine.compare_strategies(ticker, strategies, years=1)
        
        print("\n--- Metrics ---")
        print(metrics)
        
        print("\n--- Equity Curves ---")
        print(equity.head())
        
        if not metrics.empty and not equity.empty:
            print("\n✅ Verification Successful: DataFrames generated.")
            return True
        else:
            print("\n❌ Verification Failed: Empty results.")
            return False
            
    except Exception as e:
        print(f"\n❌ info: {e}")
        # If fetch error, it's expected in some envs.
        return False

if __name__ == "__main__":
    test_arena_backend()
