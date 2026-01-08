import sqlite3
import pandas as pd
from datetime import datetime

def calculate_daily_pnl_standalone(db_path, current_total_equity):
    """
    Calculates Daily PnL by comparing current_total_equity with the last recorded equity
    from the previous day (strictly < today).
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Get the latest record that is strictly BEFORE today
        cursor.execute("SELECT total_equity FROM balance WHERE date < ? ORDER BY date DESC LIMIT 1", (today_str,))
        row = cursor.fetchone()
        
        conn.close()
        
        last_equity = 0.0
        if row:
            last_equity = row[0]
            # If last_equity is 0 (unlikely but possible), PnL is just the current equity change from 0?
            # Or should be current equity - initial capital?
            # Assuming last_equity is valid if found.
            
        daily_pnl = current_total_equity - last_equity
        return daily_pnl, last_equity
        
    except Exception as e:
        print(f"Error in standalone PnL calc: {e}")
        return 0.0, 0.0
