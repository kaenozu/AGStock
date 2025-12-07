"""
取引データリセットスクリプト
paper_trading.db を削除して、初期状態に戻します。
"""
import os
import sys
from pathlib import Path

def reset_trading_data():
    db_path = Path("paper_trading.db")
    
    if db_path.exists():
        try:
            os.remove(db_path)
            print(f"✅ データベースを削除しました: {db_path.absolute()}")
            print("  次回起動時に新しいデータベースが作成されます。")
        except Exception as e:
            print(f"❌ 削除エラー: {e}")
            sys.exit(1)
    else:
        print("ℹ️ データベースファイルが見つかりません（既にリセット済みか、まだ作成されていません）。")

if __name__ == "__main__":
    reset_trading_data()
