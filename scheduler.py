"""
スケジューラー - 効率的な定期実行

APSchedulerを使用してタスクを定期実行
"""

import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

# ログ設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_morning_brief():
    """モーニングブリーフ実行"""
    logger.info("モーニングブリーフ開始")
    try:
        from morning_brief import MorningBrief

        brief = MorningBrief()
        brief.send_brief()
        logger.info("モーニングブリーフ完了")
    except Exception as e:
        logger.error(f"モーニングブリーフエラー: {e}")


def run_auto_invest():
    """自動投資実行"""
    logger.info("自動投資開始")
    try:
        from fully_automated_trader import FullyAutomatedTrader

        trader = FullyAutomatedTrader()
        trader.daily_routine()
        logger.info("自動投資完了")
    except Exception as e:
        logger.error(f"自動投資エラー: {e}")


def run_smart_alerts():
    """スマートアラート実行"""
    logger.info("スマートアラート開始")
    try:
        from smart_alerts import SmartAlerts

        alerts = SmartAlerts()
        alerts.run()
        logger.info("スマートアラート完了")
    except Exception as e:
        logger.error(f"スマートアラートエラー: {e}")


def run_performance_tracker():
    """パフォーマンストラッカー実行"""
    logger.info("パフォーマンストラッカー開始")
    try:
        from performance_tracker import PerformanceTracker

        tracker = PerformanceTracker()
        report = tracker.generate_monthly_report()
        print(report)
        tracker.save_report(report)
        logger.info("パフォーマンストラッカー完了")
    except Exception as e:
        logger.error(f"パフォーマンストラッカーエラー: {e}")


def main():
    """メイン実行"""
    scheduler = BlockingScheduler()

    # スケジュール登録
    # モーニングブリーフ: 毎日8:30
    scheduler.add_job(run_morning_brief, "cron", hour=8, minute=30)

    # 自動投資: 毎日9:00
    scheduler.add_job(run_auto_invest, "cron", hour=9, minute=0)

    # スマートアラート: 9-17時、毎時
    scheduler.add_job(run_smart_alerts, "cron", hour="9-17", minute=0)

    # パフォーマンストラッカー: 毎日21:00
    scheduler.add_job(run_performance_tracker, "cron", hour=21, minute=0)

    logger.info("スケジューラー開始")
    logger.info("登録されたジョブ:")
    for job in scheduler.get_jobs():
        logger.info(f"  {job}")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("スケジューラー停止")


if __name__ == "__main__":
    main()
