"""
AGStock 自動取引デーモン
常駐プロセスとして動作し、市場を監視して自動取引を実行します。
"""

import datetime
import logging
import sys
import time
import traceback

import schedule
from fully_automated_trader import FullyAutomatedTrader

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/daemon.log", encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger("Daemon")


def is_market_open():
    """市場が開いているか判定（日本株基準: 平日 9:00-15:00）"""
    now = datetime.datetime.now()

    # 土日は休み
    if now.weekday() >= 5:
        return False

    # 祝日判定は簡易的に省略（必要ならjpholidayライブラリなどを導入）

    current_time = now.time()
    start_time = datetime.time(9, 0)
    end_time = datetime.time(15, 0)

    return start_time <= current_time <= end_time


def job():
    """定期実行するジョブ"""
    logger.info("⏰ 定期ジョブ開始")

    try:
        trader = FullyAutomatedTrader()

        # 市場が開いているか、または強制実行モードなら実行
        if is_market_open():
            logger.info("市場オープン中: 取引ロジック実行")
            trader.daily_routine()
        else:
            logger.info("市場クローズ中: データ収集・分析のみ実行（またはスキップ）")
            # 夜間でも先物や米国株のために実行する場合はここを調整
            # 今回は簡易的に実行
            trader.daily_routine()

        logger.info("✅ 定期ジョブ完了")

    except Exception as e:
        logger.error(f"❌ ジョブ実行エラー: {e}")
        logger.error(traceback.format_exc())

        # エラー通知
        try:
            from src.smart_notifier import SmartNotifier

            notifier = SmartNotifier()
            notifier.send_line_notify(f"⚠️ AGStock デーモンエラー: {e}")
        except:
            pass


def run_daemon():
    logger.info("🚀 AGStock デーモン起動")

    # 初回実行
    job()

    # スケジュール設定
    # 毎時0分、30分に実行
    schedule.every().hour.at(":00").do(job)
    schedule.every().hour.at(":30").do(job)

    # 毎朝8:30に準備実行
    schedule.every().day.at("08:30").do(job)

    logger.info("スケジュール設定完了。待機中...")

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            logger.info("🛑 デーモン停止")
            break
        except Exception as e:
            logger.error(f"予期せぬエラー: {e}")
            time.sleep(60)


if __name__ == "__main__":
    run_daemon()
