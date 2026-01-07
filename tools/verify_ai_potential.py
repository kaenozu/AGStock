
import pandas as pd
import numpy as np
from src.data_loader import fetch_stock_data
from src.strategies.ml import MLStrategy
import logging

# 
logging.basicConfig(level=logging.ERROR)

def verify_ai_accuracy():
    tickers = ["NVDA", "AAPL", "7203.T", "9984.T"]
    print(f"--- AI  (: {', '.join(tickers)}) ---")
    
    results = []
    
    for ticker in tickers:
        # 1. EEE        data_map = fetch_stock_data([ticker], period="3y")
        df = data_map.get(ticker)
        if df is None or len(df) < 100: continue
        df.ticker = ticker  # TickerEE        
        # 2. E        strategy = MLStrategy()
        signals = strategy.generate_signals(df)
        
        # 3. E(EEEE
        # E        df['next_ret'] = df['Close'].pct_change().shift(-1)
        
        # 
        check_df = pd.DataFrame({
            'signal': signals,
            'next_ret': df['next_ret']
        }).dropna()
        
        # EE
        active_signals = check_df[check_df['signal'] != 0]
        
        if len(active_signals) == 0:
            print(f"  {ticker}: E)"
            continue
            
        # E()
        correct = (
            ((active_signals['signal'] == 1) & (active_signals['next_ret'] > 0)) |
            ((active_signals['signal'] == -1) & (active_signals['next_ret'] < 0))
        ).sum()
        
        win_rate = correct / len(active_signals)
        avg_ret = (active_signals['signal'] * active_signals['next_ret']).mean()
        
        print(f"  {ticker}:")
        print(f"    : {len(active_signals)} E)"
        print(f"    EE     {win_rate:.2%}")
        print(f"    1E: {avg_ret:+.2%}")
        
        results.append({
            'ticker': ticker,
            'win_rate': win_rate,
            'count': len(active_signals),
            'expected_return': avg_ret
        })

    if results:
        total_win = sum(r['win_rate'] * r['count'] for r in results) / sum(r['count'] for r in results)
        print("\n=========================================")
        print(f" AIEEE {total_win:.2%}")
        print("=========================================")
        
        if total_win > 0.55:
            print("EEEEEE)"
        else:
            print("EEEEE)"

if __name__ == "__main__":
    verify_ai_accuracy()