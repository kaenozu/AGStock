# """
# 完全自動トレーダー - 個人投資家向け
#     安全策を含む完全自動運用システム
# Refactored to use MarketScanner, TradeExecutor, and DailyReporter.
import datetime
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential
from src.agents.committee import InvestmentCommittee
from src.backup_manager import BackupManager
from src.constants import DEFAULT_VOLATILITY_SYMBOL, FALLBACK_VOLATILITY_SYMBOLS
from src.data_loader import fetch_stock_data, get_latest_price
from src.dynamic_risk_manager import DynamicRiskManager
from src.dynamic_stop import DynamicStopManager
from src.execution import ExecutionEngine
from src.paper_trader import PaperTrader
from src.schemas import AppConfig
from src.smart_notifier import SmartNotifier
from src.utils.logger import get_logger, setup_logger
from src.utils.self_learning import SelfLearningPipeline
# New Components
from src.trading.market_scanner import MarketScanner
from src.trading.trade_executor import TradeExecutor
from src.trading.daily_reporter import DailyReporter
from src.oracle.precog_engine import PrecogEngine
from src.execution.precog_defense import PrecogDefense
# """
class FullyAutomatedTrader:
    def __init__(self, config_path: str = "config.json") -> None:
        pass
#         """初期化"""
self.config_path = config_path
    self.config: Dict[str, Any] = self.load_config(config_path)
# ログファイル
self.log_file: str = "logs/auto_trader.log"
    os.makedirs("logs", exist_ok=True)
    setup_logger("AutoTrader", "logs", "auto_trader.log")
    self.logger = get_logger("AutoTrader")
# コアコンポーネント
self.pt = PaperTrader()
    self.notifier = SmartNotifier(self.config)
        self.engine = ExecutionEngine(self.pt)
# self.backup_manager logic...
try:
            self.backup_manager = BackupManager()
        except Exception:
            self.backup_manager = None
# AI Investment Committee
self.ai_config = self.config.get("ai_committee", {})
        self.ai_enabled = self.ai_config.get("enabled", False)
            if self.ai_enabled:
                try:
                    app_config = AppConfig(**self.config) if self.config else None
                self.committee = InvestmentCommittee(app_config)
                self.log("🤖 AI投資委員会: 有効 (Active)")
            except Exception as e:
                self.log(f"AI委員会初期化エラー: {e}", "ERROR")
                self.committee = None
                self.ai_enabled = False
        else:
            self.committee = None
            self.log("🤖 AI投資委員会: 無効 (Disabled)")
            self.risk_config: Dict[str, Any] = self.config.get("auto_trading", {})
        self.backup_enabled: bool = True
        self.emergency_stop_triggered: bool = False
        self._last_vix_level = None
# --- Initialize New Components ---
self.market_scanner = MarketScanner(self.config, self.logger)
        self.trade_executor = TradeExecutor(self.config, self.engine, self.logger)
        self.daily_reporter = DailyReporter(self.config, self.pt, self.logger, self.config_path)
# Keep Legacy/Specific Managers for top-level usage if needed
self.dynamic_stop_manager = DynamicStopManager()
        self.risk_manager = DynamicRiskManager(self.market_scanner.regime_detector)
        self.learning_pipeline = SelfLearningPipeline(self.config)
        self.precog_engine = PrecogEngine()
        self.precog_defense = PrecogDefense()
            self.log("フル自動トレーダー初期化完了 (Precog Intelligence Enabled)")
    def load_config(self, config_path: str) -> Dict[str, Any]:
#         """設定ファイルを読み込み"""
try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "paper_trading": {"initial_capital": 1000000},
                "auto_trading": {"max_daily_trades": 5, "daily_loss_limit_pct": -5.0, "max_vix": 40.0},
                "notifications": {"line": {"enabled": False}},
            }
    def log(self, message: str, level: str = "INFO") -> None:
