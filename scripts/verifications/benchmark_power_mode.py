import os
import sys
import time
import pandas as pd

# Add src to path
sys.path.append(os.getcwd())

from src.trading.fully_automated_trader import FullyAutomatedTrader

def test_power_mode_benchmark():
    print("🚀 Running Performance Benchmark: Standard vs Power Mode (Vectorized)")
    
    # 1. Initialize Traders
    standard_trader = FullyAutomatedTrader(use_power_mode=False)
    power_trader = FullyAutomatedTrader(use_power_mode=True)
    
    # Mock some tickers
    tickers = ["7203.T", "9984.T", "AAPL", "MSFT", "NVDA"]
    
    print(f"\nScanning {len(tickers)} tickers...")
    
    # Pre-warm caches
    standard_trader.warmup_caches()
    
    # Measure Standard Scan
    start = time.time()
    standard_trader.scan_market()
    standard_duration = time.time() - start
    print(f"⏱ Standard Scan Duration: {standard_duration:.2f}s")
    
    # Measure Power Mode Scan
    start = time.time()
    power_trader.scan_market()
    power_duration = time.time() - start
    print(f"⚡ Power Mode Scan Duration: {power_duration:.2f}s")
    
    improvement = (standard_duration / power_duration) if power_duration > 0 else 0
    print(f"\n🚀 Speed Improvement: {improvement:.1f}x")

if __name__ == "__main__":
    test_power_mode_benchmark()
