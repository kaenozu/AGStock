
import sqlite3
import pandas as pd
from src.paper_trader import PaperTrader

def check_cash():
    pt = PaperTrader()
    balance = pt.get_current_balance()
    print("=== Current Balance ===")
    print(balance)
    
    print("\n=== Positions ===")
    positions = pt.get_positions()
    if not positions.empty:
        print(f"Total Positions Value: {positions['market_value'].sum()}")
        print(positions[['quantity', 'entry_price', 'current_price', 'market_value']])
    
    # Check DB history for cash
    df = pd.read_sql("SELECT * FROM balance ORDER BY date DESC LIMIT 5", pt.conn)
    print("\n=== Balance History ===")
    print(df)

    pt.close()

if __name__ == "__main__":
    check_cash()
