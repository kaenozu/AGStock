import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(os.getcwd())

from src.data_manager import DataManager
from src.paper_trader import PaperTrader

def run_optimization():
    print("=" * 60)
    print("🚀 AGStock データベース最適化 (v2.0)")
    print("=" * 60)
    
    # 1. DataManager (stock_data.db / parquet metadata)
    print("\n[1/2] DataManagerの最適化中...")
    try:
        dm = DataManager()
        dm.create_indexes()
        dm.vacuum_db()
        print("✅ DataManagerの最適化が完了しました。")
    except Exception as e:
        print(f"❌ DataManagerエラー: {e}")
    
    # 2. PaperTrader (paper_trading.db)
    print("\n[2/2] PaperTraderデータベースの最適化中...")
    try:
        pt = PaperTrader()
        pt.optimize_database()
        pt.close()
        print("✅ PaperTraderの最適化が完了しました。")
    except Exception as e:
        print(f"❌ PaperTraderエラー: {e}")
    
    print("\n" + "=" * 60)
    print("✨ すべてのデータベースが最適な状態になりました。")
    print("=" * 60)

if __name__ == "__main__":
    run_optimization()
