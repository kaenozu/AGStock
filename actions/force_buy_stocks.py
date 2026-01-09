import sqlite3
import pandas as pd
import sys
import os
import datetime

# Add root to python path
sys.path.append(os.getcwd())

from src.paper_trader import PaperTrader

def reset_portfolio():
    print("🔄 Resetting Portfolio...")
    try:
        conn = sqlite3.connect("paper_trading.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM positions")
        cursor.execute("DELETE FROM orders")
        
        # Reset Cash to 10M for buying power
        cursor.execute("SELECT initial_capital FROM accounts WHERE id=1")
        row = cursor.fetchone()
        initial_cap = row[0] if row else 10000000
        cursor.execute("UPDATE accounts SET current_balance = ? WHERE id=1", (initial_cap,))
            
        conn.commit()
        conn.close()
        print("✅ Portfolio Reset Complete.")
    except Exception as e:
        print(f"❌ Error resetting portfolio: {e}")

class Order:
    def __init__(self, ticker, action, quantity, price):
        self.ticker = ticker
        self.action = action
        self.quantity = quantity
        self.price = price
    def __repr__(self):
        return f"{self.action} {self.quantity} {self.ticker} @ {self.price}"

def force_buy():
    print("🚀 Force Buying Stocks (Fallback Mode)...")
    pt = PaperTrader()
    
    # Target Stocks (Major Japanese Cos) & Approx Prices (to avoid fetching if slow, or just fetch)
    # Using fixed reasonable prices for demo/force population if fetch fails, 
    # but let's try to fetch recent price or use hardcoded reasonable defaults.
    targets = [
        {"ticker": "7203.T", "name": "Toyota", "qty": 100, "price": 2800},
        {"ticker": "9984.T", "name": "SoftBank G", "qty": 100, "price": 8500},
        {"ticker": "6758.T", "name": "Sony G", "qty": 100, "price": 13000},
        {"ticker": "8411.T", "name": "Mizuho", "qty": 100, "price": 3100},
        {"ticker": "9433.T", "name": "KDDI", "qty": 100, "price": 4500},
        {"ticker": "^N225", "name": "Nikkei 225", "qty": 1, "price": 39000}, # Index for viewing
    ]
    
    for t in targets:
        # Try to get real price?
        try:
            import yfinance as yf
            tick = yf.Ticker(t['ticker'])
            hist = tick.history(period="1d")
            if not hist.empty:
                real_price = float(hist["Close"].iloc[-1])
                t['price'] = real_price
                print(f"  Fetched price for {t['ticker']}: {real_price}")
        except:
            print(f"  Using default price for {t['ticker']}: {t['price']}")
            
        order = Order(t['ticker'], "BUY", t['qty'], t['price'])
        success = pt.execute_order(order)
        if success:
            print(f"✅ Bought {t['ticker']} ({t['qty']} units)")
        else:
            print(f"❌ Failed to buy {t['ticker']}")

    balance = pt.get_current_balance()
    pos = pt.get_positions()
    print("\n--- New Portfolio Status ---")
    print(f"Total Equity: ¥{balance['total_equity']:,.0f}")
    print(f"Positions: {len(pos)} held")

if __name__ == "__main__":
    reset_portfolio()
    force_buy()
