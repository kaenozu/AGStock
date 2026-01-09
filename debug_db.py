import sqlite3
import pandas as pd

def check_db():
    conn = sqlite3.connect("paper_trading.db")
    
    print("--- ACCOUNTS ---")
    try:
        df_acc = pd.read_sql_query("SELECT * FROM accounts", conn)
        print(df_acc)
    except Exception as e:
        print(f"Error reading accounts: {e}")
        
    print("\n--- POSITIONS ---")
    try:
        df_pos = pd.read_sql_query("SELECT * FROM positions", conn)
        print(df_pos)
    except Exception as e:
        print(f"Error reading positions: {e}")
        
    print("\n--- ORDERS ---")
    try:
        df_ord = pd.read_sql_query("SELECT * FROM orders ORDER BY timestamp DESC LIMIT 10", conn)
        print(df_ord)
    except Exception as e:
        print(f"Error reading orders: {e}")
        
    print("\n--- BALANCE HISTORY (Last 5) ---")
    try:
        df_bal = pd.read_sql_query("SELECT * FROM balance ORDER BY date DESC LIMIT 5", conn)
        print(df_bal)
    except Exception as e:
        print(f"Error reading balance: {e}")
        
    conn.close()

if __name__ == "__main__":
    check_db()
