import pandas as pd
import datetime
from src.constants import ALL_STOCKS
from src.data_loader import fetch_stock_data, get_latest_price
from src.strategies import LightGBMStrategy
from src.paper_trader import PaperTrader
from src.execution import ExecutionEngine
from src.cache_config import install_cache
from src.notifier import Notifier

def run_auto_trader():
    print(f"--- Auto Trader Started: {datetime.datetime.now()} ---")
    
    # 1. Setup
    install_cache()
    pt = PaperTrader()
    engine = ExecutionEngine(pt)
    strategy = LightGBMStrategy(lookback_days=365, threshold=0.005)
    notifier = Notifier()
    
    # 2. Fetch Data
    print("Fetching data...")
    tickers = ALL_STOCKS[:50]  # Sample 50 stocks from global universe for speed
    data_map = fetch_stock_data(tickers, period="2y")
    
    # 3. Generate Signals
    print("Generating signals...")
    signals = []
    prices = {}
    
    for ticker in tickers:
        df = data_map.get(ticker)
        if df is None or df.empty:
            continue
            
        # Get latest price for execution
        prices[ticker] = get_latest_price(df)
        
        # Run Strategy
        # Note: LightGBMStrategy fetches macro data internally
        s = strategy.generate_signals(df)
        
        if s.empty:
            continue
            
        last_signal = s.iloc[-1]
        
        # Check if we already hold it
        positions = pt.get_positions()
        is_held = ticker in positions.index
        
        if last_signal == 1 and not is_held:
            sig = {'ticker': ticker, 'action': 'BUY', 'confidence': 1.0, 'strategy': 'LightGBM'}
            signals.append(sig)
            # Notify strong signal
            notifier.notify_strong_signal(ticker, 'BUY', 1.0, prices[ticker], 'LightGBM')
        elif last_signal == -1 and is_held:
            sig = {'ticker': ticker, 'action': 'SELL', 'confidence': 1.0, 'strategy': 'LightGBM'}
            signals.append(sig)
            notifier.notify_strong_signal(ticker, 'SELL', 1.0, prices[ticker], 'LightGBM')
            
    print(f"Generated {len(signals)} signals.")
    
    # 4. Execute
    if signals:
        print("Executing trades...")
        engine.execute_orders(signals, prices)
    else:
        print("No trades to execute.")
        
    # 5. Update Equity
    pt.update_daily_equity()
    
    # 6. Send Daily Summary
    balance = pt.get_current_balance()
    portfolio_value = balance['total_equity']
    # Calculate daily P&L (simplified - compare to yesterday)
    daily_pnl = 0.0  # TODO: Track historical equity for accurate daily P&L
    
    notifier.notify_daily_summary(signals, portfolio_value, daily_pnl)
    
    print("--- Auto Trader Finished ---")

if __name__ == "__main__":
    run_auto_trader()
