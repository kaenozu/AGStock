"""
スケジューラー - 効率的な定期実行

APSchedulerを使用してタスクを定期実行
"""

import logging
import json
import os
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

# ログ設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

STATUS_FILE = "data/system_status.json"

def update_status(job_name: str, status: str, message: str = ""):
    """システムステータスを更新"""
    try:
        os.makedirs("data", exist_ok=True)
        
        current_data = {}
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    current_data = json.load(f)
            except Exception:
                pass
        
        timestamp = datetime.now().isoformat()
        
        if job_name == "heartbeat":
            current_data["heartbeat"] = timestamp
            current_data["scheduler_status"] = "running"
        else:
            if "jobs" not in current_data:
                current_data["jobs"] = {}
            
            current_data["jobs"][job_name] = {
                "last_run": timestamp,
                "status": status,
                "message": message
            }
            
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=4, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"ステータス更新エラー: {e}")

def run_heartbeat():
    """生存確認"""
    update_status("heartbeat", "alive")



def run_morning_brief():
    """モーニングブリーフ実行"""
    logger.info("モーニングブリーフ開始")
    try:
        update_status("morning_brief", "running", "実行中...")
        from morning_brief import MorningBrief

        brief = MorningBrief()
        brief.send_brief()
        logger.info("モーニングブリーフ完了")
        update_status("morning_brief", "success", "正常終了")
    except Exception as e:
        logger.error(f"モーニングブリーフエラー: {e}")
        update_status("morning_brief", "error", str(e))


def run_auto_invest():
    """自動投資実行"""
    logger.info("自動投資開始")
    try:
        update_status("auto_invest", "running", "実行中...")
        from src.trading.fully_automated_trader import FullyAutomatedTrader

        trader = FullyAutomatedTrader()
        trader.daily_routine()
        logger.info("自動投資完了")
        update_status("auto_invest", "success", "正常終了")
    except Exception as e:
        logger.error(f"自動投資エラー: {e}")
        update_status("auto_invest", "error", str(e))


def run_smart_alerts():
    """スマートアラート実行"""
    logger.info("スマートアラート開始")
    try:
        update_status("smart_alerts", "running", "実行中...")
        from smart_alerts import SmartAlerts

        alerts = SmartAlerts()
        alerts.run()
        logger.info("スマートアラート完了")
        update_status("smart_alerts", "success", "正常終了")
    except Exception as e:
        logger.error(f"スマートアラートエラー: {e}")
        update_status("smart_alerts", "error", str(e))


def run_performance_tracker():
    """パフォーマンストラッカー実行"""
    logger.info("パフォーマンストラッカー開始")
    try:
        update_status("performance_tracker", "running", "実行中...")
        from performance_tracker import PerformanceTracker

        tracker = PerformanceTracker()
        report = tracker.generate_monthly_report()
        print(report)
        tracker.save_report(report)
        logger.info("パフォーマンストラッカー完了")
        update_status("performance_tracker", "success", "正常終了")
    except Exception as e:
        logger.error(f"パフォーマンストラッカーエラー: {e}")
        update_status("performance_tracker", "error", str(e))


def main():
    """メイン実行"""
    scheduler = BlockingScheduler()

    # スケジュール登録
    # モーニングブリーフ: 毎日8:30
    scheduler.add_job(run_morning_brief, "cron", hour=8, minute=30)

    # 自動投資: 毎日9:00
    scheduler.add_job(run_auto_invest, "cron", hour=9, minute=0)

    # スマートアラート: 9-17時、毎時 (Active Defense)
    scheduler.add_job(run_smart_alerts, "cron", hour="9-17", minute=0)

    # パフォーマンストラッカー: 毎日21:00
    scheduler.add_job(run_performance_tracker, "cron", hour=21, minute=0)

    # システムハートビート: 毎分
    scheduler.add_job(run_heartbeat, "interval", minutes=1)

    logger.info("スケジューラー開始")
    logger.info("登録されたジョブ:")
    for job in scheduler.get_jobs():
        logger.info(f"  {job}")

    # 初期ステータス書き込み
    update_status("scheduler", "started", "スケジューラー起動完了")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        update_status("scheduler", "stopped", "スケジューラー停止")
        logger.info("スケジューラー停止")


if __name__ == "__main__":
    main()
