import sys
import os
import json
import pandas as pd
import yfinance as yf
import datetime
from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES
from src.strategies import RSIStrategy, BollingerBandsStrategy, CombinedStrategy
from src.cache_config import install_cache

# Install cache
install_cache()

def load_best_params():
    if os.path.exists("best_params.json"):
        with open("best_params.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_strategy(strategy_name, params):
    if strategy_name == "RSI Reversal":
        return RSIStrategy(**params)
    elif strategy_name == "Combined":
        return CombinedStrategy(**params)
    elif strategy_name == "Bollinger Bands":
        return BollingerBandsStrategy(**params)
    return None

def main():
    print(f"--- Daily Signal Scan ({datetime.date.today()}) ---")
    
    best_params = load_best_params()
    tickers = NIKKEI_225_TICKERS
    
    print(f"Fetching data for {len(tickers)} tickers...")
    # Fetch slightly more data than needed for indicators (e.g. 1 year)
    try:
        df_all = yf.download(tickers, period="1y", group_by='ticker', auto_adjust=True, threads=True, progress=False)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    signals = []
    
    for ticker in tickers:
        if len(tickers) > 1:
            df = df_all[ticker].copy()
        else:
            df = df_all.copy()
            
        df.dropna(inplace=True)
        if df.empty:
            continue
            
        # Determine which strategy to use
        # If we have optimized params, use the best one.
        # Otherwise, check all default strategies?
        # Let's check "RSI Reversal" and "Combined" by default or optimized.
        
        strategies_to_check = []
        
        if ticker in best_params and best_params[ticker]:
            # Use the best strategy found
            # Find strategy with max train_return
            best_strat_name = max(best_params[ticker], key=lambda x: best_params[ticker][x]['train_return'])
            params = best_params[ticker][best_strat_name]['params']
            strategies_to_check.append((best_strat_name, params))
        else:
            # Use defaults
            strategies_to_check.append(("RSI Reversal", {}))
            strategies_to_check.append(("Combined", {}))
            
        for strat_name, params in strategies_to_check:
            strategy = get_strategy(strat_name, params)
            if not strategy:
                continue
                
            # Generate signals
            sig_series = strategy.generate_signals(df)
            
            # Check the last signal (Today's Close)
            if sig_series.empty:
                continue
                
            last_signal = sig_series.iloc[-1]
            
            if last_signal == 1:
                signals.append({
                    "Ticker": ticker,
                    "Name": TICKER_NAMES.get(ticker, ""),
                    "Action": "BUY",
                    "Strategy": strat_name,
                    "Price": df['Close'].iloc[-1]
                })
            elif last_signal == -1:
                signals.append({
                    "Ticker": ticker,
                    "Name": TICKER_NAMES.get(ticker, ""),
                    "Action": "SELL",
                    "Strategy": strat_name,
                    "Price": df['Close'].iloc[-1]
                })
                
    # Output Report
    if not signals:
        print("No signals found for tomorrow.")
    else:
        print(f"\nFound {len(signals)} signals for Tomorrow Open:\n")
        df_sig = pd.DataFrame(signals)
        print(df_sig.to_markdown(index=False))
        
        # Save to file
        df_sig.to_csv("daily_signals.csv", index=False)
        print("\nSaved to daily_signals.csv")

if __name__ == "__main__":
    main()
