"""
高度なリスク管理機能のテストスクリプト

使い方:
  python test_advanced_risk.py
"""
from src.advanced_risk import AdvancedRiskManager
from src.paper_trader import PaperTrader
import json

def test_advanced_risk():
    """高度なリスク管理機能のテスト"""
    
    # 設定読み込み
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except:
        config = {
            "auto_trading": {
                "max_daily_loss_pct": -3.0,
                "market_crash_threshold": -3.0,
                "max_correlation": 0.7
            }
        }
    
    # インスタンス作成
    pt = PaperTrader()
    risk_mgr = AdvancedRiskManager(config)
    
    def logger(msg, level="INFO"):
        print(f"[{level}] {msg}")
    
    print("=" * 60)
    print("高度なリスク管理機能テスト")
    print("=" * 60)
    
    # 1. ドローダウン保護テスト
    print("\n1. ドローダウン保護チェック")
    is_safe, reason, signals = risk_mgr.check_drawdown_protection(pt, logger)
    print(f"   結果: {'✅ OK' if is_safe else '🚨 NG'}")
    print(f"   理由: {reason}")
    if signals:
        print(f"   緊急決済シグナル: {len(signals)}件")
    
    # 2. 市場急落チェック
    print("\n2. 市場急落チェック")
    allow_buy, reason = risk_mgr.check_market_crash(logger)
    print(f"   結果: {'✅ BUY可能' if allow_buy else '🚨 BUY停止'}")
    print(f"   理由: {reason}")
    
    # 3. 銘柄相関チェック
    print("\n3. 銘柄相関チェック")
    positions = pt.get_positions()
    if not positions.empty:
        existing_tickers = list(positions.index)
        test_ticker = "AAPL"  # テスト用
        allow, reason = risk_mgr.check_correlation(test_ticker, existing_tickers, logger)
        print(f"   新規銘柄: {test_ticker}")
        print(f"   既存銘柄: {existing_tickers}")
        print(f"   結果: {'✅ OK' if allow else '🚨 NG'}")
        print(f"   理由: {reason}")
    else:
        print("   既存ポジションなし（スキップ）")
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)
    
    print("\n📝 次のステップ:")
    print("  1. fully_automated_trader.py の daily_routine() の先頭に")
    print("     ドローダウン保護チェックを追加")
    print("  2. scan_market() の先頭に市場急落チェックを追加")
    print("  3. BUYシグナル生成時に相関チェックを追加")

if __name__ == "__main__":
    test_advanced_risk()