#         """ログ出力"""
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
            if level == "INFO":
                self.logger.info(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "CRITICAL":
            self.logger.critical(message)
        else:
            self.logger.debug(message)
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(log_message + "\n")
        except (OSError, IOError):
            pass
    def calculate_daily_pnl(self) -> float:
#         """本日の損益を計算"""
try:
            history = self.pt.get_trade_history()
            if history.empty:
                return 0.0
                today = datetime.date.today()
            if "timestamp" not in history.columns:
                return 0.0
                if not pd.api.types.is_datetime64_any_dtype(history["timestamp"]):
                    history["timestamp"] = pd.to_datetime(history["timestamp"])
                today_trades = history[history["timestamp"].dt.date == today]
            if today_trades.empty:
                return 0.0
                return float(today_trades["realized_pnl"].sum()) if "realized_pnl" in today_trades.columns else 0.0
        except Exception as e:
            self.log(f"日次損益計算エラー: {e}", "WARNING")
            return 0.0
    def _get_vix_level(self) -> Optional[float]:
#         """MarketScanner has this logic now, reusing it or delegating"""
# Delegating to market_scanner's internal method if accessible, or just duplicate simple logic/cache
return self.market_scanner._get_vix_level()
    def is_safe_to_trade(self) -> Tuple[bool, str]:
#         """取引が安全か確認"""
daily_pnl = self.calculate_daily_pnl()
        balance = self.pt.get_current_balance()
        total_equity = float(balance.get("total_equity", 0.0))
        cash = float(balance.get("cash", 0.0))
            daily_loss_pct = (daily_pnl / total_equity) * 100 if total_equity > 0 else 0
        daily_loss_limit = float(self.risk_config.get("daily_loss_limit_pct", -5.0))
            if daily_loss_pct < daily_loss_limit:
                return False, f"日次損失制限を超過: {daily_loss_pct:.2f}%"
            vix_level = self._get_vix_level()
        max_vix = float(self.risk_config.get("max_vix", 40.0))
        if vix_level is not None:
            if vix_level > max_vix:
                return False, f"市場ボラティリティが高すぎます (VIX: {vix_level:.1f})"
        else:
            self.log("VIX取得に失敗しました（キャッシュも無し）: ボラティリティチェックをスキップ", "WARNING")
            if cash < 10000:
                return False, "現金残高が不足しています"
            return True, "OK"
    def emergency_stop(self, reason: str) -> None:
#         """緊急停止を実行"""
self.emergency_stop_triggered = True
        self.log(f"🚨 緊急停止: {reason}", "CRITICAL")
        if self.backup_manager:
            try:
                self.backup_manager.auto_backup()
            except Exception:
                pass
            try:
                token = self.config.get("notifications", {}).get("line", {}).get("token")
            if token:
                self.notifier.send_line_notify(f"🚨 緊急停止: {reason}", token=token)
        except Exception:
            pass
    def evaluate_positions(self) -> List[Dict]:
        pass
#         """
#         保有ポジションを評価し、損切り・利確のシグナルを生成
#         Note: This could also be moved to MarketScanner or a PositionMonitor.
#         Keeping here for now but using _fetch_data via MarketScanner if possible.
#                 positions = self.pt.get_positions()
#         if positions.empty:
#             return []
#             if "ticker" in positions.columns:
#                 tickers = positions["ticker"].tolist()
#         else:
#             tickers = positions.index.tolist()
#         tickers = [str(t) for t in tickers if t]
#         if not tickers:
#             return []
# # Re-use MarketScanner's fetcher? Or just direct
#         try:
#             data_map = fetch_stock_data(tickers, period="2y")
#         except Exception:
#             return []
#             signals: List[Dict] = []
#             for idx, position in positions.iterrows():
#                 ticker = str(position.get("ticker", idx))
#             if not ticker or ticker not in data_map:
#                 continue
#                 df = data_map[ticker]
#             if df.empty:
#                 continue
#                 latest_price = get_latest_price(df)
#             entry_price = float(position.get("entry_price") or position.get("avg_price") or 0.0)
#             quantity = float(position.get("quantity", 0))
#             if entry_price == 0 or quantity <= 0:
#                 continue
#                 pnl_pct = (latest_price - entry_price) / entry_price
# # Dynamic Stop
#             if hasattr(self, "dynamic_stop_manager"):
#                 highest_price = float(position.get("highest_price") or entry_price)
#                 if highest_price < latest_price:
#                     highest_price = latest_price
#                     self.dynamic_stop_manager.highest_prices[ticker] = highest_price
#                 self.dynamic_stop_manager.entry_prices[ticker] = entry_price
#                     new_stop = self.dynamic_stop_manager.update_stop(ticker, latest_price, df)
#                 self.pt.update_position_stop(ticker, new_stop, highest_price)
#                     should_exit, exit_reason = self.dynamic_stop_manager.check_exit(ticker, latest_price)
#                 if should_exit:
#                     signals.append({
#                         "ticker": ticker, "action": "SELL", "reason": exit_reason,
#                         "confidence": 1.0, "price": latest_price, "quantity": quantity
#                     })
#                     continue
# # Simple TP/Trailing (Simplified from original for brevity, usually handled by DynamicStopManager now)
# # ... (Assuming DynamicStopManager covers most)
#             return signals
#     """
def daily_routine(self, force_run: bool = False) -> None:
#         """日常業務を実行"""
self.log(f"--- 日次ルーティン開始 (Force: {force_run}) ---")
# 1. 安全確認
if not force_run:
            safe, reason = self.is_safe_to_trade()
            if not safe:
                self.log(f"取引停止: {reason}", "WARNING")
                return
# NEW Phase 84/87: 更新前の学習とブリーフィング生成
self.daily_reporter.run_performance_update(self.committee)
# Phase 27: Precog Intelligence (Forecast and Defense)
self.log("🔮 Precog Intelligence: Analyzing upcoming macro events...")
        news_collector = self.market_scanner.news_collector
        recent_news = news_collector.fetch_market_news(limit=10)
        news_text = " ".join([n["title"] for n in recent_news])
            precog_results = self.precog_engine.get_upcoming_events_analysis(news_text)
    defense_action = self.precog_defense.evaluate_emergency_action(precog_results)
            if defense_action["trigger_hedge"]:
                self.log(f"🛡️ PRECOG DEFENSE TRIGGERED: {defense_action['reason']}", "WARNING")
# In a real system, this would reduce leverage or buy puts.
# Here we reflect it in the logs and could potentially reduce trade sizes.
self.trade_executor.emergency_reduction(defense_action["reduce_exposure_pct"])
# Phase 28: Automatic Index Hedging
if defense_action.get("trigger_index_hedge"):
                self.log("📉 Index Hedging initialized to protect portfolio equity.", "WARNING")
                self.trade_executor.execute_index_hedges(defense_action.get("index_symbols", ["^N225"]))
# 1.5. Phase 73: Self-Learning
if self.learning_pipeline.should_run():
            self.log("🤖 週末：自己学習パイプラインを起動中...")
            try:
                self.learning_pipeline.run_optimization(tickers=["7203.T", "9984.T", "^GSPC", "AAPL", "MSFT"])
            except Exception as e:
                self.log(f"自己学習エラー: {e}", "WARNING")
# 2. 市場スキャン & シグナル生成
pt_positions = self.pt.get_positions()
        signals = self.market_scanner.scan_market(pt_positions)
# 2.1 Evaluate existing positions (Stops/TP)
exit_signals = self.evaluate_positions()
        if exit_signals:
            signals.extend(exit_signals)
# 2.5 シグナル実行
if signals:
            self.trade_executor.execute_signals(signals)
# 3. レポート送信
self.daily_reporter.send_daily_report()
# 4. Phase 63: Post-Market Analysis
self.daily_reporter.run_post_market_analysis()
# 5. Phase 76: AI Self-Reflection
self.daily_reporter.run_self_reflection()
# 6. Phase 81: AI Strategy Evolution
self.daily_reporter.run_strategy_evolution()
        self.daily_reporter.run_genetic_evolution(self.committee.agents if self.committee else [])
            self.log("--- 日次ルーティン完了 ---")
