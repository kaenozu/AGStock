"""
ペーパートレードリセットスクリプト
Paper Trading Reset Script

データベースをリセットして、config.jsonの初期資金で再開します。

使い方:
  python reset_paper_trading.py
"""
import os
import json
from pathlib import Path

def reset_paper_trading():
    """ペーパートレードをリセット"""
    
    print("=" * 60)
    print("  📊 ペーパートレードリセット")
    print("=" * 60)
    
    # config.jsonから初期資金を読み込み
    try:
        config_path = Path('config.json')
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            initial_capital = config.get('paper_trading', {}).get('initial_capital', 1000000)
        else:
            initial_capital = 1000000
    except Exception as e:
        print(f"⚠️ config.json読み込みエラー: {e}")
        initial_capital = 1000000
    
    print(f"\n新しい初期資金: ¥{initial_capital:,}")
    print("\n⚠️ 警告: 以下のデータが削除されます:")
    print("  - すべての取引履歴")
    print("  - すべてのポジション")
    print("  - 資産履歴")
    
    response = input("\n本当にリセットしますか? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ キャンセルしました")
        return
    
    # データベースファイルを削除
    db_path = Path('paper_trading.db')
    if db_path.exists():
        try:
            os.remove(db_path)
            print(f"\n✅ {db_path} を削除しました")
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            return
    else:
        print(f"\n⚠️ {db_path} が見つかりません（既にリセット済み？）")
    
    # 新しいPaperTraderインスタンスを作成（自動的にDBを初期化）
    try:
        from src.paper_trader import PaperTrader
        pt = PaperTrader()
        balance = pt.get_current_balance()
        pt.close()
        
        print("\n✅ リセット完了！")
        print(f"\n新しい資産状況:")
        print(f"  総資産: ¥{balance['total_equity']:,}")
        print(f"  現金:   ¥{balance['cash']:,}")
        print(f"  ポジション: 0件")
        
    except Exception as e:
        print(f"\n❌ 初期化エラー: {e}")
        return
    
    print("\n" + "=" * 60)
    print("  🎉 準備完了！")
    print("=" * 60)
    print("\nダッシュボードを起動してください:")
    print("  run_unified_dashboard.bat")
    print("または")
    print("  streamlit run simple_dashboard.py")

if __name__ == "__main__":
    reset_paper_trading()
