"""
オールインワン実行スクリプト

全機能をワンクリックで実行
"""

import os
import sys
from datetime import datetime


def print_header(title: str):
    """ヘッダー表示"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def run_morning_brief():
    """モーニングブリーフ実行"""
    print_header("📊 モーニングブリーフ")
    try:
        from morning_brief import MorningBrief

        brief = MorningBrief()
        brief.send_brief()
        print("✅ モーニングブリーフ送信完了")
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def run_auto_invest():
    """自動投資実行"""
    print_header("🤖 フルオート投資")
    try:
        from fully_automated_trader import FullyAutomatedTrader

        trader = FullyAutomatedTrader()
        trader.daily_routine()
        print("✅ 自動投資完了")
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def run_smart_alerts():
    """スマートアラート実行"""
    print_header("🔔 スマートアラート")
    try:
        from smart_alerts import SmartAlerts

        alerts = SmartAlerts()
        alerts.run()
        print("✅ アラートチェック完了")
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def run_performance_tracker():
    """パフォーマンストラッ ⫯カー実行"""
    print_header("📈 パフォーマンストラッカー")
    try:
        from performance_tracker import PerformanceTracker

        tracker = PerformanceTracker()

        # 月次レポート生成
        report = tracker.generate_monthly_report()
        print(report)

        # 保存
        report_path = tracker.save_report(report)
        excel_path = tracker.export_to_excel()

        print(f"\n✅ レポート生成完了")
        print(f"   テキスト: {report_path}")
        print(f"   Excel: {excel_path}")
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def run_all():
    """すべて実行"""
    print("\n" + "🚀 AGStock オールインワン実行")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {}

    # 1. モーニングブリーフ
    results["morning_brief"] = run_morning_brief()

    # 2. フルオート投資
    results["auto_invest"] = run_auto_invest()

    # 3. スマートアラート
    results["smart_alerts"] = run_smart_alerts()

    # 4. パフォーマンストラッカー
    results["performance_tracker"] = run_performance_tracker()

    # 結果サマリー
    print_header("📊 実行結果サマリー")
    total = len(results)
    success = sum(1 for v in results.values() if v)

    for task, status in results.items():
        status_emoji = "✅" if status else "❌"
        print(f"{status_emoji} {task}")

    print(f"\n成功: {success}/{total}")

    if success == total:
        print("\n🎉 すべて成功！")
        return 0
    else:
        print("\n⚠️ 一部失敗")
        return 1


def main():
    """メイン実行"""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        commands = {
            "brief": run_morning_brief,
            "invest": run_auto_invest,
            "alerts": run_smart_alerts,
            "performance": run_performance_tracker,
            "all": run_all,
        }

        if command in commands:
            return commands[command]()
        else:
            print(f"不明なコマンド: {command}")
            print("\n使用方法:")
            print("  python run_all.py [command]")
            print("\nコマンド:")
            print("  brief       - モーニングブリーフのみ")
            print("  invest      - フルオート投資のみ")
            print("  alerts      - スマートアラートのみ")
            print("  performance - パフォーマンスレポートのみ")
            print("  all         - すべて実行（デフォルト）")
            return 1
    else:
        # 引数なしの場合はすべて実行
        return run_all()


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n中断されました。")
        sys.exit(0)
