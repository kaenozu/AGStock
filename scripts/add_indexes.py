"""データベースインデックス追加スクリプト"""
import sqlite3
import os

DB_FILES = [
    "stock_data.db",
    "cache.db", 
    "paper_trading.db",
    "metrics.db",
    "committee_feedback.db",
    "sentiment_history.db",
]

def add_indexes():
    """各DBにインデックスを追加"""
    for db_file in DB_FILES:
        if not os.path.exists(db_file):
            print(f"⏭️  {db_file} not found, skipping")
            continue
            
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # stock_data.db用インデックス
        if db_file == "stock_data.db":
            indexes = [
                ("idx_date_desc", "stock_data", "date DESC"),
                ("idx_ticker_close", "stock_data", "ticker, close"),
                ("idx_ticker_volume", "stock_data", "ticker, volume DESC"),
            ]
        elif db_file == "paper_trading.db":
            indexes = [
                ("idx_trade_timestamp", "trades", "timestamp DESC"),
                ("idx_trade_ticker", "trades", "ticker"),
            ]
        elif db_file == "cache.db":
            indexes = [
                ("idx_cache_expires", "cache", "expires_at"),
            ]
        else:
            indexes = []
        
        for idx_name, table, columns in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({columns})")
                print(f"✅ Created index {idx_name} on {db_file}")
            except Exception as e:
                print(f"⚠️  Index {idx_name} on {db_file}: {e}")
        
        conn.commit()
        conn.close()
    
    print("\n✅ Index creation complete!")

if __name__ == "__main__":
    add_indexes()
