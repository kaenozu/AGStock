import pandas as pd
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.data_loader import fetch_stock_data, get_latest_price
from src.strategies import (
    LightGBMStrategy, MLStrategy, CombinedStrategy, DividendStrategy
)

def check_predictions():
    tickers = ['8308.T', '7186.T', '9432.T', 'AMZN', 'NVDA']
    
    print(f"Fetching data for {tickers}...")
    data_map = fetch_stock_data(tickers, period="2y")
    
    strategies = [
        ("LightGBM", LightGBMStrategy(lookback_days=365, threshold=0.005)),
        ("ML Random Forest", MLStrategy()),
        ("Combined", CombinedStrategy()),
        # ("High Dividend", DividendStrategy()) # Skip dividend for short-term price prediction check
    ]
    
    print("\n--- Current Predictions ---")
    
    for ticker in tickers:
        df = data_map.get(ticker)
        if df is None or df.empty:
            print(f"{ticker}: No data found")
            continue
            
        latest_price = get_latest_price(df)
        print(f"\n[{ticker}] Current Price: {latest_price:,.2f}")
        
        for name, strategy in strategies:
            try:
                # Generate signals
                signals = strategy.generate_signals(df)
                
                if not signals.empty:
                    last_signal = signals.iloc[-1]
                    
                    signal_str = "NEUTRAL"
                    if last_signal == 1:
                        signal_str = "BUY (UP)"
                    elif last_signal == -1:
                        signal_str = "SELL (DOWN)"
                        
                    print(f"  {name:<20}: {signal_str}")
                else:
                    print(f"  {name:<20}: No signal generated")
                    
            except Exception as e:
                print(f"  {name:<20}: Error ({e})")

if __name__ == "__main__":
    check_predictions()
