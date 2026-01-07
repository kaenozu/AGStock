
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.data_loader import fetch_stock_data
from src.strategies.ml import MLStrategy
import logging
import warnings

# 
logging.basicConfig(level=logging.ERROR)
warnings.filterwarnings('ignore')

def run_rigorous_validation(ticker, test_days=120):
    """"
    EEEE
    EEEE
    """"
    print(f"\n=====  EE {ticker} =====")
    
    # 1. EEE(3E
    data_map = fetch_stock_data([ticker], period="3y")
    df = data_map.get(ticker)
    if df is None or len(df) < 500:
        print("EEEE)"
        return None
        
    df.ticker = ticker
    
    # 2. E
    strategy = MLStrategy()
    
    # 3. E (EE)
    # SingularityEEE4E
    signals = strategy.generate_signals(df)
    
    # 4.  (Etest_days E
    # next_day_return E
    df['next_ret'] = df['Close'].pct_change().shift(-1)
    
    results_df = pd.DataFrame({
        'price': df['Close'],
        'signal': signals,
        'next_ret': df['next_ret']
    }).tail(test_days)
    
    # E
    active = results_df[results_df['signal'] != 0]
    
    if len(active) == 0:
        print(f"E{test_days} EEE)"
        return None
        
    # EE
    correct = (((active['signal'] == 1) & (active['next_ret'] > 0)) |
               ((active['signal'] == -1) & (active['next_ret'] < 0))).sum()
    
    win_rate = correct / len(active)
    
    # E
    #  * 
    active['trade_ret'] = active['signal'] * active['next_ret']
    cumulative_ret = (1 + active['trade_ret']).prod() - 1
    
    # E()
    sharpe = np.sqrt(252) * (active['trade_ret'].mean() / active['trade_ret'].std()) if len(active) > 5 else 0
    
    print(f"  : E{test_days} ")
    print(f"  : {len(active)} E)"
    print(f"  EE {win_rate:.2%}")
    print(f"  : {cumulative_ret:+.2%}")
    print(f"  : {sharpe:.2f}")
    
    # EEE
    print("\n  --- EEEEEE---")
    recent_trades = active.tail(5)
    for idx, row in recent_trades.iterrows():
        action = "BUY " if row['signal'] == 1 else "SELL"
        result = "EHIT " if (row['signal'] * row['next_ret']) > 0 else "EMISS"
        print(f"    {idx.date()} | Action: {action} | Next Ret: {row['next_ret']:+.2%} | {result}")
        
    return {
        'ticker': ticker,
        'win_rate': win_rate,
        'return': cumulative_ret,
        'count': len(active)
    }

if __name__ == "__main__":
    # E2E1
    targets = ["8015.T", "9984.T", "NVDA"]
    all_res = []
    
    for t in targets:
        res = run_rigorous_validation(t)
        if res: all_res.append(res)
        
    if all_res:
        avg_win = sum(r['win_rate'] for r in all_res) / len(all_res)
        print("\n" + "="*40)
        print(f" E {' EXCELLENT' if avg_win > 0.55 else 'EGOOD' if avg_win > 0.50 else 'EECAUTION'}")
        print(f" 3EE {avg_win:.2%}")
        print("="*40)
        print( EEEEEE)  