"""
AGStock Headless Trader (Daemon Mode)
Runs the automated trading system in a background loop without UI.
"""

import argparse
import logging
import sys
import time
from datetime import datetime

from src.cache_config import install_cache
from src.constants import NIKKEI_225_TICKERS
from src.live_trading import LiveTradingEngine, PaperBroker
from src.smart_notifier import SmartNotifier
from src.strategies import (BollingerBandsStrategy, MLStrategy, RSIStrategy,
                            SMACrossoverStrategy)

# Configure Logging
log_file = "headless_trader.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("HeadlessTrader")


def setup_strategies(tickers):
    """
    Setup default strategies for tickers.
    In a real scenario, this would load optimal params from a file.
    """
    strategies = {}
    # For now, assign a mix of strategies or a default robust one
    for ticker in tickers:
        # Improved logic: Use ML for Tech/Auto, BB for others, etc.
        # Defaulting to combined or SMA for safety in headless demo
        strategies[ticker] = SMACrossoverStrategy(short_window=5, long_window=20)
    return strategies


def main():
    parser = argparse.ArgumentParser(description="AGStock Headless Trader")
    parser.add_argument("--dry-run", action="store_true", help="Run without executing orders")
    parser.add_argument("--interval", type=int, default=3600, help="Loop interval in seconds (default: 1 hour)")
    args = parser.parse_args()

    install_cache()
    logger.info("🚀 Starting AGStock Headless Trader...")

    if args.dry_run:
        logger.info("⚠️ DRY RUN MODE: Orders will not be executed.")

    # Initialize Components
    broker = PaperBroker()
    notifier = SmartNotifier()  # Assumes env vars or config loaded

    # Initialize AutoSelector
    from src.auto_selector import AutoSelector

    selector = AutoSelector()

    # Initial Configuration for "Today"
    config = selector.select_daily_config()
    strategies = {}
    strategy_cls = config["strategy_cls"]
    strategy_params = config["strategy_params"]
    selected_tickers = config["tickers"]
    regime_info = config["regime_info"]

    # Instantiate strategies for selected tickers
    for ticker in selected_tickers:
        strategies[ticker] = strategy_cls(**strategy_params)

    # Notification
    start_msg = (
        "🤖 AGStock Hyper-Autonomous Mode 起動\n"
        f"📊 市場環境: {regime_info['regime_name']}\n"
        f"🎯 選定銘柄 ({len(selected_tickers)}): {', '.join(selected_tickers)}\n"
        f"🧠 採用戦略: {strategy_cls.__name__}\n"
        f"⏱️ チェック間隔: {args.interval}秒"
    )

    # Check if LINE enabled in config (accessed via protected attrib or just try sending)
    # Wrapper helper
    def send_system_msg(msg):
        # Quick hack: try line notify using stored token in notifier instance if possible
        # Or better, use notifier.send_line_notify if we can get config.
        # SmartNotifier stores config in self.notification_settings.
        line_conf = notifier.notification_settings.get("line", {})
        if line_conf.get("enabled"):
            notifier.send_line_notify(msg, token=line_conf.get("token"))
        else:
            logger.info(f"System Notification (Text only): {msg}")

    send_system_msg(start_msg)

    engine = LiveTradingEngine(broker=broker, strategies=strategies, tickers=selected_tickers, enable_risk_guard=True)
    engine.interval_seconds = args.interval

    try:
        # Start the loop
        # Note: To fully support daily switching, we ideally run engine.run_cycle() here in a loop
        # checking dates. For now, relying on engine.start() which blocks forever.
        engine.start()
    except KeyboardInterrupt:
        logger.info("🛑 Stopping Trader...")
        send_system_msg("🛑 自動運転モードを停止しました。")
    except Exception as e:
        logger.critical(f"🔥 Critical Error: {e}", exc_info=True)
        send_system_msg(f"🔥 エラーで停止しました: {e}")
        raise


if __name__ == "__main__":
    main()
