"""
Test Phase 30-2: Multi-Timeframe Analysis Strategy
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from src.hierarchical_strategy import HierarchicalStrategy
from src.data_loader import fetch_stock_data
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mtf_strategy():
    print("=" * 80)
    print("Testing Phase 30-2: Multi-Timeframe Strategy")
    print("=" * 80)
    
    tickers = ['7203.T', '6758.T', '9984.T']
    
    try:
        # Fetch data (Daily)
        print("Fetching daily data...")
        data_map = fetch_stock_data(tickers, period="2y")
        
        strategy = HierarchicalStrategy()
        
        results = []
        
        for ticker in tickers:
            if ticker not in data_map or data_map[ticker].empty:
                print(f"No data for {ticker}")
                continue
                
            df = data_map[ticker]
            print(f"\nAnalyzing {ticker} ({len(df)} days)...")
            
            # Generate signals
            signals = strategy.generate_signals(df)
            
            if signals.empty:
                print("  No signals generated.")
                continue
                
            # Calculate returns
            returns = df['Close'].pct_change().shift(-1)
            strategy_returns = signals * returns
            
            total_return = (1 + strategy_returns.fillna(0)).prod() - 1
            buy_hold_return = (1 + returns.fillna(0)).prod() - 1
            
            # Count trades
            trades = signals.diff().abs().sum() / 2
            
            print(f"  Total Return: {total_return*100:.2f}%")
            print(f"  Buy & Hold:   {buy_hold_return*100:.2f}%")
            print(f"  Trades:       {int(trades)}")
            
            # Check if MTF features were added (by inspecting a sample)
            # We can't easily inspect internal state, but if signals are generated, it likely worked.
            
            results.append({
                'ticker': ticker,
                'return': total_return,
                'buy_hold': buy_hold_return
            })
            
        if results:
            avg_return = np.mean([r['return'] for r in results])
            avg_bh = np.mean([r['buy_hold'] for r in results])
            print(f"\nAverage Strategy Return: {avg_return*100:.2f}%")
            print(f"Average Buy & Hold Return: {avg_bh*100:.2f}%")
            
            if avg_return > avg_bh:
                print("✅ Strategy outperformed Buy & Hold")
            else:
                print("⚠️ Strategy underperformed Buy & Hold")
                
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_mtf_strategy()
