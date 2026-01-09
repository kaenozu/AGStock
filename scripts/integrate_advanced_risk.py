"""
fully_automated_trader.py に高度なリスク管理機能を統合するスクリプト

実行方法: python integrate_advanced_risk.py
"""

import re


def integrate_advanced_risk():
    """高度なリスク管理機能を統合"""

    with open("fully_automated_trader.py", "r", encoding="utf-8") as f:
        content = f.read()

    # バックアップ
    with open("fully_automated_trader.py.backup", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ バックアップ作成: fully_automated_trader.py.backup")

    # 統合完了フラグ
    changes_made = []

    # 1. scan_market メソッドに市場急落チェックを追加
    pattern1 = r'(def scan_market\(self\).*?"""市場をスキャン.*?""".*?self\.log\("市場スキャン開始\.\.\."\))'
    replacement1 = r"""\1
        
        # 🚨 市場急落チェック
        allow_buy_market, market_reason = self.advanced_risk.check_market_crash(self.log)
        if not allow_buy_market:
            self.log(f"⚠️ 市場急落のため新規BUY停止: {market_reason}", "WARNING")"""

    if re.search(pattern1, content, re.DOTALL):
        content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
        changes_made.append("市場急落チェック")

    # 2. BUYシグナル生成箇所に相関チェックを追加
    # "if last_signal == 1 and not is_held and allow_buy:" の直後に追加
    pattern2 = r"(if last_signal == 1 and not is_held and allow_buy:)"
    replacement2 = r"""\1
                        
                        # 📊 銘柄相関チェック
                        positions = self.pt.get_positions()
                        existing_tickers = list(positions.index) if not positions.empty else []
                        allow_corr, corr_reason = self.advanced_risk.check_correlation(ticker, existing_tickers, self.log)
                        if not allow_corr:
                            self.log(f"  {ticker}: {corr_reason}")
                            continue"""

    if re.search(pattern2, content):
        content = re.sub(pattern2, replacement2, content, count=1)
        changes_made.append("銘柄相関チェック")

    # 3. ファイルに書き戻し
    with open("fully_automated_trader.py", "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n✅ 統合完了: {len(changes_made)}個の機能を追加")
    for change in changes_made:
        print(f"   - {change}")

    print("\n📝 注意:")
    print("   - ドローダウン保護は daily_routine の先頭に手動で追加してください")
    print("   - バックアップ: fully_automated_trader.py.backup")
    print("\n🧪 テスト実行:")
    print("   python test_advanced_risk.py")


if __name__ == "__main__":
    integrate_advanced_risk()
