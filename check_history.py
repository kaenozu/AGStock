
import sqlite3
import pandas as pd
from src.paper_trader import PaperTrader

def check_history():
    pt = PaperTrader()
    df = pd.read_sql("SELECT * FROM orders ORDER BY date DESC LIMIT 10", pt.conn)
    print("\n=== Trade History ===")
    print(df[['date', 'ticker', 'action', 'quantity', 'price', 'reason']])
    pt.close()

if __name__ == "__main__":
    check_history()
