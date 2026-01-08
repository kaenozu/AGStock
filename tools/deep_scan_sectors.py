
import pandas as pd
import numpy as np
import yfinance as yf
from src.data_loader import fetch_stock_data
from src.strategies.ml import MLStrategy
import logging
import warnings
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.ERROR)
warnings.filterwarnings('ignore')

def get_sector_tickers():
    """Sector Tickers"""
    sectors = {
        "Semiconductor": ["8035.T", "6857.T", "6146.T", "6723.T", "NVDA", "AMD", "ASML"],
        "Trading_Houses": ["8001.T", "8031.T", "8058.T", "8053.T", "8015.T"],
        "Automotive": ["7203.T", "7267.T", "7261.T", "TSLA"],
        "Tech_Platform": ["9984.T", "6758.T", "4755.T", "MSFT", "GOOGL", "META", "AMZN", "AAPL"],
        "Financial": ["8306.T", "8316.T", "8411.T", "JPM", "GS"],
        "Energy_Shipping": ["1605.T", "9101.T", "9104.T", "9107.T"],
        "Consumer_Retail": ["9983.T", "7974.T", "4661.T", "WMT", "COST"]
    }
    all_tickers = []
    for t_list in sectors.values():
        all_tickers.extend(t_list)
    return list(set(all_tickers))

def verify_single_ticker(ticker):
    try:
        data_map = fetch_stock_data([ticker], period="3y")
        df = data_map.get(ticker)
        if df is None or len(df) < 200:
            return None
        
        df.ticker = ticker
        strategy = MLStrategy()
        signals = strategy.generate_signals(df)
        
        df['next_ret'] = df['Close'].pct_change().shift(-1)
        check_df = pd.DataFrame({'signal': signals, 'next_ret': df['next_ret']}).dropna()
        active_signals = check_df[check_df['signal'] != 0]
        
        if len(active_signals) < 10:
            return {"ticker": ticker, "status": "Filtered (Low Signals)"}
            
        correct = (((active_signals['signal'] == 1) & (active_signals['next_ret'] > 0)) |
                   ((active_signals['signal'] == -1) & (active_signals['next_ret'] < 0))).sum()
        
        win_rate = correct / len(active_signals)
        avg_ret = (active_signals['signal'] * active_signals['next_ret']).mean()
        
        return {
            "ticker": ticker,
            "win_rate": win_rate,
            "avg_ret": avg_ret,
            "count": len(active_signals),
            "status": "Success"
        }
    except Exception:
        return None

def run_deep_scan():
    tickers = get_sector_tickers()
    print(f"--- Deep Scan Start (Total: {len(tickers)}) ---")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_ticker = {executor.submit(verify_single_ticker, ticker): ticker for ticker in tickers}
        for future in concurrent.futures.as_completed(future_to_ticker):
            res = future.result()
            if res and res.get("status") == "Success":
                results.append(res)
                ticker = res['ticker']
                wr = res['win_rate']
                ret = res['avg_ret']
                indicator = "🚀" if wr > 0.55 else "✅" if wr > 0.52 else "  "
                print(f"  {indicator} {ticker:8}: WinRate={wr:.1%} | AvgRet={ret:+.2%} ({res['count']} Trades)")

    if not results:
        print("No valid results found.")
        return

    df_res = pd.DataFrame(results)
    
    print("\n" + "="*60)
    print("  Deep Sector Scan Results")
    print("="*60)
    
    best_stocks = df_res[df_res['win_rate'] >= 0.53].sort_values(by='win_rate', ascending=False)
    
    for i, row in best_stocks.iterrows():
        print(f"  {row['ticker']:8} | WinRate {row['win_rate']:.1%} | AvgRet: {row['avg_ret']:+.2%}")
    
    print("="*60)
    print(f"\nScan complete. {len(best_stocks)} stocks passed threshold.")

if __name__ == "__main__":
    run_deep_scan()