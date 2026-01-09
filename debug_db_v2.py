import sqlite3
import pandas as pd
import os

def check_db():
    if not os.path.exists("paper_trading.db"):
        print("Database file NOT FOUND!")
        return
        
    conn = sqlite3.connect("paper_trading.db")
    
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
    print(f"Tables in DB: {tables['name'].tolist()}")
    
    print("\n--- ACCOUNTS ---")
    try:
        print(pd.read_sql_query("SELECT * FROM accounts", conn))
    except Exception as e: print(e)
    
    print("\n--- POSITIONS ---")
    try:
        pos = pd.read_sql_query("SELECT * FROM positions", conn)
        if pos.empty: print("No positions found.")
        else: print(pos)
    except Exception as e: print(e)
    
    print("\n--- ORDERS (Last 20) ---")
    try:
        ord = pd.read_sql_query("SELECT * FROM orders ORDER BY timestamp DESC LIMIT 20", conn)
        if ord.empty: print("No orders found.")
        else: print(ord)
    except Exception as e: print(e)
    
    print("\n--- BALANCE HISTORY (Last 10) ---")
    try:
        bal = pd.read_sql_query("SELECT * FROM balance ORDER BY date DESC LIMIT 10", conn)
        if bal.empty: print("No balance history found.")
        else: print(bal)
    except Exception as e: print(e)
        
    conn.close()

if __name__ == "__main__":
    check_db()
