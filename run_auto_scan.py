import sys
import os
import logging

# Add current directory to path
sys.path.append(os.getcwd())

# Setup basic logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from src.trading.fully_automated_trader.full_auto_trader import FullyAutomatedTrader

def live_scan():
    print("--- AGStock Live Market Scan ---")
    
    try:
        # Some versions might have different class names or paths
        # Let's try the most common one found in the project
        from src.trading.fully_automated_trader import FullyAutomatedTrader
    except ImportError:
        # Fallback to local import check
        from src.trading.fully_automated_trader.full_auto_trader import FullyAutomatedTrader

    trader = FullyAutomatedTrader()
    
    print("\n[Step 1] Fetching target tickers...")
    tickers = trader.get_target_tickers()
    print(f"Targeting: {len(tickers)} tickers.")
    
    print("\n[Step 2] Generating signals...")
    # This invokes the strategy logic
    signals = trader.generate_signals(tickers)
    
    print("\n[Final Result]")
    if not signals:
        print("❌ 現在、買付条件に合致する銘柄はありません。")
        print("理由: トレンドが出ていないか、リスク管理（ボラティリティ等）により抑制されています。")
    else:
        print(f"✅ {len(signals)} 件のシグナルを検出しました！")
        for s in signals:
            print(f"- {s['ticker']}: {s['action']} (Reason: {s['reason']})")

if __name__ == "__main__":
    live_scan()
