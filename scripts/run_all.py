"""
オールインワン実行スクリプト (v2.0)
全機能を一括で実行し、システムを最新状態に保ちます。
"""

import os
import sys
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.append(os.getcwd())

from src.trading.fully_automated_trader import FullyAutomatedTrader
from src.smart_alerts import SmartAlerts
from scripts.morning_brief import MorningBrief
from src.reporting.weekly_report_html import generate_html_report
from src.paper_trader import PaperTrader


def print_header(title: str):
    """ヘッダー表示"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def run_morning_brief():
    """モーニングブリーフ実行"""
    print_header("📊 モーニングブリーフ")
    try:
        brief = MorningBrief()
        brief.send_brief()
        print("\n✅ モーニングブリーフ完了")
        return True
    except Exception as e:
        print(f"❌ モーニングブリーフエラー: {e}")
        return False


def run_auto_invest():
    """自動投資実行"""
    print_header("🤖 フルオート投資")
    try:
        trader = FullyAutomatedTrader()
        trader.run_daily_cycle()
        print("\n✅ 自動投資完了")
        return True
    except Exception as e:
        print(f"❌ 自動投資エラー: {e}")
        return False


def run_smart_alerts():
    """スマートアラート実行"""
    print_header("🔔 スマートアラート")
    try:
        alerts = SmartAlerts()
        alerts.run()
        print("\n✅ アラートチェック完了")
        return True
    except Exception as e:
        print(f"❌ アラートエラー: {e}")
        return False

def run_weekly_report():
    """週次レポート生成"""
    print_header("📈 週次レポート生成")
    try:
        pt = PaperTrader()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        html_content = generate_html_report(pt, start_date, end_date)
        
        report_dir = "reports"
        os.makedirs(report_dir, exist_ok=True)
        filename = f"weekly_report_{end_date.strftime('%Y%m%d')}.html"
        filepath = os.path.join(report_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"✅ 週次レポート生成完了: {filepath}")
        return True
    except Exception as e:
        print(f"❌ レポート生成エラー: {e}")
        return False

def run_all():
    """すべて実行"""
    print("\n" + "🚀 AGStock オールインワン実行システム (v2.0)")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {}

    # 1. モーニングブリーフ
    results["Morning Brief"] = run_morning_brief()

    # 2. フルオート投資
    results["Auto Invest"] = run_auto_invest()

    # 3. スマートアラート
    results["Smart Alerts"] = run_smart_alerts()

    # 4. 週次レポート (日曜のみ、または明示的な実行)
    if datetime.now().weekday() == 6: # Sunday
        results["Weekly Report"] = run_weekly_report()

    # 結果サマリー
    print_header("📊 実行結果サマリー")
    total = len(results)
    success = sum(1 for v in results.values() if v)

    for task, status in results.items():
        status_emoji = "✅" if status else "❌"
        print(f"{status_emoji} {task}")

    print(f"\n成功: {success}/{total}")

    if success == total:
        print("\n🎉 すべてのルーチンが正常に完了しました！")
        return 0
    else:
        print("\n⚠️ 一部の処理でエラーが発生しました。")
        return 1

def main():
    """メイン実行"""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        commands = {
            "brief": run_morning_brief,
            "invest": run_auto_invest,
            "alerts": run_smart_alerts,
            "report": run_weekly_report,
            "all": run_all,
        }

        if command in commands:
            return 0 if commands[command]() else 1
        else:
            print(f"不明なコマンド: {command}")
            print("\n使用方法:")
            print("  python scripts/run_all.py [command]")
            print("\nコマンド:")
            print("  brief  - モーニングブリーフのみ")
            print("  invest - フルオート投資のみ")
            print("  alerts - スマートアラートのみ")
            print("  report - 週次レポートのみ")
            print("  all    - すべて実行（デフォルト）")
            return 1
    else:
        return run_all()


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n中断されました。")
        sys.exit(0)