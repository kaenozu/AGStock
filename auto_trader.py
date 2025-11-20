import pandas as pd
import datetime
from src.constants import NIKKEI_225_TICKERS
from src.data_loader import fetch_stock_data, get_latest_price
from src.strategies import LightGBMStrategy
from src.paper_trader import PaperTrader
from src.execution import ExecutionEngine
from src.cache_config import install_cache

def run_auto_trader():
    print(f"--- Auto Trader Started: {datetime.datetime.now()} ---")
    
    # 1. Setup
    install_cache()
    pt = PaperTrader()
    engine = ExecutionEngine(pt)
    strategy = LightGBMStrategy(lookback_days=365, threshold=0.005)
    
    # 2. Fetch Data
    print("Fetching data...")
    tickers = NIKKEI_225_TICKERS
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
            signals.append({'ticker': ticker, 'action': 'BUY', 'confidence': 1.0}) # TODO: Get real confidence
        elif last_signal == -1 and is_held:
            signals.append({'ticker': ticker, 'action': 'SELL', 'confidence': 1.0})
            
    print(f"Generated {len(signals)} signals.")
    
    # 4. Execute
    if signals:
        print("Executing trades...")
        engine.execute_orders(signals, prices)
    else:
        print("No trades to execute.")
        
    # 5. Update Equity
    pt.update_daily_equity()
    print("--- Auto Trader Finished ---")

if __name__ == "__main__":
    run_auto_trader()
