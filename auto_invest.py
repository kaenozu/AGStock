"""
🚀 AGStock フルオートシステム - ワンクリック起動版

使い方:
    python auto_invest.py

これだけ！あとは全自動です。
"""
import sys
import os
from datetime import datetime
import json

# シンプルな出力
def print_header():
    print("\n" + "="*60)
    print("🚀 AGStock フルオート投資システム")
    print("="*60 + "\n")

def print_step(step: str, message: str = ""):
    """進捗表示"""
    symbol = "✓" if "完了" in message or "OK" in message else "►"
    print(f"{symbol} {step} {message}")

def main():
    print_header()
    
    # ステップ1: システムチェック
    print_step("システムチェック", "")
    
    try:
        from src.cache_config import install_cache
        install_cache()
        print_step("", "キャッシュ: OK")
    except Exception as e:
        print_step("", f"キャッシュ: スキップ ({e})")
    
    # ステップ2: 設定確認
    print_step("設定確認", "")
    
    config_path = "config.json"
    if not os.path.exists(config_path):
        # デフォルト設定作成
        default_config = {
            "paper_trading": {
                "initial_capital": 1000000,
                "enabled": True
            },
            "auto_trading": {
                "enabled": True,
                "max_daily_trades": 5,
                "risk_per_trade": 0.02
            },
            "notifications": {
                "line": {"enabled": False, "token": ""},
                "discord": {"enabled": False, "webhook_url": ""}
            }
        }
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        print_step("", f"設定ファイル作成: {config_path}")
    else:
        print_step("", "設定ファイル: OK")
    
    # ステップ3: フルオート起動
    print_step("フルオート起動", "")
    
    try:
        from fully_automated_trader import FullyAutomatedTrader
        
        print("\n" + "-"*60)
        print("📊 自動投資開始...")
        print("-"*60 + "\n")
        
        trader = FullyAutomatedTrader(config_path)
        trader.daily_routine()
        
        print("\n" + "="*60)
        print("✅ 自動投資完了！")
        print("="*60 + "\n")
        
        # レポート表示
        print_summary(trader)
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        print("\nトラブルシューティング:")
        print("1. Streamlitアプリが起動していないか確認")
        print("2. 依存パッケージをインストール: pip install -r requirements.txt")
        print("3. データベースを確認: paper_trading.db")
        return 1
    
    return 0


def print_summary(trader):
    """結果サマリーを表示"""
    try:
        from src.paper_trader import PaperTrader
        
        pt = PaperTrader()
        balance = pt.get_current_balance()
        positions = pt.get_positions()
        
        print("📈 現在の状況:")
        print(f"   総資産:      ¥{balance['total_equity']:,.0f}")
        print(f"   現金:        ¥{balance['cash']:,.0f}")
        print(f"   投資額:      ¥{balance['invested_amount']:,.0f}")
        print(f"   含み損益:    ¥{balance['unrealized_pnl']:+,.0f}")
        print(f"   保有銘柄数:  {len(positions)}銘柄")
        
        if not positions.empty:
            print("\n📋 保有銘柄:")
            for idx, pos in positions.head(5).iterrows():
                pnl_pct = (pos['unrealized_pnl'] / (pos['entry_price'] * pos['quantity'])) * 100
                print(f"   {pos['ticker']:<12} {pos['quantity']:>6}株  {pnl_pct:+.1f}%")
        
        print("\n💡 次のステップ:")
        print("   • 毎日自動実行: タスクスケジューラーに登録")
        print("   • 結果確認: streamlit run app.py")
        print("   • 通知設定: config.json を編集")
        
    except Exception as e:
        print(f"サマリー表示エラー: {e}")


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n中断されました。")
        sys.exit(0)
