import sys
import os
import json
import pandas as pd
import yfinance as yf
import warnings
from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES
from src.optimizer import Optimizer
from src.cache_config import install_cache

# Install cache
install_cache()

# Suppress warnings
warnings.filterwarnings("ignore")

def fetch_data_local(tickers, period="2y"):
    print(f"Fetching data for {len(tickers)} tickers...")
    try:
        df = yf.download(tickers, period=period, group_by='ticker', auto_adjust=True, threads=True, progress=False)
        data_dict = {}
        for ticker in tickers:
            if len(tickers) > 1:
                stock_df = df[ticker].copy()
            else:
                stock_df = df.copy()
            stock_df.dropna(inplace=True)
            if not stock_df.empty:
                data_dict[ticker] = stock_df
        return data_dict
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {}

def main():
    print("Starting AI Parameter Optimization...")
    
    # 1. Fetch Data
    tickers = NIKKEI_225_TICKERS
    data_map = fetch_data_local(tickers, period="2y")
    
    if not data_map:
        print("No data fetched.")
        return

    # Optimize only the most promising strategies to save time
    strategies = ["RSI Reversal", "Combined"]
    
    best_params = {}
    
    print(f"Optimizing {len(data_map)} tickers for {len(strategies)} strategies...")
    
    for ticker, df in data_map.items():
        ticker_name = TICKER_NAMES.get(ticker, ticker)
        print(f"Optimizing {ticker} ({ticker_name})...")
        
        best_params[ticker] = {}
        
        for strategy_name in strategies:
            optimizer = Optimizer(df, strategy_name)
            # 20 trials is a quick scan. For production, use 50-100.
            params, value = optimizer.optimize(n_trials=20) 
            
            print(f"  {strategy_name}: Best Return (Train) = {value*100:.2f}%")
            
            best_params[ticker][strategy_name] = {
                "params": params,
                "train_return": value
            }
            
    # Save to JSON
    with open("best_params.json", "w", encoding="utf-8") as f:
        json.dump(best_params, f, indent=4, ensure_ascii=False)
        
    print("Optimization complete. Results saved to best_params.json")

if __name__ == "__main__":
    main()
