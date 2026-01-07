
import pandas as pd
import numpy as np
from src.data_loader import fetch_stock_data
from src.strategies.ml import MLStrategy
import logging
import warnings

# 
logging.basicConfig(level=logging.ERROR)
warnings.filterwarnings('ignore')

def verify_comprehensive():
    # EEEEEE
    jp_tickers = ["6758.T", "8035.T", "8306.T", "7974.T", "9432.T", "8001.T"]
    us_tickers = ["MSFT", "GOOGL", "TSLA", "AMZN", "META"]
    
    tickers = jp_tickers + us_tickers
    print(f"--- AI EEE---")
    print(f": {len(tickers)} (JP: {len(jp_tickers)}, US: {len(us_tickers)})")
    
    results = []
    
    for ticker in tickers:
        try:
            # 1. EEE
            data_map = fetch_stock_data([ticker], period="3y")
            df = data_map.get(ticker)
            if df is None or len(df) < 200: 
                print(f"  {ticker:8}: EE")
                continue
            
            df.ticker = ticker
            
            # 2. E
            strategy = MLStrategy()
            signals = strategy.generate_signals(df)
            
            # 3. E
            df['next_ret'] = df['Close'].pct_change().shift(-1)
            check_df = pd.DataFrame({
                'signal': signals,
                'next_ret': df['next_ret']
            }).dropna()
            
            active_signals = check_df[check_df['signal'] != 0]
            
            if len(active_signals) == 0:
                print(f"  {ticker:8}:  ()")
                continue
                
            correct = (
                ((active_signals['signal'] == 1) & (active_signals['next_ret'] > 0)) |
                ((active_signals['signal'] == -1) & (active_signals['next_ret'] < 0))
            ).sum()
            
            win_rate = correct / len(active_signals)
            avg_ret = (active_signals['signal'] * active_signals['next_ret']).mean()
            
            status = "E" if win_rate > 0.53 else " E"
            print(f"  {ticker:8}: EE{win_rate:.1%} | E {avg_ret:+.2%} | {status}")
            
            results.append({
                'ticker': ticker,
                'win_rate': win_rate,
                'count': len(active_signals),
                'expected_return': avg_ret
            })
        except Exception as e:
            print(f"  {ticker:8}: E({str(e)})")

    if results:
        df_res = pd.DataFrame(results)
        total_win = (df_res['win_rate'] * df_res['count']).sum() / df_res['count'].sum()
        total_ret = df_res['expected_return'].mean()
        
        print("\n" + "="*50)
        print(f"  (11E")
        print(f" EE {total_win:.2%}")
        print(f" EE: {total_ret:+.2%}")
        print("="*50)
        print("\n EE")
        print("1. AIEEE)"
        print("2. EEEEEEAPLEEE)"
        print("3. E EESLA, NVDAEEEEE)"

if __name__ == "__main__":
    verify_comprehensive()