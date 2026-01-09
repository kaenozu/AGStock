import sqlite3
import pandas as pd
import sys
import os
from unittest.mock import MagicMock

# Add root to python path
sys.path.append(os.getcwd())

# --- Monkeypatch SentimentAnalyzer BEFORE imports that use it ---
# We need to mock it in sys.modules or patch the class after import
import src.sentiment
original_sa = src.sentiment.SentimentAnalyzer

class MockSentimentAnalyzer:
    def __init__(self, db_path=None):
        pass
    def get_market_sentiment(self):
        print("⚡ [Mock] Sentiment Analysis skipped (Returning Neutral)")
        return {"score": 0.0, "label": "Neutral", "news_count": 0}
        
src.sentiment.SentimentAnalyzer = MockSentimentAnalyzer
# ------------------------------------------------------------

from src.trading.fully_automated_trader import FullyAutomatedTrader
from src.paper_trader import PaperTrader

def reset_portfolio():
    print("🔄 Resetting Portfolio...")
    try:
        conn = sqlite3.connect("paper_trading.db")
        cursor = conn.cursor()
        
        # 1. Clear tables
        cursor.execute("DELETE FROM positions")
        cursor.execute("DELETE FROM orders")
        
        # 2. Reset Cash
        # Get initial capital (default 1M)
        cursor.execute("SELECT initial_capital FROM accounts WHERE id=1")
        row = cursor.fetchone()
        if row:
            initial_cap = row[0]
            cursor.execute("UPDATE accounts SET current_balance = ? WHERE id=1", (initial_cap,))
        else:
            # Re-init if missing
            initial_cap = 1000000
            cursor.execute("INSERT INTO accounts (initial_capital, current_balance) VALUES (?, ?)", (initial_cap, initial_cap))
            
        conn.commit()
        conn.close()
        print("✅ Portfolio Reset Complete. Cash restored to Initial Capital.")
    except Exception as e:
        print(f"❌ Error resetting portfolio: {e}")

def run_auto_trade():
    print("🚀 Starting Auto-Trade Sequence (Fast Mode)...")
    try:
        trader = FullyAutomatedTrader()
        
        # 1. Scan
        print("🔍 Scanning Market...")
        # Force log to stdout
        trader.logger.handlers = []
        import logging
        handler = logging.StreamHandler(sys.stdout)
        trader.logger.addHandler(handler)
        trader.logger.setLevel(logging.INFO)
        
        signals = trader.scan_market()
        print(f"📊 Signals Generated: {len(signals)}")
        
        if not signals:
            print("⚠️ No signals found. Checks logs above.")
            return

        # 2. Execute
        print("💸 Executing Orders...")
        prices = {s['ticker']: s['price'] for s in signals}
        
        results = trader.engine.execute_orders(signals, prices)
        
        print((f"✅ Execution Complete. Trades executed: {len(signals)}"))
        
        # 3. Summary
        pt = PaperTrader()
        balance = pt.get_current_balance()
        pos = pt.get_positions()
        print("\n--- New Portfolio Status ---")
        print(f"Total Equity: ¥{balance['total_equity']:,.0f}")
        print(f"Cash: ¥{balance['cash']:,.0f}")
        print(f"Positions: {len(pos)} held")
        if not pos.empty:
            print(pos[["ticker", "quantity", "entry_price", "current_price"]])
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Error during Auto-Trade: {e}")

if __name__ == "__main__":
    reset_portfolio()
    run_auto_trade()
