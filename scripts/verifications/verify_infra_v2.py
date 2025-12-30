import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.getcwd())

from src.paths import DATA_DIR, LOGS_DIR, STOCK_DATA_DB
from src.utils.cache_mgr import persistent_cache, get_cache
from src.utils.currency import CurrencyConverter
from src.utils.db_utils import optimize_sqlite_connection
import sqlite3

def test_paths():
    print("Testing Paths...")
    assert DATA_DIR.exists(), "DATA_DIR missing"
    assert LOGS_DIR.exists(), "LOGS_DIR missing"
    print(f"✅ Paths OK: {DATA_DIR}")

def test_cache():
    print("Testing Persistent Cache...")
    
    @persistent_cache(expire=10)
    def expensive_func(x):
        return x * 2
        
    res1 = expensive_func(21)
    assert res1 == 42
    
    # Check if actually in cache
    cache = get_cache()
    key = f"expensive_func:(21,):{{}}"
    assert cache.get(key) == 42
    print("✅ Cache OK")

def test_currency():
    print("Testing Currency Converter...")
    rate = CurrencyConverter.get_rate("USD", "JPY")
    print(f"USD/JPY Rate: {rate}")
    assert rate > 100
    
    jpy_val = CurrencyConverter.convert(100, "USD")
    print(f"$100 = ¥{jpy_val}")
    assert jpy_val == 100 * rate
    print("✅ Currency OK")

def test_db_optimization():
    print("Testing DB Optimization...")
    db_path = "data/test_opt.db"
    conn = sqlite3.connect(db_path)
    optimize_sqlite_connection(conn)
    
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode;")
    mode = cursor.fetchone()[0]
    print(f"Journal Mode: {mode}")
    assert mode.lower() == "wal"
    conn.close()
    os.remove(db_path)
    print("✅ DB Optimization OK")

if __name__ == "__main__":
    print("=== AGStock New Features Self-Test ===")
    try:
        test_paths()
        test_cache()
        test_currency()
        test_db_optimization()
        print("\n✨ ALL TESTS PASSED ✨")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
